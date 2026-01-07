#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志配置模块

使用 loguru 进行日志记录，按日期命名和分割日志文件
"""

import sys
from pathlib import Path
from loguru import logger

# 日志目录
LOG_DIR = Path(__file__).parent / "logs"

# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)


def setup_logger():
    """配置 loguru 日志器"""
    # 移除默认的 handler
    logger.remove()

    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 控制台输出（简化格式）
    console_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )

    # 添加控制台 handler
    logger.add(
        sys.stderr,
        format=console_format,
        level="INFO",
        colorize=True,
    )

    # 添加文件 handler - 按日期分割
    logger.add(
        LOG_DIR / "{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="00:00",  # 每天午夜分割
        retention="30 days",  # 保留 30 天
        encoding="utf-8",
        enqueue=True,  # 异步写入，提高性能
    )

    # 添加错误日志文件 - 单独记录 ERROR 及以上级别
    logger.add(
        LOG_DIR / "{time:YYYY-MM-DD}_error.log",
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        enqueue=True,
    )

    return logger


# 初始化日志器
setup_logger()
