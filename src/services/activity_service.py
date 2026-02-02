"""活跃度得分服务"""
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from src.models.branch import Branch
from src.models.segment import Segment
from src.models.bot_branch_membership import BotBranchMembership
from src.models.vote import Vote
from src.services.vote_service import calculate_score
from redis import Redis
from src.config import Config


def get_redis_connection():
    """获取Redis连接"""
    return Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True
    )


def calculate_activity_score(
    db: Session,
    branch_id: uuid.UUID
) -> float:
    """
    计算分支活跃度得分
    
    公式：vote_score * 0.5 + segments_count * 0.3 + active_bots_count * 0.2
    
    Args:
        branch_id: 分支ID
    
    Returns:
        活跃度得分
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError("分支不存在")
    
    # 计算投票得分（所有segment的投票得分之和）
    segments = db.query(Segment).filter(Segment.branch_id == branch_id).all()
    vote_score = 0.0
    for segment in segments:
        segment_score = calculate_score(db, 'segment', segment.id)
        vote_score += segment_score
    
    # 计算续写数量
    segments_count = len(segments)
    
    # 计算活跃Bot数量
    active_bots_count = db.query(BotBranchMembership).filter(
        BotBranchMembership.branch_id == branch_id
    ).count()
    
    # 计算活跃度得分
    activity_score = (
        vote_score * 0.5 +
        segments_count * 0.3 +
        active_bots_count * 0.2
    )
    
    return round(activity_score, 2)


def get_activity_score_cached(
    db: Session,
    branch_id: uuid.UUID
) -> float:
    """
    获取活跃度得分（带缓存）
    
    Returns:
        活跃度得分
    """
    redis_key = f"branch:{branch_id}:activity_score"
    
    try:
        redis_client = get_redis_connection()
        cached_score = redis_client.get(redis_key)
        
        if cached_score:
            return float(cached_score)
    except Exception as e:
        import logging
        logging.warning(f"获取缓存活跃度得分失败: {e}")
    
    # 缓存未命中，计算并缓存
    score = calculate_activity_score(db, branch_id)
    
    try:
        redis_client = get_redis_connection()
        redis_client.setex(redis_key, 3600, str(score))  # 缓存1小时
    except Exception as e:
        import logging
        logging.warning(f"缓存活跃度得分失败: {e}")
    
    return score


def update_activity_score_cache(
    db: Session,
    branch_id: uuid.UUID
):
    """
    更新活跃度得分缓存
    
    在以下情况调用：
    - 新续写提交时
    - 新投票时
    - Bot加入/离开分支时
    """
    score = calculate_activity_score(db, branch_id)
    
    try:
        redis_client = get_redis_connection()
        redis_key = f"branch:{branch_id}:activity_score"
        redis_client.setex(redis_key, 3600, str(score))  # 缓存1小时
    except Exception as e:
        import logging
        logging.warning(f"更新活跃度得分缓存失败: {e}")


def update_all_branch_activity_scores(db: Session) -> Dict[str, Any]:
    """
    更新所有分支的活跃度得分（定时任务）
    
    Returns:
        包含更新结果的字典
    """
    # 获取所有活跃分支
    active_branches = db.query(Branch).filter(
        Branch.status == 'active'
    ).all()
    
    results = {
        'updated_count': 0,
        'errors': []
    }
    
    for branch in active_branches:
        try:
            update_activity_score_cache(db, branch.id)
            results['updated_count'] += 1
        except Exception as e:
            results['errors'].append({
                'branch_id': str(branch.id),
                'error': str(e)
            })
    
    return results
