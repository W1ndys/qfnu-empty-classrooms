#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
空教室查询服务层

提供登录、学期信息获取、空教室查询等核心功能
"""

import os
import re
import json
import base64
import pickle
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from loguru import logger

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
    MAX_RETRIES = 3
    MAX_CAPTCHA_RETRIES = 3  # 验证码最大尝试次数

    # Flask 配置
    FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # 缓存配置
    CACHE_DIR = Path(os.environ.get("CACHE_DIR", os.path.dirname(os.path.abspath(__file__)))) / "cache"
    CACHE_FILE = CACHE_DIR / "classroom_cache.json"
    SESSION_FILE = CACHE_DIR / "session_cache.pkl"  # Session 序列化文件
    REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "600"))  # 默认10分钟

    # 高级账号配置
    USE_ADVANCED_API = os.environ.get("USE_ADVANCED_API", "false").lower() == "true"

    @classmethod
    def validate(cls) -> Tuple[bool, str]:
        """验证配置是否完整"""
        if not cls.USERNAME:
            return False, "请设置环境变量 QFNU_USERNAME"
        if not cls.PASSWORD:
            return False, "请设置环境变量 QFNU_PASSWORD"
        return True, "配置验证通过"

    @classmethod
    def ensure_cache_dir(cls) -> None:
        """确保缓存目录存在"""
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)


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
            result = ocr.classification(image_content)
            return str(result) if result else None
        except ImportError:
            return None
        except Exception:
            return None

    def login(
        self, username: str, password: str, max_captcha_retries: int = 3
    ) -> Tuple[bool, requests.Session | str]:
        """登录教务系统
        
        Args:
            username: 用户名
            password: 密码
            max_captcha_retries: 验证码最大尝试次数，默认3次
        """
        session = requests.Session()

        for attempt in range(max_captcha_retries):
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
                    logger.debug(f"验证码获取失败，尝试 {attempt + 1}/{max_captcha_retries}")
                    continue

                if (
                    b"html" in verify_resp.content[:20].lower()
                    or b"<!doctype" in verify_resp.content[:20].lower()
                ):
                    logger.debug(f"验证码内容异常，尝试 {attempt + 1}/{max_captcha_retries}")
                    continue

                # 识别验证码
                captcha_code = self._ocr_captcha(verify_resp.content)
                if not captcha_code:
                    logger.debug(f"验证码识别失败，尝试 {attempt + 1}/{max_captcha_retries}")
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
                    logger.debug(f"验证码错误，尝试 {attempt + 1}/{max_captcha_retries}")
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
                    logger.info("登录成功")
                    return True, session
                else:
                    return False, "登录验证失败"

            except requests.RequestException as e:
                return False, f"网络错误: {str(e)}"
            except Exception as e:
                return False, f"系统错误: {str(e)}"

        return False, f"验证码识别{max_captcha_retries}次均失败，请稍后重试"


class SessionManager:
    """Session 管理器 - 负责 Session 的序列化、反序列化和过期检测"""
    
    # 登录过期的关键词
    LOGIN_EXPIRED_KEYWORDS = ["请输入账号", "请输入密码", "用户登录", "LoginToXk"]
    
    def __init__(self):
        self.base_url = Config.SCHOOL_URL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
    
    @staticmethod
    def save_session(session: requests.Session) -> bool:
        """将 Session 序列化保存到文件
        
        Args:
            session: 要保存的 Session 对象
            
        Returns:
            是否保存成功
        """
        try:
            Config.ensure_cache_dir()
            with open(Config.SESSION_FILE, "wb") as f:
                pickle.dump(session.cookies, f)
            logger.info(f"Session 已保存到: {Config.SESSION_FILE}")
            return True
        except Exception as e:
            logger.error(f"保存 Session 失败: {e}")
            return False
    
    @staticmethod
    def load_session() -> Optional[requests.Session]:
        """从文件加载 Session
        
        Returns:
            加载的 Session 对象，如果失败返回 None
        """
        try:
            if not Config.SESSION_FILE.exists():
                logger.info("Session 缓存文件不存在")
                return None
            
            with open(Config.SESSION_FILE, "rb") as f:
                cookies = pickle.load(f)
            
            session = requests.Session()
            session.cookies = cookies
            logger.info("Session 已从缓存加载")
            return session
        except Exception as e:
            logger.warning(f"加载 Session 失败: {e}")
            return None
    
    @staticmethod
    def delete_session() -> None:
        """删除保存的 Session 文件"""
        try:
            if Config.SESSION_FILE.exists():
                Config.SESSION_FILE.unlink()
                logger.info("Session 缓存文件已删除")
        except Exception as e:
            logger.warning(f"删除 Session 文件失败: {e}")
    
    def is_session_expired(self, session: requests.Session) -> bool:
        """检测 Session 是否过期
        
        通过请求一个需要登录的页面，检查响应内容是否包含登录页面的关键词
        
        Args:
            session: 要检测的 Session 对象
            
        Returns:
            True 表示已过期，False 表示有效
        """
        try:
            # 请求一个需要登录才能访问的页面
            test_url = f"{self.base_url}/jsxsd/framework/xsMain_new.jsp"
            response = session.get(test_url, headers=self.headers, timeout=10)
            
            # 检查响应内容是否包含登录过期的关键词
            for keyword in self.LOGIN_EXPIRED_KEYWORDS:
                if keyword in response.text:
                    logger.warning(f"Session 已过期，检测到关键词: {keyword}")
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"检测 Session 状态失败: {e}")
            # 发生异常时视为过期，触发重新登录
            return True
    
    def check_response_expired(self, response_text: str) -> bool:
        """检查响应内容是否表示登录已过期
        
        Args:
            response_text: 响应内容文本
            
        Returns:
            True 表示已过期，False 表示有效
        """
        for keyword in self.LOGIN_EXPIRED_KEYWORDS:
            if keyword in response_text:
                return True
        return False


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

            # 从 xsMain_new.jsp 获取周次信息
            main_url = f"{self.base_url}/jsxsd/framework/xsMain_new.jsp?t1=1"
            main_response = self.session.get(main_url, headers=self.headers, timeout=10)

            if main_response.status_code == 200:
                week = self._parse_current_week(main_response.text)

            # 从课表查询页面获取学期信息
            kb_url = f"{self.base_url}/jsxsd/kbcx/kbxx_kc"
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
            # 查找 select 标签中 selected 的 option
            # 例如: <option value="2025-2026-1" selected="selected">2025-2026-1</option>
            for select_tag in soup.find_all("select"):
                selected_option = select_tag.find("option", selected=True)
                if selected_option:
                    value = selected_option.get("value")
                    # 验证学期格式: YYYY-YYYY-N
                    if value and isinstance(value, str) and re.match(r"\d{4}-\d{4}-\d", value):
                        return value
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

            # 方法3: 备用方案 - 直接从文本匹配
            week_match = re.search(r"第(\d+)周", html_content)
            if week_match:
                return int(week_match.group(1))

        except Exception:
            pass
        return None


class ClassroomService:
    """空教室查询服务

    新接口说明：
    - URL: /jsxsd/kbcx/kbxx_classroom_ifr
    - 方法: POST
    - 该接口返回的是有课的教室列表，需要反向过滤得到空教室
    - 需要在启动时先获取所有教室列表作为基准
    """

    TIME_SLOTS = {
        "slot_1_2": ("01", "02"),
        "slot_3_4": ("03", "04"),
        "slot_5_6": ("05", "06"),
        "slot_7_8": ("07", "08"),
        "slot_9_11": ("09", "11"),
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
        self.query_url = f"{self.base_url}/jsxsd/kbcx/kbxx_classroom_ifr"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/jsxsd/kbcx/kbxx_classroom_ifr",
        }
        # 所有教室列表缓存（按教学楼关键词分类）
        self._all_classrooms_cache: Dict[str, List[str]] = {}

    def fetch_all_classrooms(
        self, semester: str, building_keyword: str = ""
    ) -> Tuple[bool, List[str] | str]:
        """获取所有教室列表

        通过查询空字符串条件来获取本学期所有有课的教室
        Args:
            semester: 学期，如 "2025-2026-1"
            building_keyword: 教学楼关键词，如 "格物楼"
        Returns:
            (成功标志, 教室列表或错误信息)
        """
        try:
            # 构造查询参数 - 使用较大的周次范围和时间段来获取尽可能多的教室
            form_data = {
                "xnxqh": semester,
                "kbjcmsid": "94786EE0ABE2D3B2E0531E64A8C09931",
                "skyx": "",
                "xqid": "",
                "jzwid": "",
                "skjsid": "",
                "skjs": building_keyword,  # 教学楼关键词搜索
                "zc1": "",
                "zc2": "",  # 查询整个学期
                "skxq1": "",
                "skxq2": "",  # 周一到周日
                "jc1": "",
                "jc2": "",  # 全天
            }

            response = self.session.post(
                self.query_url, data=form_data, headers=self.headers, timeout=30
            )

            if response.status_code != 200:
                return False, f"请求失败，状态码: {response.status_code}"

            if self._is_login_expired(response.text):
                return False, "登录已过期"

            classrooms = self._extract_classrooms_from_table(response.text)
            return True, classrooms

        except requests.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"系统错误: {str(e)}"

    def query_busy_classrooms(
        self,
        semester: str,
        building_keyword: str,
        week: int,
        weekday: int,
        start_section: str,
        end_section: str,
    ) -> Tuple[bool, List[str] | str]:
        """查询有课（忙碌）的教室

        Args:
            semester: 学期，如 "2025-2026-1"
            building_keyword: 教学楼关键词，如 "格物楼B10"
            week: 周次
            weekday: 星期几 (1-7)
            start_section: 起始节次，如 "01"
            end_section: 结束节次，如 "04"
        Returns:
            (成功标志, 有课教室列表或错误信息)
        """
        try:
            form_data = {
                "xnxqh": semester,
                "kbjcmsid": "94786EE0ABE2D3B2E0531E64A8C09931",
                "skyx": "",
                "xqid": "",
                "jzwid": "",
                "skjsid": "",
                "skjs": building_keyword,
                "zc1": str(week),
                "zc2": str(week),
                "skxq1": str(weekday),
                "skxq2": str(weekday),
                "jc1": start_section,
                "jc2": end_section,
            }

            response = self.session.post(
                self.query_url, data=form_data, headers=self.headers, timeout=15
            )

            if response.status_code != 200:
                return False, f"请求失败，状态码: {response.status_code}"

            if self._is_login_expired(response.text):
                return False, "登录已过期"

            classrooms = self._extract_classrooms_from_table(response.text)
            return True, classrooms

        except requests.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"系统错误: {str(e)}"

    def _is_login_expired(self, response_text: str) -> bool:
        """检查登录是否过期"""
        expired_keywords = [
            "请先登录",
            "登录超时",
            "会话已过期",
            "重新登录",
            "login",
            "Login",
        ]
        return any(keyword in response_text for keyword in expired_keywords)

    def _extract_classrooms_from_table(self, html_content: str) -> List[str]:
        """从 HTML 表格中提取教室列表

        教室名在表格的第一列（tbody 中的 tr > td:first-child）
        例如：<td height="28" align="center"><nobr>格物楼B108</nobr></td>
        """
        soup = BeautifulSoup(html_content, "html.parser")
        classroom_list = []

        # 找到课表表格
        table = soup.find("table", id="kbtable")
        if not table:
            return classroom_list

        # 遍历所有数据行（跳过表头）
        rows = table.find_all("tr")
        for row in rows:
            # 获取第一个 td
            first_td = row.find("td")
            if first_td:
                # 获取 nobr 标签内的文本，或直接获取 td 文本
                nobr = first_td.find("nobr")
                if nobr:
                    classroom_name = nobr.get_text(strip=True)
                else:
                    classroom_name = first_td.get_text(strip=True)

                # 过滤掉表头和无效数据
                if (
                    classroom_name
                    and classroom_name != "教室\\节次"
                    and not classroom_name.startswith("教室")
                ):
                    classroom_list.append(classroom_name)

        return classroom_list

    def query_empty_classrooms(
        self,
        semester: str,
        all_classrooms: List[str],
        week: int,
        weekday: int,
        start_section: str,
        end_section: str,
        keyword: str = "",
    ) -> Tuple[bool, List[str] | str]:
        """查询空教室

        空教室 = 所有教室 - 有课教室

        Args:
            semester: 学期
            all_classrooms: 所有教室列表
            week: 周次
            weekday: 星期几
            start_section: 起始节次
            end_section: 结束节次
            keyword: 搜索关键词（教学楼名等）
        Returns:
            (成功标志, 空教室列表或错误信息)
        """
        # 查询有课的教室
        success, busy_classrooms = self.query_busy_classrooms(
            semester, keyword, week, weekday, start_section, end_section
        )

        if not success:
            return False, busy_classrooms

        # 计算空教室 = 总教室 - 有课教室
        busy_set = set(busy_classrooms)

        # 如果有关键词，先过滤总列表
        if keyword:
            filtered_all = [c for c in all_classrooms if keyword in c]
        else:
            filtered_all = all_classrooms

        empty_classrooms = [c for c in filtered_all if c not in busy_set]

        return True, empty_classrooms

    def query_all_slots(
        self,
        semester: str,
        all_classrooms: List[str],
        week: int,
        weekday: int,
        keyword: str = "",
    ) -> Dict[str, List[str]]:
        """查询所有时间段的空教室

        Args:
            semester: 学期
            all_classrooms: 所有教室列表
            week: 周次
            weekday: 星期几
            keyword: 搜索关键词
        Returns:
            各时间段的空教室字典
        """
        result = {slot: [] for slot in self.TIME_SLOTS}

        for slot_key, (start, end) in self.TIME_SLOTS.items():
            success, classrooms = self.query_empty_classrooms(
                semester, all_classrooms, week, weekday, start, end, keyword
            )
            if success and isinstance(classrooms, list):
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


class AdvancedClassroomService:
    """高级账号教室查询服务
    
    使用教务系统的 jsjy_query2 接口直接查询空闲教室，
    该接口可以直接返回指定条件下的空闲教室列表。
    """

    QUERY_URL = f"{Config.SCHOOL_URL}/jsxsd/kbxx/jsjy_query2"

    def __init__(self, session: requests.Session):
        self.session = session
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def query_empty_classrooms(
        self,
        semester: str,
        building_name: str,
        week: int,
        weekday: int,
        start_section: str,
        end_section: str,
    ) -> Tuple[bool, List[str] | str]:
        """查询指定条件下的空闲教室
        
        Args:
            semester: 学期字符串，如 "2025-2026-1"
            building_name: 教学楼名称，如 "综合教学楼"
            week: 周次
            weekday: 星期几 (1-7)
            start_section: 开始节次，如 "01"
            end_section: 结束节次，如 "02"
            
        Returns:
            (成功标志, 空教室列表或错误信息)
            如果检测到登录过期，返回 (False, 响应文本) 供上层检测
        """
        try:
            # 构造请求表单数据
            form_data = {
                "typewhere": "jszq",
                "xnxqh": semester,
                "gnq_mh": "",
                "jsmc_mh": building_name,
                "bjfh": "=",
                "jszt": "8",  # 8代表完全空闲
                "zc": str(week),
                "zc2": str(week),
                "xq": str(weekday),
                "xq2": str(weekday),
                "jc": start_section,
                "jc2": end_section,
                "kbjcmsid": "94786EE0ABE2D3B2E0531E64A8C09931",
            }
            
            response = self.session.post(
                self.QUERY_URL,
                data=form_data,
                headers=self.headers,
                timeout=30,
            )
            
            if response.status_code != 200:
                return False, f"请求失败，状态码: {response.status_code}"
            
            # 检测登录是否过期（返回原始响应文本供上层检测）
            login_expired_keywords = ["请输入账号", "请输入密码", "用户登录", "LoginToXk"]
            for keyword in login_expired_keywords:
                if keyword in response.text:
                    logger.warning(f"检测到登录过期关键词: {keyword}")
                    return False, response.text
            
            # 解析响应HTML，提取教室列表
            classrooms = self._extract_classrooms(response.text)
            return True, classrooms
            
        except requests.RequestException as e:
            return False, f"网络请求错误: {str(e)}"
        except Exception as e:
            return False, f"查询失败: {str(e)}"

    def _extract_classrooms(self, html_content: str) -> List[str]:
        """解析HTML，提取表格第一列的教室名称，并去除括号及其内容
        
        Args:
            html_content: 包含HTML内容的字符串
            
        Returns:
            处理后的教室名称列表
        """
        soup = BeautifulSoup(html_content, "html.parser")
        classroom_list = []

        # 寻找包含教室信息的元素
        # 在HTML中，教室名称所在的单元格都包含一个 name="jsids" 的 input 复选框
        checkboxes = soup.find_all("input", {"name": "jsids"})

        for box in checkboxes:
            # 获取 input 标签的父级 td 标签
            td = box.parent
            if td:
                # 获取 td 中的纯文本
                full_text = td.get_text(strip=True)
                
                # 使用正则表达式去除括号及其中间的内容
                clean_name = re.sub(r"\(.*?\)|（.*?）", "", full_text)
                clean_name = clean_name.strip()
                
                if clean_name:
                    classroom_list.append(clean_name)

        return classroom_list


class EmptyClassroomQueryService:
    """空教室查询主服务 - 整合所有服务

    功能说明：
    1. 支持从缓存恢复数据，快速启动
    2. 定时刷新教室列表（默认每10分钟）
    3. 前端传入参数：教学楼名称、开始节次、结束节次、日期偏移
    4. 后端计算目标日期的周次和星期几
    5. 查询指定条件的有课教室，计算空教室
    """

    def __init__(self):
        self.session: Optional[requests.Session] = None
        self.semester: Optional[str] = None
        self.current_week: Optional[int] = None
        self.all_classrooms: List[str] = []  # 所有教室列表缓存
        self.last_refresh: Optional[datetime] = None  # 上次刷新时间
        # 查询结果缓存: {cache_key: (result, timestamp)}
        self._query_cache: Dict[str, Tuple[Dict, datetime]] = {}

    def _load_cache(self) -> bool:
        """从缓存文件加载数据"""
        try:
            if not Config.CACHE_FILE.exists():
                logger.info("缓存文件不存在")
                return False

            with open(Config.CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # 验证缓存数据
            if not isinstance(cache_data, dict):
                logger.warning("缓存数据格式错误")
                return False

            self.semester = cache_data.get("semester")
            self.current_week = cache_data.get("current_week")
            self.all_classrooms = cache_data.get("all_classrooms", [])
            last_refresh_str = cache_data.get("last_refresh")

            if last_refresh_str:
                self.last_refresh = datetime.fromisoformat(last_refresh_str)

            if self.semester and self.current_week and self.all_classrooms:
                logger.info(
                    f"从缓存恢复数据: 学期={self.semester}, 周次={self.current_week}, "
                    f"教室数量={len(self.all_classrooms)}, 上次刷新={last_refresh_str}"
                )
                return True
            else:
                logger.warning("缓存数据不完整")
                return False

        except json.JSONDecodeError as e:
            logger.warning(f"缓存文件JSON解析失败: {e}")
            return False
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return False

    def _save_cache(self) -> bool:
        """保存数据到缓存文件"""
        try:
            Config.ensure_cache_dir()

            cache_data = {
                "semester": self.semester,
                "current_week": self.current_week,
                "all_classrooms": self.all_classrooms,
                "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
                "saved_at": datetime.now().isoformat(),
            }

            with open(Config.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"缓存已保存: {Config.CACHE_FILE}")
            return True

        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False

    def _needs_refresh(self) -> bool:
        """检查是否需要刷新数据"""
        if not self.last_refresh:
            return True

        elapsed = (datetime.now() - self.last_refresh).total_seconds()
        return elapsed >= Config.REFRESH_INTERVAL

    def initialize(self, force: bool = False) -> Tuple[bool, str]:
        """初始化服务（登录 + 获取学期信息 + 获取所有教室列表）

        Args:
            force: 是否强制刷新，忽略缓存
        """
        # 尝试从缓存恢复（非强制刷新时）
        if not force and self._load_cache():
            # 如果缓存有效且不需要刷新，直接使用缓存
            if not self._needs_refresh():
                logger.info("使用缓存数据，无需刷新")
                return True, "从缓存恢复成功"
            else:
                logger.info("缓存已过期，需要刷新")

        # 验证配置
        valid, msg = Config.validate()
        if not valid:
            return False, msg

        # 登录
        auth_service = AuthService()
        login_success, login_result = auth_service.login(Config.USERNAME, Config.PASSWORD)
        if not login_success:
            # 如果登录失败但有缓存，使用缓存数据
            if self.all_classrooms:
                logger.warning(f"登录失败但有缓存数据，继续使用缓存: {login_result}")
                return True, "登录失败，使用缓存数据"
            return False, f"登录失败: {login_result}"

        # login_result 是 Session 类型（登录成功时）
        if not isinstance(login_result, requests.Session):
            return False, "登录返回类型错误"
        self.session = login_result

        # 获取学期信息
        semester_service = SemesterService(self.session)
        sem_success, sem_result = semester_service.fetch_semester_and_week()
        if not sem_success:
            if self.semester and self.current_week:
                logger.warning(f"获取学期信息失败但有缓存，继续使用: {sem_result}")
            else:
                return False, f"获取学期信息失败: {sem_result}"
        else:
            # sem_result 是 Dict 类型（成功时）
            if not isinstance(sem_result, dict):
                return False, "学期信息返回类型错误"
            semester_value = sem_result.get("semester")
            week_value = sem_result.get("week")
            if not isinstance(semester_value, str) or not isinstance(week_value, int):
                return False, "学期信息格式错误"
            self.semester = semester_value
            self.current_week = week_value

        # 获取所有教室列表（查询整学期有课的教室作为基准）
        if self.semester:
            logger.info("正在获取所有教室列表...")
            classroom_service = ClassroomService(self.session)

            # 不传教学楼参数，获取所有教室
            room_success, rooms = classroom_service.fetch_all_classrooms(self.semester, "")
            if room_success and isinstance(rooms, list):
                self.all_classrooms = rooms
                self.last_refresh = datetime.now()
                logger.info(f"共获取到 {len(self.all_classrooms)} 个教室")

                # 保存到缓存
                self._save_cache()
            else:
                if self.all_classrooms:
                    logger.warning(f"获取教室列表失败但有缓存，继续使用: {rooms}")
                else:
                    logger.warning(f"获取教室列表失败: {rooms}")
                    self.all_classrooms = []

        return True, "初始化成功"

    def refresh(self) -> Tuple[bool, str]:
        """强制刷新数据"""
        logger.info("开始强制刷新数据...")
        return self.initialize(force=True)

    def _get_query_cache_key(
        self, building_keyword: str, start_section: str, end_section: str,
        target_week: int, target_weekday: int
    ) -> str:
        """生成查询缓存的键"""
        return f"{self.semester}:{target_week}:{target_weekday}:{start_section}:{end_section}:{building_keyword}"

    def _get_cached_query(self, cache_key: str) -> Optional[Dict]:
        """获取缓存的查询结果"""
        if cache_key not in self._query_cache:
            return None

        result, timestamp = self._query_cache[cache_key]
        elapsed = (datetime.now() - timestamp).total_seconds()

        if elapsed >= Config.REFRESH_INTERVAL:
            # 缓存已过期，删除
            del self._query_cache[cache_key]
            return None

        return result

    def _set_query_cache(self, cache_key: str, result: Dict) -> None:
        """设置查询结果缓存"""
        self._query_cache[cache_key] = (result, datetime.now())

        # 清理过期缓存（避免内存无限增长）
        self._cleanup_query_cache()

    def _cleanup_query_cache(self) -> None:
        """清理过期的查询缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._query_cache.items()
            if (now - timestamp).total_seconds() >= Config.REFRESH_INTERVAL
        ]
        for key in expired_keys:
            del self._query_cache[key]

    def ensure_initialized(self) -> Tuple[bool, str]:
        """确保服务已初始化"""
        if not self.session or not self.semester:
            return self.initialize()
        return True, "已初始化"

    def query(
        self,
        building_keyword: str,
        start_section: str,
        end_section: str,
        day_offset: int = 0,
    ) -> Tuple[bool, Dict | str]:
        """查询空教室

        Args:
            building_keyword: 教学楼关键词，如 "格物楼B10"
            start_section: 开始节次，如 "01", "03", "05" 等
            end_section: 结束节次，如 "02", "04", "06" 等
            day_offset: 日期偏移，0=今天，1=明天，-1=昨天
        Returns:
            (成功标志, 结果数据或错误信息)
        """
        # 确保已初始化
        success, msg = self.ensure_initialized()
        if not success:
            return False, msg

        # 此时 current_week 和 semester 必定已初始化
        if self.current_week is None or self.semester is None or self.session is None:
            return False, "服务未正确初始化"

        # 计算目标日期的周次和星期
        target_date = datetime.now() + timedelta(days=day_offset)
        target_week, target_weekday = DateService.calculate_week_and_weekday(
            target_date, self.current_week
        )

        # 生成缓存键并尝试从缓存获取结果
        cache_key = self._get_query_cache_key(
            building_keyword, start_section, end_section, target_week, target_weekday
        )
        cached_result = self._get_cached_query(cache_key)
        if cached_result is not None:
            logger.debug(f"命中查询缓存: {cache_key}")
            # 更新查询时间为当前时间
            cached_result["query_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cached_result["from_cache"] = True
            return True, cached_result

        # 过滤出匹配关键词的教室作为基准
        if building_keyword:
            base_classrooms = [c for c in self.all_classrooms if building_keyword in c]
        else:
            base_classrooms = self.all_classrooms

        # 查询空教室
        classroom_service = ClassroomService(self.session)
        query_success, query_result = classroom_service.query_empty_classrooms(
            self.semester,
            base_classrooms,
            target_week,
            target_weekday,
            start_section,
            end_section,
            building_keyword,
        )

        if not query_success:
            return False, query_result if isinstance(query_result, str) else "查询失败"

        # 此时 query_result 是 List[str]
        if not isinstance(query_result, list):
            return False, "查询结果类型错误"

        weekday_name = DateService.WEEKDAY_NAMES[target_weekday - 1]

        result = {
            "date": target_date.strftime("%Y-%m-%d"),
            "weekday": target_weekday,
            "weekday_name": weekday_name,
            "semester": self.semester,
            "week": target_week,
            "start_section": start_section,
            "end_section": end_section,
            "building_keyword": building_keyword,
            "empty_classrooms": sorted(query_result),
            "total_count": len(query_result),
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_cache": False,
        }

        # 缓存查询结果
        self._set_query_cache(cache_key, result)
        logger.debug(f"缓存查询结果: {cache_key}")

        return True, result

    def get_info(self) -> Dict:
        """获取当前服务状态信息"""
        return {
            "initialized": self.session is not None or len(self.all_classrooms) > 0,
            "semester": self.semester,
            "current_week": self.current_week,
            "total_classrooms": len(self.all_classrooms),
            "last_refresh": self.last_refresh.strftime("%Y-%m-%d %H:%M:%S") if self.last_refresh else None,
            "refresh_interval": Config.REFRESH_INTERVAL,
            "query_cache_count": len(self._query_cache),
        }


class AdvancedEmptyClassroomQueryService:
    """高级账号空教室查询主服务
    
    使用高级账号的 jsjy_query2 接口直接查询空闲教室，
    相比普通模式，该模式直接返回空闲教室，无需计算差集。
    
    功能说明：
    1. 支持从缓存恢复数据，快速启动
    2. 定时刷新学期信息
    3. 前端传入参数：教学楼名称、开始节次、结束节次、日期偏移
    4. 后端计算目标日期的周次和星期几
    5. 直接查询指定条件的空闲教室
    """

    def __init__(self):
        self.session: Optional[requests.Session] = None
        self.semester: Optional[str] = None
        self.current_week: Optional[int] = None
        self.last_refresh: Optional[datetime] = None
        # 查询结果缓存: {cache_key: (result, timestamp)}
        self._query_cache: Dict[str, Tuple[Dict, datetime]] = {}
        # Session 管理器
        self._session_manager = SessionManager()

    def _load_cache(self) -> bool:
        """从缓存文件加载学期信息"""
        try:
            if not Config.CACHE_FILE.exists():
                logger.info("缓存文件不存在")
                return False

            with open(Config.CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            if not isinstance(cache_data, dict):
                logger.warning("缓存数据格式错误")
                return False

            self.semester = cache_data.get("semester")
            self.current_week = cache_data.get("current_week")
            last_refresh_str = cache_data.get("last_refresh")

            if last_refresh_str:
                self.last_refresh = datetime.fromisoformat(last_refresh_str)

            if self.semester and self.current_week:
                logger.info(
                    f"从缓存恢复学期信息: 学期={self.semester}, 周次={self.current_week}"
                )
                return True
            else:
                logger.warning("缓存数据不完整")
                return False

        except json.JSONDecodeError as e:
            logger.warning(f"缓存文件JSON解析失败: {e}")
            return False
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
            return False

    def _save_cache(self) -> bool:
        """保存学期信息到缓存文件"""
        try:
            Config.ensure_cache_dir()

            cache_data = {
                "semester": self.semester,
                "current_week": self.current_week,
                "all_classrooms": [],  # 高级模式不需要缓存教室列表
                "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
                "saved_at": datetime.now().isoformat(),
            }

            with open(Config.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"缓存已保存: {Config.CACHE_FILE}")
            return True

        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False

    def _needs_refresh(self) -> bool:
        """检查是否需要刷新数据"""
        if not self.last_refresh:
            return True
        elapsed = (datetime.now() - self.last_refresh).total_seconds()
        return elapsed >= Config.REFRESH_INTERVAL

    def initialize(self, force: bool = False) -> Tuple[bool, str]:
        """初始化服务（登录 + 获取学期信息）
        
        Args:
            force: 是否强制刷新，忽略缓存
        """
        # 尝试从缓存恢复学期信息（非强制刷新时）
        cache_loaded = False
        if not force:
            cache_loaded = self._load_cache()
        
        # 验证配置
        valid, msg = Config.validate()
        if not valid:
            return False, msg

        # 尝试从缓存加载 Session（非强制刷新时）
        session_loaded = False
        if not force:
            cached_session = SessionManager.load_session()
            if cached_session:
                # 验证缓存的 Session 是否有效
                if not self._session_manager.is_session_expired(cached_session):
                    self.session = cached_session
                    session_loaded = True
                    logger.info("使用缓存的 Session")
                else:
                    logger.info("缓存的 Session 已过期，需要重新登录")
                    SessionManager.delete_session()

        # 如果没有有效的缓存 Session，则登录
        if not session_loaded:
            auth_service = AuthService()
            login_success, login_result = auth_service.login(
                Config.USERNAME, Config.PASSWORD, 
                max_captcha_retries=Config.MAX_CAPTCHA_RETRIES
            )
            if not login_success:
                return False, f"登录失败: {login_result}"

            if not isinstance(login_result, requests.Session):
                return False, "登录返回类型错误"
            self.session = login_result
            
            # 保存 Session 到缓存
            SessionManager.save_session(self.session)

        # 如果缓存有效且不需要刷新，使用缓存的学期信息
        if cache_loaded and not self._needs_refresh():
            logger.info("使用缓存的学期信息")
            return True, "初始化成功（使用缓存）"

        # 获取学期信息
        semester_service = SemesterService(self.session)
        sem_success, sem_result = semester_service.fetch_semester_and_week()
        if not sem_success:
            if self.semester and self.current_week:
                logger.warning(f"获取学期信息失败但有缓存，继续使用: {sem_result}")
            else:
                return False, f"获取学期信息失败: {sem_result}"
        else:
            if not isinstance(sem_result, dict):
                return False, "学期信息返回类型错误"
            semester_value = sem_result.get("semester")
            week_value = sem_result.get("week")
            if not isinstance(semester_value, str) or not isinstance(week_value, int):
                return False, "学期信息格式错误"
            self.semester = semester_value
            self.current_week = week_value

        self.last_refresh = datetime.now()
        self._save_cache()

        return True, "初始化成功"

    def refresh(self) -> Tuple[bool, str]:
        """强制刷新数据"""
        logger.info("开始强制刷新数据...")
        return self.initialize(force=True)

    def _get_query_cache_key(
        self, building_keyword: str, start_section: str, end_section: str,
        target_week: int, target_weekday: int
    ) -> str:
        """生成查询缓存的键"""
        return f"adv:{self.semester}:{target_week}:{target_weekday}:{start_section}:{end_section}:{building_keyword}"

    def _get_cached_query(self, cache_key: str) -> Optional[Dict]:
        """获取缓存的查询结果"""
        if cache_key not in self._query_cache:
            return None

        result, timestamp = self._query_cache[cache_key]
        elapsed = (datetime.now() - timestamp).total_seconds()

        if elapsed >= Config.REFRESH_INTERVAL:
            del self._query_cache[cache_key]
            return None

        return result

    def _set_query_cache(self, cache_key: str, result: Dict) -> None:
        """设置查询结果缓存"""
        self._query_cache[cache_key] = (result, datetime.now())
        self._cleanup_query_cache()

    def _cleanup_query_cache(self) -> None:
        """清理过期的查询缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._query_cache.items()
            if (now - timestamp).total_seconds() >= Config.REFRESH_INTERVAL
        ]
        for key in expired_keys:
            del self._query_cache[key]

    def ensure_initialized(self) -> Tuple[bool, str]:
        """确保服务已初始化"""
        if not self.session or not self.semester:
            return self.initialize()
        return True, "已初始化"


    def _relogin(self) -> bool:
        """重新登录并更新 Session
        
        Returns:
            是否重新登录成功
        """
        logger.info("正在重新登录...")
        auth_service = AuthService()
        login_success, login_result = auth_service.login(
            Config.USERNAME, Config.PASSWORD,
            max_captcha_retries=Config.MAX_CAPTCHA_RETRIES
        )
        
        if login_success and isinstance(login_result, requests.Session):
            self.session = login_result
            SessionManager.save_session(self.session)
            logger.info("重新登录成功")
            return True
        else:
            logger.error(f"重新登录失败: {login_result}")
            return False

    def _query_with_retry(
        self,
        building_keyword: str,
        target_week: int,
        target_weekday: int,
        start_section: str,
        end_section: str,
        max_retries: int = 2,
    ) -> Optional[List[str]]:
        """带登录过期检测和自动重试的查询
        
        Args:
            building_keyword: 教学楼名称
            target_week: 周次
            target_weekday: 星期几
            start_section: 开始节次
            end_section: 结束节次
            max_retries: 最大重试次数
            
        Returns:
            空教室列表，失败返回 None
        """
        for attempt in range(max_retries):
            if self.session is None or self.semester is None:
                logger.error("Session 或学期信息为空")
                return None
            
            advanced_service = AdvancedClassroomService(self.session)
            query_success, query_result = advanced_service.query_empty_classrooms(
                self.semester,
                building_keyword,
                target_week,
                target_weekday,
                start_section,
                end_section,
            )
            
            if query_success and isinstance(query_result, list):
                return query_result
            
            # 检查是否是登录过期导致的失败
            if isinstance(query_result, str) and self._session_manager.check_response_expired(query_result):
                logger.warning(f"检测到登录过期，尝试重新登录 (尝试 {attempt + 1}/{max_retries})")
                SessionManager.delete_session()
                if self._relogin():
                    continue  # 重新登录成功，重试查询
                else:
                    return None  # 重新登录失败
            
            # 其他错误，直接返回
            logger.error(f"查询失败: {query_result}")
            return None
        
        return None

    def query(
        self,
        building_keyword: str,
        start_section: str,
        end_section: str,
        day_offset: int = 0,
    ) -> Tuple[bool, Dict | str]:
        """查询空教室
        
        Args:
            building_keyword: 教学楼名称，如 "综合教学楼"
            start_section: 开始节次，如 "01", "03", "05" 等
            end_section: 结束节次，如 "02", "04", "06" 等
            day_offset: 日期偏移，0=今天，1=明天，-1=昨天
            
        Returns:
            (成功标志, 结果数据或错误信息)
        """
        # 确保已初始化
        success, msg = self.ensure_initialized()
        if not success:
            return False, msg

        if self.current_week is None or self.semester is None or self.session is None:
            return False, "服务未正确初始化"

        # 计算目标日期的周次和星期
        target_date = datetime.now() + timedelta(days=day_offset)
        target_week, target_weekday = DateService.calculate_week_and_weekday(
            target_date, self.current_week
        )

        # 生成缓存键并尝试从缓存获取结果
        cache_key = self._get_query_cache_key(
            building_keyword, start_section, end_section, target_week, target_weekday
        )
        cached_result = self._get_cached_query(cache_key)
        if cached_result is not None:
            logger.debug(f"命中查询缓存: {cache_key}")
            cached_result["query_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cached_result["from_cache"] = True
            return True, cached_result

        # 使用高级接口查询空闲教室（带登录过期检测和自动重试）
        query_result = self._query_with_retry(
            building_keyword, target_week, target_weekday, start_section, end_section
        )
        
        if query_result is None:
            return False, "查询失败，请稍后重试"

        weekday_name = DateService.WEEKDAY_NAMES[target_weekday - 1]

        result = {
            "date": target_date.strftime("%Y-%m-%d"),
            "weekday": target_weekday,
            "weekday_name": weekday_name,
            "semester": self.semester,
            "week": target_week,
            "start_section": start_section,
            "end_section": end_section,
            "building_keyword": building_keyword,
            "empty_classrooms": sorted(query_result),
            "total_count": len(query_result),
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_cache": False,
        }

        # 缓存查询结果
        self._set_query_cache(cache_key, result)
        logger.debug(f"缓存查询结果: {cache_key}")

        return True, result

    def get_info(self) -> Dict:
        """获取当前服务状态信息"""
        return {
            "initialized": self.session is not None,
            "semester": self.semester,
            "current_week": self.current_week,
            "total_classrooms": 0,  # 高级模式不缓存教室列表
            "last_refresh": self.last_refresh.strftime("%Y-%m-%d %H:%M:%S") if self.last_refresh else None,
            "refresh_interval": Config.REFRESH_INTERVAL,
            "query_cache_count": len(self._query_cache),
            "mode": "advanced",
        }
