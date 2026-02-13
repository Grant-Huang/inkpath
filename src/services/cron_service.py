"""定时任务服务 - 增强版"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.models.bot import Bot
from src.models.bot_branch_membership import BotBranchMembership
from src.services.reputation_service import update_reputation


def check_bot_timeouts(db: Session) -> Dict[str, Any]:
    """
    检查Bot超时并扣声誉分，同时清理不活跃的分支成员关系
    
    规则：
    - 检查所有状态为'active'的Bot
    - 如果updated_at超过1小时未更新，扣5分
    - 如果声誉降到0以下，自动暂停Bot
    - 清理超过2小时未活动的 BotBranchMembership
    
    Returns:
        包含检查结果的字典
    """
    now = datetime.utcnow()
    timeout_threshold = now - timedelta(hours=1)
    membership_threshold = now - timedelta(hours=2)  # 2小时无活动的 membership
    
    # 1. 查找超时的Bot（updated_at超过1小时）
    timeout_bots = db.query(Bot).filter(
        and_(
            Bot.status == 'active',
            Bot.updated_at < timeout_threshold
        )
    ).all()
    
    # 2. 清理不活跃的分支成员关系（2小时无活动）
    inactive_memberships = db.query(BotBranchMembership).filter(
        BotBranchMembership.joined_at < membership_threshold
    ).all()
    
    results = {
        'checked_at': now.isoformat(),
        'timeout_threshold': timeout_threshold.isoformat(),
        'membership_threshold': membership_threshold.isoformat(),
        'timeout_bots_count': len(timeout_bots),
        'inactive_memberships_count': len(inactive_memberships),
        'processed_bots': [],
        'cleaned_memberships': [],
        'errors': []
    }
    
    # 3. 处理超时的 Bot
    for bot in timeout_bots:
        try:
            old_reputation = bot.reputation or 0
            old_status = bot.status
            
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
    
    # 4. 清理不活跃的 membership
    for membership in inactive_memberships:
        try:
            bot = db.query(Bot).filter(Bot.id == membership.bot_id).first()
            bot_name = bot.name if bot else "Unknown"
            
            db.delete(membership)
            db.commit()
            
            results['cleaned_memberships'].append({
                'bot_id': str(membership.bot_id),
                'bot_name': bot_name,
                'branch_id': str(membership.branch_id),
                'joined_at': membership.joined_at.isoformat() if membership.joined_at else None
            })
        except Exception as e:
            results['errors'].append({
                'membership_bot_id': str(membership.bot_id),
                'membership_branch_id': str(membership.branch_id),
                'error': str(e)
            })
    
    return results


def cleanup_stuck_memberships(db: Session, hours: int = 1) -> Dict[str, Any]:
    """
    清理"卡住"的 Bot 分支成员关系
    
    检测条件：
    - Bot 的 updated_at 超过 N 小时未更新
    - 但 membership 仍然存在于分支中
    
    这可以快速清理那些已经"死掉"但还占用位置的 Bot
    
    Args:
        db: 数据库会话
        hours: 多少小时无更新视为不活跃
    
    Returns:
        包含清理结果的字典
    """
    now = datetime.utcnow()
    threshold = now - timedelta(hours=hours)
    
    # 查找不活跃的 Bot（updated_at 超过阈值）
    inactive_bots = db.query(Bot).filter(
        and_(
            Bot.status == 'active',
            Bot.updated_at < threshold
        )
    ).all()
    
    inactive_bot_ids = [bot.id for bot in inactive_bots]
    
    # 查找这些 Bot 的 membership
    stuck_memberships = db.query(BotBranchMembership).filter(
        BotBranchMembership.bot_id.in_(inactive_bot_ids)
    ).all()
    
    results = {
        'cleaned_at': now.isoformat(),
        'threshold_hours': hours,
        'inactive_bots_count': len(inactive_bots),
        'stuck_memberships_count': len(stuck_memberships),
        'cleaned': [],
        'errors': []
    }
    
    for membership in stuck_memberships:
        try:
            bot = db.query(Bot).filter(Bot.id == membership.bot_id).first()
            bot_name = bot.name if bot else "Unknown"
            last_active = bot.updated_at.isoformat() if bot and bot.updated_at else "Never"
            
            db.delete(membership)
            db.commit()
            
            results['cleaned'].append({
                'bot_id': str(membership.bot_id),
                'bot_name': bot_name,
                'branch_id': str(membership.branch_id),
                'last_active': last_active
            })
            
            print(f"🧹 清理卡住的 membership: Bot={bot_name}, Branch={str(membership.branch_id)[:8]}...")
            
        except Exception as e:
            results['errors'].append({
                'bot_id': str(membership.bot_id),
                'branch_id': str(membership.branch_id),
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
    """
    from src.services.activity_service import update_all_branch_activity_scores
    return update_all_branch_activity_scores(db)


def cleanup_expired_data(db: Session) -> Dict[str, Any]:
    """
    清理过期数据（定时任务）
    """
    results = {
        'cleaned_at': datetime.utcnow().isoformat(),
        'cleaned_items': [],
        'errors': []
    }
    
    return results
