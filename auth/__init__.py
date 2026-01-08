#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
前端访问验证模块

提供前端访问密码验证功能
"""

from flask import Blueprint

# 创建 Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 导入路由（必须在 Blueprint 创建后导入，避免循环导入）
from . import routes  # noqa: F401, E402
