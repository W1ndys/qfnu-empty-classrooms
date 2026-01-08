#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
后台管理路由模块

提供管理员登录、公告管理、系统配置等 API 和页面路由
"""

from flask import render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from loguru import logger

from . import admin_bp
from .decorators import admin_required
from services import Config
from database import (
    get_config, set_config, get_all_config,
    get_announcements, get_announcement_by_id,
    create_announcement, update_announcement, delete_announcement
)


# ============ 页面路由 ============

@admin_bp.route('/')
@admin_required
def index():
    """管理后台首页"""
    return render_template('admin/dashboard.html')


@admin_bp.route('/login')
def login():
    """管理员登录页面"""
    # 如果已登录，重定向到后台首页
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.index'))
    return render_template('admin/login.html')


# ============ 认证 API ============

@admin_bp.route('/api/login', methods=['POST'])
def api_login():
    """管理员登录 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'message': '请求数据为空', 'data': None}), 400

        password = data.get('password', '')
        if not password:
            return jsonify({'code': 1, 'message': '请输入密码', 'data': None}), 400

        # 获取管理员密码（优先从数据库，其次从环境变量）
        stored_password_hash = get_config('admin_password_hash')

        if stored_password_hash:
            # 数据库中有密码哈希，使用哈希验证
            if check_password_hash(stored_password_hash, password):
                session['admin_logged_in'] = True
                session.permanent = True
                logger.info("管理员登录成功（使用数据库密码）")
                return jsonify({'code': 0, 'message': '登录成功', 'data': None})
        else:
            # 使用环境变量中的密码（明文比较，首次登录）
            if password == Config.ADMIN_PASSWORD:
                session['admin_logged_in'] = True
                session.permanent = True
                # 首次登录成功后，将密码哈希存入数据库
                set_config('admin_password_hash', generate_password_hash(password))
                logger.info("管理员登录成功（使用环境变量密码，已保存哈希）")
                return jsonify({'code': 0, 'message': '登录成功', 'data': None})

        logger.warning("管理员登录失败：密码错误")
        return jsonify({'code': 1, 'message': '密码错误', 'data': None}), 401

    except Exception as e:
        logger.error(f"登录异常: {e}")
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500


@admin_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """管理员退出登录 API"""
    session.pop('admin_logged_in', None)
    logger.info("管理员已退出登录")
    return jsonify({'code': 0, 'message': '已退出登录', 'data': None})


# ============ 公告管理 API ============

@admin_bp.route('/api/announcements', methods=['GET'])
@admin_required
def api_get_announcements():
    """获取公告列表"""
    try:
        announcements = get_announcements(active_only=False)
        return jsonify({'code': 0, 'message': 'success', 'data': announcements})
    except Exception as e:
        logger.error(f"获取公告列表失败: {e}")
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500


@admin_bp.route('/api/announcements', methods=['POST'])
@admin_required
def api_create_announcement():
    """创建公告"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'message': '请求数据为空', 'data': None}), 400

        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({'code': 1, 'message': '标题和内容不能为空', 'data': None}), 400

        announcement_id = create_announcement(
            title=title,
            content=content,
            type=data.get('type', 'info'),
            is_active=data.get('is_active', True),
            priority=data.get('priority', 0),
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )

        if announcement_id:
            logger.info(f"创建公告成功: ID={announcement_id}, 标题={title}")
            return jsonify({'code': 0, 'message': '创建成功', 'data': {'id': announcement_id}})
        else:
            return jsonify({'code': 1, 'message': '创建失败', 'data': None}), 500

    except Exception as e:
        logger.error(f"创建公告异常: {e}")
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500


@admin_bp.route('/api/announcements/<int:announcement_id>', methods=['PUT'])
@admin_required
def api_update_announcement(announcement_id):
    """更新公告"""
    try:
        # 检查公告是否存在
        existing = get_announcement_by_id(announcement_id)
        if not existing:
            return jsonify({'code': 1, 'message': '公告不存在', 'data': None}), 404

        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'message': '请求数据为空', 'data': None}), 400

        success = update_announcement(
            announcement_id=announcement_id,
            title=data.get('title'),
            content=data.get('content'),
            type=data.get('type'),
            is_active=data.get('is_active'),
            priority=data.get('priority'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )

        if success:
            logger.info(f"更新公告成功: ID={announcement_id}")
            return jsonify({'code': 0, 'message': '更新成功', 'data': None})
        else:
            return jsonify({'code': 1, 'message': '更新失败', 'data': None}), 500

    except Exception as e:
        logger.error(f"更新公告异常: {e}")
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500


@admin_bp.route('/api/announcements/<int:announcement_id>', methods=['DELETE'])
@admin_required
def api_delete_announcement(announcement_id):
    """删除公告"""
    try:
        # 检查公告是否存在
        existing = get_announcement_by_id(announcement_id)
        if not existing:
            return jsonify({'code': 1, 'message': '公告不存在', 'data': None}), 404

        success = delete_announcement(announcement_id)

        if success:
            logger.info(f"删除公告成功: ID={announcement_id}")
            return jsonify({'code': 0, 'message': '删除成功', 'data': None})
        else:
            return jsonify({'code': 1, 'message': '删除失败', 'data': None}), 500

    except Exception as e:
        logger.error(f"删除公告异常: {e}")
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500


# ============ 配置管理 API ============

@admin_bp.route('/api/config', methods=['GET'])
@admin_required
def api_get_config():
    """获取系统配置"""
    try:
        # 从数据库获取配置
        db_config = get_all_config()

        # 构建配置响应（敏感信息不返回）
        config_data = {
            'enable_frontend_auth': db_config.get('enable_frontend_auth', str(Config.ENABLE_FRONTEND_AUTH).lower()),
            'frontend_password': db_config.get('frontend_password', Config.FRONTEND_PASSWORD) or '',
            'site_title': db_config.get('site_title', '空教室查询系统'),
        }

        return jsonify({'code': 0, 'message': 'success', 'data': config_data})
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500


@admin_bp.route('/api/config', methods=['PUT'])
@admin_required
def api_update_config():
    """更新系统配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 1, 'message': '请求数据为空', 'data': None}), 400

        # 记录前端密码是否变更
        frontend_password_changed = False

        # 更新各项配置
        if 'enable_frontend_auth' in data:
            set_config('enable_frontend_auth', str(data['enable_frontend_auth']).lower())

        if 'frontend_password' in data:
            old_frontend_password = get_config('frontend_password') or Config.FRONTEND_PASSWORD
            new_frontend_password = data['frontend_password']
            if old_frontend_password != new_frontend_password:
                set_config('frontend_password', new_frontend_password)
                frontend_password_changed = True

        if 'site_title' in data:
            set_config('site_title', data['site_title'])

        # 更新管理员密码（需要验证旧密码）
        if 'new_admin_password' in data and data['new_admin_password']:
            old_password = data.get('old_admin_password', '')
            new_password = data['new_admin_password']

            # 验证旧密码
            stored_hash = get_config('admin_password_hash')
            if stored_hash:
                if not check_password_hash(stored_hash, old_password):
                    return jsonify({'code': 1, 'message': '原密码错误', 'data': None}), 400
            else:
                if old_password != Config.ADMIN_PASSWORD:
                    return jsonify({'code': 1, 'message': '原密码错误', 'data': None}), 400

            # 保存新密码哈希
            set_config('admin_password_hash', generate_password_hash(new_password))
            logger.info("管理员密码已更新")

        # 如果前端密码变更，更新密码版本号，使所有用户的验证失效
        if frontend_password_changed:
            import time
            set_config('frontend_password_version', str(int(time.time())))
            logger.info("前端访问密码已更新，所有用户需要重新验证")

        logger.info("系统配置已更新")
        return jsonify({'code': 0, 'message': '配置更新成功', 'data': None})

    except Exception as e:
        logger.error(f"更新配置异常: {e}")
        return jsonify({'code': 2, 'message': f'服务器错误: {str(e)}', 'data': None}), 500
