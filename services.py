#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
空教室查询服务层

提供登录、学期信息获取、空教室查询等核心功能
"""

import os
import re
import base64
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional

import requests
from bs4 import BeautifulSoup

# 加载 .env 文件
try:
    from dotenv import load_dotenv

    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")

    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass


class Config:
    """配置管理类"""

    SCHOOL_URL = "http://zhjw.qfnu.edu.cn"
    USERNAME = os.environ.get("QFNU_USERNAME", "")
    PASSWORD = os.environ.get("QFNU_PASSWORD", "")
    BUILDINGS = os.environ.get("QFNU_BUILDINGS", "综合教学楼")
    MAX_RETRIES = 3

    # Flask 配置
    FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    @classmethod
    def get_buildings(cls) -> List[str]:
        """获取待查询的教学楼列表"""
        return [b.strip() for b in cls.BUILDINGS.split(",") if b.strip()]

    @classmethod
    def validate(cls) -> Tuple[bool, str]:
        """验证配置是否完整"""
        if not cls.USERNAME:
            return False, "请设置环境变量 QFNU_USERNAME"
        if not cls.PASSWORD:
            return False, "请设置环境变量 QFNU_PASSWORD"
        if not cls.get_buildings():
            return False, "请设置环境变量 QFNU_BUILDINGS"
        return True, "配置验证通过"


class AuthService:
    """登录认证服务"""

    def __init__(self):
        self.base_url = Config.SCHOOL_URL
        self.login_url = f"{self.base_url}/jsxsd/xk/LoginToXkLdap"
        self.verify_code_url = f"{self.base_url}/jsxsd/verifycode.servlet"
        self.user_info_url = f"{self.base_url}/jsxsd/framework/jsMain.jsp"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        }

    def _get_encoded_payload(self, username: str, password: str) -> str:
        """生成加密的 encoded 字段"""
        try:
            account_b64 = base64.b64encode(username.encode()).decode()
            password_b64 = base64.b64encode(password.encode()).decode()
            return f"{account_b64}%%%{password_b64}"
        except Exception:
            return ""

    def _ocr_captcha(self, image_content: bytes) -> Optional[str]:
        """识别验证码"""
        try:
            import ddddocr
            ocr = ddddocr.DdddOcr(show_ad=False)
            return ocr.classification(image_content)
        except ImportError:
            return None
        except Exception:
            return None

    def login(self, username: str, password: str) -> Tuple[bool, requests.Session | str]:
        """登录教务系统"""
        session = requests.Session()

        for attempt in range(Config.MAX_RETRIES):
            try:
                # 1. 获取初始 Cookie
                try:
                    session.get(
                        f"{self.base_url}/jsxsd/xk/LoginToXk",
                        headers=self.headers,
                        timeout=10,
                    )
                except Exception:
                    pass

                # 2. 获取验证码
                verify_resp = session.get(
                    self.verify_code_url, headers=self.headers, timeout=10
                )
                if verify_resp.status_code != 200:
                    return False, "无法连接到教务系统"

                if not verify_resp.content:
                    continue

                if (
                    b"html" in verify_resp.content[:20].lower()
                    or b"<!doctype" in verify_resp.content[:20].lower()
                ):
                    continue

                # 识别验证码
                captcha_code = self._ocr_captcha(verify_resp.content)
                if not captcha_code:
                    continue

                # 3. 构造登录参数
                encoded = self._get_encoded_payload(username, password)
                data = {
                    "userAccount": username,
                    "userPassword": password,
                    "RANDOMCODE": captcha_code,
                    "encoded": encoded,
                }

                # 4. 发送登录请求
                login_resp = session.post(
                    self.login_url, data=data, headers=self.headers, timeout=10
                )
                login_text = login_resp.text

                # 5. 判断登录结果
                if "验证码错误" in login_text:
                    continue
                elif "密码错误" in login_text or "账号或密码错误" in login_text:
                    return False, "账号或密码错误"
                elif "系统繁忙" in login_text:
                    return False, "教务系统繁忙，请稍后再试"

                # 6. 二次验证
                info_resp = session.get(
                    self.user_info_url, headers=self.headers, timeout=10
                )

                if username in info_resp.text or "退出" in info_resp.text:
                    return True, session
                else:
                    return False, "登录验证失败"

            except requests.RequestException as e:
                return False, f"网络错误: {str(e)}"
            except Exception as e:
                return False, f"系统错误: {str(e)}"

        return False, "验证码识别多次失败，请稍后重试"


class SemesterService:
    """学期信息服务"""

    def __init__(self, session: requests.Session):
        self.session = session
        self.base_url = Config.SCHOOL_URL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def fetch_semester_and_week(self) -> Tuple[bool, Dict | str]:
        """获取当前学期和周次"""
        try:
            semester = None
            week = None

            # 从 jsMain_new.jsp 获取周次信息
            main_url = f"{self.base_url}/jsxsd/framework/jsMain_new.jsp?t1=1"
            main_response = self.session.get(main_url, headers=self.headers, timeout=10)

            if main_response.status_code == 200:
                week = self._parse_current_week(main_response.text)

            # 从课表页面获取学期信息
            kb_url = f"{self.base_url}/jsxsd/jskb/jskb_list.do"
            kb_response = self.session.get(kb_url, headers=self.headers, timeout=10)

            if kb_response.status_code == 200:
                semester = self._parse_selected_semester(kb_response.text)
                if not week:
                    week = self._parse_current_week(kb_response.text)

            # 尝试学生课表
            if not semester:
                kb_url = f"{self.base_url}/jsxsd/xskb/xskb_list.do"
                kb_response = self.session.get(kb_url, headers=self.headers, timeout=10)

                if kb_response.status_code == 200:
                    semester = self._parse_selected_semester(kb_response.text)
                    if not week:
                        week = self._parse_current_week(kb_response.text)

            if semester and week:
                return True, {"semester": semester, "week": week}
            elif semester:
                return True, {"semester": semester, "week": 1}
            else:
                return False, "无法解析学期和周次信息"

        except Exception as e:
            return False, f"获取学期信息失败: {str(e)}"

    def _parse_selected_semester(self, html_content: str) -> Optional[str]:
        """解析当前选中的学期"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            select_tag = soup.find("select", id="xnxq01id")
            if select_tag:
                selected_option = select_tag.find("option", selected=True)
                if selected_option:
                    return selected_option.get("value")
        except Exception:
            pass
        return None

    def _parse_current_week(self, html_content: str) -> Optional[int]:
        """解析当前周次"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # 方法1: 从 li_showWeek 获取
            week_div = soup.find("div", id="li_showWeek")
            if week_div:
                week_span = week_div.find("span", class_="main_text")
                if week_span:
                    week_text = week_span.get_text(strip=True)
                    week_match = re.search(r"第(\d+)周", week_text)
                    if week_match:
                        return int(week_match.group(1))

            # 方法2: 从周次选择器获取
            week_select = soup.find("select", id="zc")
            if week_select:
                selected_option = week_select.find("option", selected=True)
                if selected_option:
                    week_value = selected_option.get("value")
                    if week_value and isinstance(week_value, str):
                        return int(week_value)

            # 方法3: 备用方案
            week_match = re.search(r"第(\d+)周", html_content)
            if week_match:
                return int(week_match.group(1))

        except Exception:
            pass
        return None


class ClassroomService:
    """空教室查询服务"""

    TIME_SLOTS = {
        "slot_1_2": (1, 2),
        "slot_3_4": (3, 4),
        "slot_5_6": (5, 6),
        "slot_7_8": (7, 8),
        "slot_9_11": (9, 11),
    }

    TIME_SLOT_NAMES = {
        "slot_1_2": "第1-2节",
        "slot_3_4": "第3-4节",
        "slot_5_6": "第5-6节",
        "slot_7_8": "第7-8节",
        "slot_9_11": "第9-11节",
    }

    def __init__(self, session: requests.Session):
        self.session = session
        self.base_url = Config.SCHOOL_URL
        self.query_url = f"{self.base_url}/jsxsd/kbxx/jsjy_query2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/jsxsd/kbxx/jsjy_query",
        }

    def query(
        self,
        semester: str,
        building_name: str,
        week: int,
        weekday: int,
        start_section: int,
        end_section: int,
    ) -> Tuple[bool, List[str] | str]:
        """查询空闲教室"""
        try:
            form_data = {
                "typewhere": "jszq",
                "xnxqh": semester,
                "gnq_mh": "",
                "jsmc_mh": building_name,
                "bjfh": "=",
                "jszt": "8",
                "zc": str(week),
                "zc2": str(week),
                "xq": str(weekday),
                "xq2": str(weekday),
                "jc": str(start_section),
                "jc2": str(end_section),
                "kbjcmsid": "94786EE0ABE2D3B2E0531E64A8C09931",
            }

            response = self.session.post(
                self.query_url, data=form_data, headers=self.headers, timeout=15
            )

            if response.status_code != 200:
                return False, f"请求失败，状态码: {response.status_code}"

            if self._is_login_expired(response.text):
                return False, "登录已过期"

            classrooms = self._extract_classrooms(response.text)
            return True, classrooms

        except requests.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"系统错误: {str(e)}"

    def _is_login_expired(self, response_text: str) -> bool:
        """检查登录是否过期"""
        expired_keywords = ["请先登录", "登录超时", "会话已过期", "重新登录", "login", "Login"]
        return any(keyword in response_text for keyword in expired_keywords)

    def _extract_classrooms(self, html_content: str) -> List[str]:
        """从 HTML 中提取教室列表"""
        soup = BeautifulSoup(html_content, "html.parser")
        classroom_list = []

        checkboxes = soup.find_all("input", {"name": "jsids"})
        for box in checkboxes:
            td = box.parent
            if td:
                full_text = td.get_text(strip=True)
                clean_name = re.sub(r"\(.*?\)|（.*?）", "", full_text)
                clean_name = clean_name.strip()
                if clean_name:
                    classroom_list.append(clean_name)

        return classroom_list

    def query_all_slots(
        self, semester: str, week: int, weekday: int
    ) -> Dict[str, List[str]]:
        """查询所有时间段的空教室"""
        result = {slot: [] for slot in self.TIME_SLOTS}

        for slot_key, (start, end) in self.TIME_SLOTS.items():
            success, classrooms = self.query(semester, "", week, weekday, start, end)
            if success:
                result[slot_key] = classrooms

        return result

    def filter_by_buildings(
        self, all_classrooms: Dict[str, List[str]], buildings: List[str]
    ) -> Dict[str, Dict[str, List[str]]]:
        """按教学楼过滤教室"""
        result = {}

        for building in buildings:
            result[building] = {}
            for slot_key in self.TIME_SLOTS:
                result[building][slot_key] = [
                    c for c in all_classrooms[slot_key] if c.startswith(building)
                ]

        return result


class DateService:
    """日期计算服务"""

    WEEKDAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]

    @staticmethod
    def get_tomorrow() -> datetime:
        """获取明天的日期"""
        return datetime.now() + timedelta(days=1)

    @staticmethod
    def calculate_week_and_weekday(
        target_date: datetime, current_week: int
    ) -> Tuple[int, int]:
        """计算目标日期的周次和星期几"""
        today = datetime.now()
        today_weekday = today.isoweekday()
        delta_days = (target_date.date() - today.date()).days
        target_weekday = ((today_weekday - 1 + delta_days) % 7) + 1

        weeks_diff = 0
        if delta_days > 0:
            days_to_sunday = 7 - today_weekday
            if delta_days > days_to_sunday:
                weeks_diff = 1 + (delta_days - days_to_sunday - 1) // 7

        target_week = current_week + weeks_diff
        return target_week, target_weekday


class EmptyClassroomQueryService:
    """空教室查询主服务 - 整合所有服务"""

    def __init__(self):
        self.session: Optional[requests.Session] = None
        self.semester: Optional[str] = None
        self.current_week: Optional[int] = None

    def initialize(self) -> Tuple[bool, str]:
        """初始化服务（登录 + 获取学期信息）"""
        # 验证配置
        valid, msg = Config.validate()
        if not valid:
            return False, msg

        # 登录
        auth_service = AuthService()
        success, result = auth_service.login(Config.USERNAME, Config.PASSWORD)
        if not success:
            return False, f"登录失败: {result}"
        self.session = result

        # 获取学期信息
        semester_service = SemesterService(self.session)
        success, result = semester_service.fetch_semester_and_week()
        if not success:
            return False, f"获取学期信息失败: {result}"

        self.semester = result["semester"]
        self.current_week = result["week"]

        return True, "初始化成功"

    def query_tomorrow(self) -> Tuple[bool, Dict | str]:
        """查询明天的空教室"""
        if not self.session or not self.semester:
            success, msg = self.initialize()
            if not success:
                return False, msg

        # 计算明天的周次和星期
        tomorrow = DateService.get_tomorrow()
        target_week, target_weekday = DateService.calculate_week_and_weekday(
            tomorrow, self.current_week
        )

        # 查询空教室
        classroom_service = ClassroomService(self.session)
        all_classrooms = classroom_service.query_all_slots(
            self.semester, target_week, target_weekday
        )

        # 按教学楼过滤
        buildings = Config.get_buildings()
        filtered_data = classroom_service.filter_by_buildings(all_classrooms, buildings)

        # 构建返回数据
        weekday_name = DateService.WEEKDAY_NAMES[target_weekday - 1]

        return True, {
            "date": tomorrow.strftime("%Y-%m-%d"),
            "weekday": target_weekday,
            "weekday_name": weekday_name,
            "semester": self.semester,
            "week": target_week,
            "buildings": [
                {
                    "name": building,
                    "slot_1_2": sorted(data.get("slot_1_2", [])),
                    "slot_3_4": sorted(data.get("slot_3_4", [])),
                    "slot_5_6": sorted(data.get("slot_5_6", [])),
                    "slot_7_8": sorted(data.get("slot_7_8", [])),
                    "slot_9_11": sorted(data.get("slot_9_11", [])),
                }
                for building, data in filtered_data.items()
            ],
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
