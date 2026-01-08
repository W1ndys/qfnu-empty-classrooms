#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模块

提供 SQLite 数据库初始化、连接管理和配置读写功能
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Any, List, Dict
from pathlib import Path

from loguru import logger

# 数据库文件路径
DB_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "instance"
DB_FILE = DB_DIR / "app.db"


def get_db_path() -> Path:
    """获取数据库文件路径"""
    return DB_FILE


def init_db() -> None:
    """初始化数据库，创建所需的表"""
    logger.info("数据库初始化开始")

    # 确保目录存在
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()

    try:
        # 创建公告表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                type VARCHAR(20) DEFAULT 'info',
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                start_time DATETIME,
                end_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("数据库表创建成功")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        conn.close()


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row  # 返回字典形式的结果
    try:
        yield conn
    finally:
        conn.close()


# ============ 配置管理函数 ============

def get_config(key: str, default: Any = None) -> Optional[str]:
    """获取配置值

    Args:
        key: 配置键名
        default: 默认值

    Returns:
        配置值，不存在则返回默认值
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default


def set_config(key: str, value: str) -> bool:
    """设置配置值

    Args:
        key: 配置键名
        value: 配置值

    Returns:
        是否设置成功
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, (key, value, datetime.now().isoformat()))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"设置配置失败: {e}")
        return False


def get_all_config() -> Dict[str, str]:
    """获取所有配置"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM config")
        rows = cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}


# ============ 公告管理函数 ============

def get_announcements(active_only: bool = False) -> List[Dict]:
    """获取公告列表

    Args:
        active_only: 是否只获取启用的公告

    Returns:
        公告列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if active_only:
            now = datetime.now().isoformat()
            cursor.execute("""
                SELECT * FROM announcements
                WHERE is_active = 1
                AND (start_time IS NULL OR start_time <= ?)
                AND (end_time IS NULL OR end_time >= ?)
                ORDER BY priority DESC, created_at DESC
            """, (now, now))
        else:
            cursor.execute("""
                SELECT * FROM announcements
                ORDER BY priority DESC, created_at DESC
            """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_announcement_by_id(announcement_id: int) -> Optional[Dict]:
    """根据ID获取公告

    Args:
        announcement_id: 公告ID

    Returns:
        公告信息，不存在返回 None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM announcements WHERE id = ?", (announcement_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_announcement(
    title: str,
    content: str,
    type: str = "info",
    is_active: bool = True,
    priority: int = 0,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Optional[int]:
    """创建公告

    Args:
        title: 标题
        content: 内容
        type: 类型 (info/warning/success/error)
        is_active: 是否启用
        priority: 优先级
        start_time: 开始时间
        end_time: 结束时间

    Returns:
        新创建的公告ID，失败返回 None
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO announcements
                (title, content, type, is_active, priority, start_time, end_time, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, content, type, is_active, priority, start_time, end_time, now, now))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"创建公告失败: {e}")
        return None


def update_announcement(
    announcement_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    type: Optional[str] = None,
    is_active: Optional[bool] = None,
    priority: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> bool:
    """更新公告

    Args:
        announcement_id: 公告ID
        其他参数: 要更新的字段，None 表示不更新

    Returns:
        是否更新成功
    """
    try:
        # 构建动态更新语句
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if type is not None:
            updates.append("type = ?")
            params.append(type)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if start_time is not None:
            updates.append("start_time = ?")
            params.append(start_time if start_time else None)
        if end_time is not None:
            updates.append("end_time = ?")
            params.append(end_time if end_time else None)

        if not updates:
            return True  # 没有要更新的字段

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(announcement_id)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE announcements SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"更新公告失败: {e}")
        return False


def delete_announcement(announcement_id: int) -> bool:
    """删除公告

    Args:
        announcement_id: 公告ID

    Returns:
        是否删除成功
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"删除公告失败: {e}")
        return False
