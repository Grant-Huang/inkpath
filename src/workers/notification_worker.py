"""通知Worker（使用RQ）"""
import uuid
import os
import sys
from typing import Dict, Any
from rq import get_current_job

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.notification_service import (
    send_webhook_notification,
    build_your_turn_notification,
    build_new_branch_notification
)
from src.database import get_db


def send_notification_job(
    bot_id: str,
    event: str,
    data: Dict[str, Any]
) -> bool:
    """
    RQ Job: 发送Webhook通知
    
    Args:
        bot_id: Bot ID (字符串)
        event: 事件类型
        data: 事件数据
    
    Returns:
        是否成功
    """
    bot_uuid = uuid.UUID(bot_id)
    
    success, error_msg = send_webhook_notification(
        bot_uuid, event, data, timeout=10
    )
    
    if not success:
        # 抛出异常以触发重试
        raise Exception(f"Webhook通知失败: {error_msg}")
    
    return True


def send_your_turn_notification_job(
    bot_id: str,
    branch_id: str
) -> bool:
    """
    RQ Job: 发送"轮到续写"通知
    
    Args:
        bot_id: Bot ID (字符串)
        branch_id: 分支ID (字符串)
    
    Returns:
        是否成功
    """
    from src.database import get_db
    db = next(get_db())
    
    bot_uuid = uuid.UUID(bot_id)
    branch_uuid = uuid.UUID(branch_id)
    
    # 构建通知数据
    notification_data = build_your_turn_notification(db, bot_uuid, branch_uuid)
    
    # 发送通知
    success, error_msg = send_webhook_notification(
        bot_uuid, 'your_turn', notification_data, timeout=10
    )
    
    if not success:
        raise Exception(f"Webhook通知失败: {error_msg}")
    
    return True


def send_new_branch_notification_job(
    bot_id: str,
    branch_id: str
) -> bool:
    """
    RQ Job: 发送"新分支创建"通知
    
    Args:
        bot_id: Bot ID (字符串)
        branch_id: 分支ID (字符串)
    
    Returns:
        是否成功
    """
    from src.database import get_db
    db = next(get_db())
    
    bot_uuid = uuid.UUID(bot_id)
    branch_uuid = uuid.UUID(branch_id)
    
    # 构建通知数据
    notification_data = build_new_branch_notification(db, branch_uuid)
    
    # 发送通知
    success, error_msg = send_webhook_notification(
        bot_uuid, 'new_branch', notification_data, timeout=10
    )
    
    if not success:
        raise Exception(f"Webhook通知失败: {error_msg}")
    
    return True
