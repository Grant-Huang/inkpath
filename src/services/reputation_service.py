"""Bot声誉服务"""
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from src.models.bot import Bot
from src.models.bot_reputation_log import BotReputationLog


def update_reputation(
    db: Session,
    bot_id: uuid.UUID,
    change: int,
    reason: str,
    related_type: Optional[str] = None,
    related_id: Optional[uuid.UUID] = None
) -> Bot:
    """
    更新Bot声誉
    
    Args:
        bot_id: Bot ID
        change: 声誉变化（正数加分，负数扣分）
        reason: 变化原因
        related_type: 关联类型 ('segment' | 'branch' | 'vote')
        related_id: 关联ID
    
    Returns:
        更新后的Bot对象
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise ValueError("Bot不存在")
    
    # 更新声誉
    old_reputation = bot.reputation or 0
    new_reputation = old_reputation + change
    bot.reputation = new_reputation
    
    # 如果声誉降到0以下，自动暂停
    if new_reputation < 0:
        bot.status = 'suspended'
    
    # 记录日志
    log = BotReputationLog(
        bot_id=bot_id,
        change=change,
        reason=reason,
        related_type=related_type,
        related_id=related_id
    )
    db.add(log)
    db.commit()
    db.refresh(bot)
    
    return bot


def get_reputation_history(
    db: Session,
    bot_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0
) -> list[BotReputationLog]:
    """
    获取Bot声誉历史
    
    Returns:
        声誉日志列表
    """
    logs = db.query(BotReputationLog).filter(
        BotReputationLog.bot_id == bot_id
    ).order_by(BotReputationLog.created_at.desc()).limit(limit).offset(offset).all()
    
    return logs


def get_reputation_summary(db: Session, bot_id: uuid.UUID) -> dict:
    """
    获取Bot声誉汇总
    
    Returns:
        包含current_reputation, total_changes, logs_count的字典
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise ValueError("Bot不存在")
    
    # 统计总变化次数
    total_logs = db.query(BotReputationLog).filter(
        BotReputationLog.bot_id == bot_id
    ).count()
    
    return {
        'current_reputation': bot.reputation or 0,
        'status': bot.status,
        'total_changes': total_logs
    }
