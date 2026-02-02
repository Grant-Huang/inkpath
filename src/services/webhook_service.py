"""Webhook服务"""
import uuid
from typing import Optional
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from src.models.bot import Bot


def validate_webhook_url(url: str) -> tuple[bool, Optional[str]]:
    """
    验证Webhook URL
    
    Returns:
        (是否有效, 错误信息)
    """
    if not url or url.strip() == "":
        return False, "Webhook URL不能为空"
    
    try:
        parsed = urlparse(url)
        
        # 必须是HTTP或HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False, "Webhook URL必须是HTTP或HTTPS协议"
        
        # 必须有主机名
        if not parsed.netloc or not parsed.hostname:
            return False, "Webhook URL必须包含有效的主机名"
        
        # 不能是localhost或127.0.0.1（生产环境）
        if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            # 允许在开发环境中使用
            pass
        
        return True, None
    
    except Exception as e:
        return False, f"无效的URL格式: {str(e)}"


def update_webhook_url(
    db: Session,
    bot_id: uuid.UUID,
    webhook_url: str
) -> Bot:
    """
    更新Bot的Webhook URL
    
    Returns:
        更新后的Bot对象
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise ValueError("Bot不存在")
    
    # 验证URL
    is_valid, error_msg = validate_webhook_url(webhook_url)
    if not is_valid:
        raise ValueError(error_msg)
    
    bot.webhook_url = webhook_url
    db.commit()
    db.refresh(bot)
    
    return bot


def get_webhook_status(db: Session, bot_id: uuid.UUID) -> dict:
    """
    获取Bot的Webhook状态
    
    Returns:
        包含webhook_url, is_configured的字典
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise ValueError("Bot不存在")
    
    return {
        'webhook_url': bot.webhook_url,
        'is_configured': bot.webhook_url is not None and bot.webhook_url != ''
    }
