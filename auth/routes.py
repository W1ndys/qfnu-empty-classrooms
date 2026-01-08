#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
前端访问验证路由模块

提供前端访问密码验证的 API 和页面路由
"""

from flask import render_template, request, jsonify, session, redirect, url_for

from . import auth_bp
from services import Config
from database import get_config


# ============ 页面路由 ============

@auth_bp.route('/verify')
def verify():
    """前端验证页面"""
    # 检查是否开启前端验证
    enable_auth = get_config('enable_frontend_auth')
    if enable_auth is None:
        enable_auth = Config.ENABLE_FRONTEND_AUTH
    else:
        enable_auth = enable_auth.lower() == 'true' or enable_auth == '1'

    # 如果未开启验证或已验证，重定向到首页
    if not enable_auth or session.get('frontend_verified'):
        return redirect('/')

    return render_template('auth/verify.html')


# ============ 验证 API ============

@auth_bp.route('/api/verify', methods=['POST'])
def api_verify():
    """前端访问验证 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'message': '请求数据为空', 'data': None}), 400

        password = data.get('password', '')
        if not password:
            return jsonify({'code': 1, 'message': '请输入密码', 'data': None}), 400

        # 获取前端访问密码（优先从数据库，其次从环境变量）
        stored_password = get_config('frontend_password')
        if stored_password is None:
            stored_password = Config.FRONTEND_PASSWORD

        # 验证密码
        if password == stored_password:
            session['frontend_verified'] = True
            session.permanent = True
            # 保存当前密码版本号，用于检测密码变更
            session['frontend_password_version'] = get_config('frontend_password_version') or '0'
            return jsonify({'code': 0, 'message': '验证成功', 'data': None})

        return jsonify({'code': 1, 'message': '密码错误', 'data': None}), 401

    except Exception as e:
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500


@auth_bp.route('/api/check', methods=['GET'])
def api_check():
    """检查前端验证状态 API"""
    try:
        # 检查是否开启前端验证
        enable_auth = get_config('enable_frontend_auth')
        if enable_auth is None:
            enable_auth = Config.ENABLE_FRONTEND_AUTH
        else:
            enable_auth = enable_auth.lower() == 'true' or enable_auth == '1'

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'auth_enabled': enable_auth,
                'verified': session.get('frontend_verified', False)
            }
        })

    except Exception as e:
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500
