"""定时任务服务"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.models.bot import Bot
from src.services.reputation_service import update_reputation


def check_bot_timeouts(db: Session) -> Dict[str, Any]:
    """
    检查Bot超时并扣声誉分
    
    规则：
    - 检查所有状态为'active'的Bot
    - 如果updated_at超过1小时未更新，扣5分
    - 如果声誉降到0以下，自动暂停Bot
    
    Returns:
        包含检查结果的字典
    """
    now = datetime.utcnow()
    timeout_threshold = now - timedelta(hours=1)
    
    # 查找超时的Bot（updated_at超过1小时）
    timeout_bots = db.query(Bot).filter(
        and_(
            Bot.status == 'active',
            Bot.updated_at < timeout_threshold
        )
    ).all()
    
    results = {
        'checked_at': now.isoformat(),
        'timeout_threshold': timeout_threshold.isoformat(),
        'timeout_bots_count': len(timeout_bots),
        'processed_bots': [],
        'errors': []
    }
    
    for bot in timeout_bots:
        try:
            # 保存旧值（因为update_reputation会更新updated_at）
            old_reputation = bot.reputation or 0
            old_status = bot.status
            
            # 扣5分
            updated_bot = update_reputation(
                db=db,
                bot_id=bot.id,
                change=-5,
                reason='Bot超时未响应（超过1小时）',
                related_type='timeout'
            )
            
            results['processed_bots'].append({
                'bot_id': str(bot.id),
                'bot_name': bot.name,
                'old_reputation': old_reputation,
                'new_reputation': updated_bot.reputation or 0,
                'status': updated_bot.status,
                'was_suspended': updated_bot.status == 'suspended' and old_status == 'active'
            })
        except Exception as e:
            results['errors'].append({
                'bot_id': str(bot.id),
                'error': str(e)
            })
    
    return results


def update_bot_activity(db: Session, bot_id: uuid.UUID):
    """
    更新Bot活动时间（更新updated_at字段）
    
    在Bot执行操作时调用，如：
    - 提交续写
    - 创建分支
    - 加入分支
    - 投票
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if bot:
        bot.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(bot)


def update_activity_scores(db: Session) -> Dict[str, Any]:
    """
    更新所有分支的活跃度得分（定时任务）
    
    Returns:
        包含更新结果的字典
    """
    from src.services.activity_service import update_all_branch_activity_scores
    return update_all_branch_activity_scores(db)


def cleanup_expired_data(db: Session) -> Dict[str, Any]:
    """
    清理过期数据（定时任务）
    
    目前实现：
    - 清理过期的速率限制记录（Redis自动过期，无需清理）
    - 清理过期的活跃度得分缓存（Redis自动过期，无需清理）
    - 未来可以添加：清理归档的故事、清理旧的日志等
    
    Returns:
        包含清理结果的字典
    """
    results = {
        'cleaned_at': datetime.utcnow().isoformat(),
        'cleaned_items': [],
        'errors': []
    }
    
    # 目前没有需要清理的数据库数据
    # Redis中的缓存数据会自动过期，无需手动清理
    
    # 未来可以添加：
    # - 清理归档的故事（status='archived'且超过一定时间）
    # - 清理旧的日志记录
    # - 清理过期的会话数据等
    
    return results
