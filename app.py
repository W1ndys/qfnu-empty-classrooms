#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
空教室查询 Flask Web 服务

功能：
1. 自动检测设备类型，路由到不同的前端页面
2. PC 端使用 Element Plus 组件库
3. 移动端使用 Vant 组件库
4. 提供 API 接口查询空教室数据
5. 启动时从缓存恢复数据，定时刷新教室列表
"""

from logger import setup_logger
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from user_agents import parse
from loguru import logger


from services import EmptyClassroomQueryService, Config

app = Flask(__name__)

# 修改 Jinja2 的变量定界符，避免与 Vue 冲突
app.jinja_env.variable_start_string = "[["
app.jinja_env.variable_end_string = "]]"

# 配置日志
setup_logger()


# 全局服务管理
class ServiceManager:
    """服务管理器 - 管理查询服务的初始化状态和定时刷新"""

    def __init__(self):
        self.initialized = False
        self.last_init = None
        self.error = None
        self.lock = threading.Lock()
        self.query_service = EmptyClassroomQueryService()
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()

    def initialize(self, force=False):
        """初始化服务（登录 + 获取学期信息 + 获取所有教室列表）"""
        with self.lock:
            try:
                logger.info("正在初始化查询服务...")

                # 强制刷新时重新创建服务实例
                if force:
                    self.query_service = EmptyClassroomQueryService()

                success, result = self.query_service.initialize(force=force)

                if success:
                    self.initialized = True
                    self.last_init = datetime.now()
                    self.error = None
                    logger.info(
                        f"初始化成功，时间: {self.last_init.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    return True, result
                else:
                    self.initialized = False
                    self.error = result
                    logger.error(f"初始化失败: {result}")
                    return False, result

            except Exception as e:
                self.initialized = False
                self.error = str(e)
                logger.exception(f"初始化异常: {e}")
                return False, str(e)

    def _refresh_loop(self):
        """定时刷新循环"""
        logger.info(f"定时刷新线程已启动，刷新间隔: {Config.REFRESH_INTERVAL}秒")

        while not self._stop_refresh.is_set():
            # 等待刷新间隔时间
            if self._stop_refresh.wait(timeout=Config.REFRESH_INTERVAL):
                # 如果收到停止信号，退出循环
                break

            # 执行刷新
            try:
                logger.info("定时刷新：开始刷新教室列表...")
                with self.lock:
                    success, result = self.query_service.refresh()
                    if success:
                        self.last_init = datetime.now()
                        logger.info(f"定时刷新成功: {result}")
                    else:
                        logger.warning(f"定时刷新失败: {result}")
            except Exception as e:
                logger.exception(f"定时刷新异常: {e}")

        logger.info("定时刷新线程已停止")

    def start_refresh_thread(self):
        """启动定时刷新线程"""
        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            logger.warning("定时刷新线程已在运行")
            return

        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()

    def stop_refresh_thread(self):
        """停止定时刷新线程"""
        self._stop_refresh.set()
        if self._refresh_thread is not None:
            self._refresh_thread.join(timeout=5)

    def get_status(self):
        """获取服务状态"""
        with self.lock:
            service_info = self.query_service.get_info()
            return {
                "initialized": self.initialized,
                "last_init": (
                    self.last_init.strftime("%Y-%m-%d %H:%M:%S")
                    if self.last_init
                    else None
                ),
                "error": self.error,
                "service_info": service_info,
            }


# 需要导入 Optional
from typing import Optional


# 全局服务实例
service_manager = ServiceManager()


def is_mobile(user_agent_string: str) -> bool:
    """检测是否为移动设备"""
    user_agent = parse(user_agent_string)
    return user_agent.is_mobile or user_agent.is_tablet


@app.route("/")
def index():
    """根据设备类型自动路由到对应页面"""
    user_agent = request.headers.get("User-Agent", "")

    if is_mobile(user_agent):
        return redirect(url_for("mobile"))
    else:
        return redirect(url_for("desktop"))


@app.route("/desktop")
def desktop():
    """PC 端页面 - Element Plus"""
    return render_template("desktop.html")


@app.route("/mobile")
def mobile():
    """移动端页面 - Vant"""
    return render_template("mobile.html")


@app.route("/api/query")
def api_query():
    """API: 实时查询空教室

    请求参数:
        building: 教学楼关键词，如 "格物楼B10"，默认为空（查所有）
        start_section: 开始节次，如 "01", "03"，默认 "01"
        end_section: 结束节次，如 "02", "04"，默认 "02"
        day_offset: 日期偏移，0=今天，1=明天，默认 0

    返回:
        {
            "code": 0,
            "message": "success",
            "data": {
                "date": "2025-01-08",
                "weekday": 3,
                "weekday_name": "三",
                "semester": "2024-2025-1",
                "week": 18,
                "start_section": "01",
                "end_section": "02",
                "building_keyword": "格物楼",
                "empty_classrooms": ["格物楼B101", "格物楼B102", ...],
                "total_count": 10,
                "query_time": "2025-01-08 10:00:00"
            }
        }
    """
    try:
        # 获取请求参数
        building = request.args.get("building", "")
        start_section = request.args.get("start_section", "01")
        end_section = request.args.get("end_section", "02")
        day_offset = int(request.args.get("day_offset", "0"))

        # 调用查询服务
        success, result = service_manager.query_service.query(
            building_keyword=building,
            start_section=start_section,
            end_section=end_section,
            day_offset=day_offset,
        )

        if success:
            return jsonify({"code": 0, "message": "success", "data": result})
        else:
            return jsonify({"code": 1, "message": result, "data": None}), 500

    except ValueError as e:
        return jsonify({"code": 3, "message": f"参数错误: {str(e)}", "data": None}), 400
    except Exception as e:
        return (
            jsonify({"code": 2, "message": f"服务器错误: {str(e)}", "data": None}),
            500,
        )


@app.route("/api/info")
def api_info():
    """API: 获取服务状态信息"""
    try:
        info = service_manager.query_service.get_info()
        return jsonify({"code": 0, "message": "success", "data": info})
    except Exception as e:
        return (
            jsonify({"code": 2, "message": f"服务器错误: {str(e)}", "data": None}),
            500,
        )


@app.route("/api/health")
def api_health():
    """API: 健康检查"""
    valid, msg = Config.validate()
    status = service_manager.get_status()
    return jsonify(
        {
            "status": "ok" if valid and status["initialized"] else "error",
            "config_valid": valid,
            "config_message": msg,
            "service": status,
        }
    )


def main():
    """启动 Flask 服务"""
    logger.info("=" * 50)
    logger.info("空教室查询 Web 服务")
    logger.info("=" * 50)

    # 验证配置
    valid, msg = Config.validate()
    if not valid:
        logger.error(msg)
        return 1

    logger.info(f"账号: {Config.USERNAME[:4]}****")
    logger.info(f"刷新间隔: {Config.REFRESH_INTERVAL}秒")

    # 启动时初始化服务（优先从缓存恢复）
    logger.info("正在初始化查询服务...")
    success, result = service_manager.initialize()
    if success:
        logger.info(f"服务初始化成功: {result}")
    else:
        logger.warning(f"服务初始化失败: {result}")
        logger.warning("服务将继续启动，等待定时刷新重试")

    # 启动定时刷新线程
    service_manager.start_refresh_thread()

    logger.info(f"地址: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    logger.info("=" * 50)

    try:
        app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
    finally:
        # 停止定时刷新线程
        service_manager.stop_refresh_thread()

    return 0


if __name__ == "__main__":
    exit(main())
