#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
空教室查询 Flask Web 服务

功能：
1. 自动检测设备类型，路由到不同的前端页面
2. PC 端使用 Element Plus 组件库
3. 移动端使用 Vant 组件库
4. 提供 API 接口查询空教室数据
5. 启动时预加载数据，使用缓存避免频繁请求教务系统
"""

import os
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from user_agents import parse

from services import EmptyClassroomQueryService, Config

app = Flask(__name__)

# 修改 Jinja2 的变量定界符，避免与 Vue 冲突
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'

# 全局数据缓存
class DataCache:
    def __init__(self):
        self.data = None
        self.last_update = None
        self.error = None
        self.lock = threading.Lock()
        self.query_service = EmptyClassroomQueryService()

    def get_data(self):
        """获取缓存的数据"""
        with self.lock:
            if self.data:
                return True, self.data
            elif self.error:
                return False, self.error
            else:
                return False, "数据尚未加载"

    def refresh(self, force=False):
        """刷新数据"""
        with self.lock:
            try:
                print("[数据] 正在从教务系统获取数据...")

                # 强制刷新时重新初始化服务
                if force:
                    self.query_service = EmptyClassroomQueryService()

                success, result = self.query_service.query_tomorrow()

                if success:
                    self.data = result
                    self.last_update = datetime.now()
                    self.error = None
                    print(f"[数据] 数据获取成功，更新时间: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                    return True, result
                else:
                    self.error = result
                    print(f"[数据] 数据获取失败: {result}")
                    return False, result

            except Exception as e:
                self.error = str(e)
                print(f"[数据] 数据获取异常: {e}")
                return False, str(e)

    def get_status(self):
        """获取缓存状态"""
        with self.lock:
            return {
                "has_data": self.data is not None,
                "last_update": self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None,
                "error": self.error
            }

# 全局缓存实例
cache = DataCache()


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


@app.route("/api/classrooms")
def api_classrooms():
    """API: 获取空教室数据（从缓存读取）"""
    try:
        success, result = cache.get_data()

        if success:
            return jsonify({
                "code": 0,
                "message": "success",
                "data": result
            })
        else:
            return jsonify({
                "code": 1,
                "message": result,
                "data": None
            }), 500

    except Exception as e:
        return jsonify({
            "code": 2,
            "message": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route("/api/refresh")
def api_refresh():
    """API: 强制刷新数据（重新登录并查询教务系统）"""
    try:
        success, result = cache.refresh(force=True)

        if success:
            return jsonify({
                "code": 0,
                "message": "刷新成功",
                "data": result
            })
        else:
            return jsonify({
                "code": 1,
                "message": result,
                "data": None
            }), 500

    except Exception as e:
        return jsonify({
            "code": 2,
            "message": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route("/api/health")
def api_health():
    """API: 健康检查"""
    valid, msg = Config.validate()
    status = cache.get_status()
    return jsonify({
        "status": "ok" if valid and status["has_data"] else "error",
        "config_valid": valid,
        "config_message": msg,
        "buildings": Config.get_buildings(),
        "cache": status
    })


def main():
    """启动 Flask 服务"""
    print("=" * 50)
    print("空教室查询 Web 服务")
    print("=" * 50)

    # 验证配置
    valid, msg = Config.validate()
    if not valid:
        print(f"[错误] {msg}")
        return 1

    print(f"[配置] 账号: {Config.USERNAME[:4]}****")
    print(f"[配置] 教学楼: {Config.get_buildings()}")

    # 启动时预加载数据
    print("[启动] 正在预加载空教室数据...")
    success, result = cache.refresh()
    if success:
        print("[启动] 数据预加载成功")
    else:
        print(f"[警告] 数据预加载失败: {result}")
        print("[警告] 服务将继续启动，可稍后通过 /api/refresh 重试")

    print(f"[服务] 地址: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print("=" * 50)

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )

    return 0


if __name__ == "__main__":
    exit(main())
