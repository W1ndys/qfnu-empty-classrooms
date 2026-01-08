#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
后台管理模块

提供管理员登录、公告管理、系统配置等功能
"""

from flask import Blueprint

# 创建 Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 导入路由（必须在 Blueprint 创建后导入，避免循环导入）
from . import routes  # noqa: F401, E402
