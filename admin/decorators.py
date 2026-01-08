#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
认证装饰器模块

提供管理员认证和前端访问验证的装饰器
"""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify

from services import Config
from database import get_config


def admin_required(f):
    """管理员认证装饰器

    检查用户是否已登录管理后台，未登录则重定向到登录页面
    对于 API 请求返回 JSON 错误响应
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            # 判断是否为 API 请求
            if request.path.startswith('/admin/api/'):
                return jsonify({
                    'code': 401,
                    'message': '未登录或登录已过期',
                    'data': None
                }), 401
            # 页面请求重定向到登录页
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


def frontend_auth_required(f):
    """前端访问验证装饰器

    检查是否开启了前端访问验证，如果开启则检查用户是否已验证
    未验证则重定向到验证页面
    管理员已登录则跳过验证
    密码变更后需要重新验证
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from loguru import logger

        # 管理员已登录，跳过前端验证
        if session.get('admin_logged_in'):
            logger.debug("管理员已登录，跳过前端验证")
            return f(*args, **kwargs)

        # 检查是否开启前端验证
        # 优先从数据库读取配置，其次从环境变量读取
        enable_auth = get_config('enable_frontend_auth')
        logger.debug(f"数据库 enable_frontend_auth 值: {enable_auth}, 类型: {type(enable_auth)}")

        if enable_auth is None:
            enable_auth = Config.ENABLE_FRONTEND_AUTH
            logger.debug(f"使用环境变量配置: {enable_auth}")
        else:
            enable_auth = enable_auth.lower() == 'true' or enable_auth == '1'
            logger.debug(f"转换后的 enable_auth: {enable_auth}")

        if not enable_auth:
            # 未开启验证，直接放行
            logger.debug("前端验证未开启，直接放行")
            return f(*args, **kwargs)

        # 检查是否已验证
        if not session.get('frontend_verified'):
            # 判断是否为 API 请求
            if request.path.startswith('/api/'):
                return jsonify({
                    'code': 403,
                    'message': '需要验证访问权限',
                    'data': None
                }), 403
            # 页面请求重定向到验证页
            return redirect(url_for('auth.verify'))

        # 检查密码版本号是否匹配（密码变更后需要重新验证）
        current_version = get_config('frontend_password_version') or '0'
        session_version = session.get('frontend_password_version', '0')
        if current_version != session_version:
            # 密码已变更，清除验证状态
            session.pop('frontend_verified', None)
            session.pop('frontend_password_version', None)
            # 判断是否为 API 请求
            if request.path.startswith('/api/'):
                return jsonify({
                    'code': 403,
                    'message': '访问密码已变更，请重新验证',
                    'data': None
                }), 403
            # 页面请求重定向到验证页
            return redirect(url_for('auth.verify'))

        return f(*args, **kwargs)
    return decorated_function
