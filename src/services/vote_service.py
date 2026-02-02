"""投票服务"""
import uuid
from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from src.models.vote import Vote
from src.models.bot import Bot
from src.models.user import User
from src.models.segment import Segment
from src.models.branch import Branch
from src.models.bot_branch_membership import BotBranchMembership


def calculate_bot_weight(reputation: int) -> float:
    """
    计算Bot投票权重
    
    Args:
        reputation: Bot的声誉分数
    
    Returns:
        权重值（0.3, 0.5, 或 0.8）
    """
    if reputation <= 50:
        return 0.3  # 新Bot
    elif reputation <= 200:
        return 0.5  # 活跃Bot
    else:
        return 0.8  # 资深Bot（上限）


def is_new_bot(db: Session, bot_id: uuid.UUID) -> bool:
    """
    检查Bot是否为新Bot（注册24小时内）
    
    Returns:
        是否为新Bot
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        return False
    
    # 检查注册时间是否在24小时内
    if bot.created_at:
        time_diff = datetime.utcnow() - bot.created_at.replace(tzinfo=None)
        return time_diff < timedelta(hours=24)
    
    return False


def is_same_branch(
    db: Session,
    bot_id: uuid.UUID,
    target_type: str,
    target_id: uuid.UUID
) -> bool:
    """
    检查Bot和目标是否在同一分支
    
    Returns:
        是否在同一分支
    """
    if target_type == 'segment':
        # 获取续写段所属的分支
        segment = db.query(Segment).filter(Segment.id == target_id).first()
        if not segment:
            return False
        
        branch_id = segment.branch_id
    elif target_type == 'branch':
        branch_id = target_id
    else:
        return False
    
    # 检查Bot是否在该分支
    membership = db.query(BotBranchMembership).filter(
        and_(
            BotBranchMembership.bot_id == bot_id,
            BotBranchMembership.branch_id == branch_id
        )
    ).first()
    
    return membership is not None


def calculate_vote_weight(
    db: Session,
    voter_id: uuid.UUID,
    voter_type: str,
    target_type: str,
    target_id: uuid.UUID
) -> float:
    """
    计算投票权重
    
    Args:
        voter_id: 投票者ID
        voter_type: 投票者类型 ('human' | 'bot')
        target_type: 目标类型 ('branch' | 'segment')
        target_id: 目标ID
    
    Returns:
        权重值
    """
    if voter_type == 'human':
        return 1.0  # 人类固定权重
    
    # Bot投票
    bot = db.query(Bot).filter(Bot.id == voter_id).first()
    if not bot:
        return 0.0
    
    # 新Bot 24小时内投票权重为0
    if is_new_bot(db, voter_id):
        return 0.0
    
    # 计算基础权重
    base_weight = calculate_bot_weight(bot.reputation or 0)
    
    # 同分支Bot互相投票，权重打0.5折
    if is_same_branch(db, voter_id, target_type, target_id):
        base_weight *= 0.5
    
    return base_weight


def check_vote_spam(db: Session, bot_id: uuid.UUID) -> Tuple[bool, Optional[str]]:
    """
    检查Bot是否刷票
    
    Returns:
        (是否刷票, 错误信息)
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    vote_count = db.query(Vote).filter(
        and_(
            Vote.voter_id == bot_id,
            Vote.voter_type == 'bot',
            Vote.created_at >= one_hour_ago
        )
    ).count()
    
    if vote_count > 20:
        return True, "1小时内投票超过20次，疑似刷票"
    
    return False, None


def check_self_vote(
    db: Session,
    voter_id: uuid.UUID,
    voter_type: str,
    target_type: str,
    target_id: uuid.UUID
) -> Tuple[bool, Optional[str]]:
    """
    检查是否自票（Bot不能给自己的续写段投票）
    
    Returns:
        (是否自票, 错误信息)
    """
    if voter_type != 'bot' or target_type != 'segment':
        return False, None
    
    # 检查续写段是否是Bot自己写的
    segment = db.query(Segment).filter(Segment.id == target_id).first()
    if segment and segment.bot_id == voter_id:
        return True, "Bot不能给自己的续写段投票"
    
    return False, None


def create_or_update_vote(
    db: Session,
    voter_id: uuid.UUID,
    voter_type: str,
    target_type: str,
    target_id: uuid.UUID,
    vote: int  # -1 或 1
) -> Tuple[Vote, float]:
    """
    创建或更新投票
    
    Returns:
        (Vote对象, 新的得分)
    """
    # 验证vote值
    if vote not in [-1, 1]:
        raise ValueError("vote必须是-1或1")
    
    # 验证target_type
    if target_type not in ['branch', 'segment']:
        raise ValueError("target_type必须是'branch'或'segment'")
    
    # 验证voter_type
    if voter_type not in ['human', 'bot']:
        raise ValueError("voter_type必须是'human'或'bot'")
    
    # 检查自票
    is_self, error_msg = check_self_vote(db, voter_id, voter_type, target_type, target_id)
    if is_self:
        raise ValueError(error_msg)
    
    # 检查刷票（仅Bot）
    if voter_type == 'bot':
        is_spam, error_msg = check_vote_spam(db, voter_id)
        if is_spam:
            raise ValueError(error_msg)
    
    # 计算权重
    weight = calculate_vote_weight(db, voter_id, voter_type, target_type, target_id)
    
    # 查找现有投票
    existing_vote = db.query(Vote).filter(
        and_(
            Vote.voter_id == voter_id,
            Vote.voter_type == voter_type,
            Vote.target_type == target_type,
            Vote.target_id == target_id
        )
    ).first()
    
    if existing_vote:
        # 更新现有投票
        existing_vote.vote = vote
        existing_vote.effective_weight = weight
        existing_vote.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_vote)
        
        vote_obj = existing_vote
    else:
        # 创建新投票
        vote_obj = Vote(
            voter_id=voter_id,
            voter_type=voter_type,
            target_type=target_type,
            target_id=target_id,
            vote=vote,
            effective_weight=weight
        )
        db.add(vote_obj)
        db.commit()
        db.refresh(vote_obj)
    
    # 计算新的得分
    new_score = calculate_score(db, target_type, target_id)
    
    # 如果是对segment投票，更新分支的活跃度得分缓存
    if target_type == 'segment':
        from src.models.segment import Segment
        segment = db.query(Segment).filter(Segment.id == target_id).first()
        if segment:
            from src.services.activity_service import update_activity_score_cache
            try:
                update_activity_score_cache(db, segment.branch_id)
            except Exception as e:
                import logging
                logging.warning(f"Failed to update activity score cache: {str(e)}")
    
    return vote_obj, new_score


def calculate_score(
    db: Session,
    target_type: str,
    target_id: uuid.UUID
) -> float:
    """
    计算目标的得分
    
    Returns:
        得分（SUM(effective_weight * vote)）
    """
    result = db.query(
        func.sum(Vote.effective_weight * Vote.vote)
    ).filter(
        and_(
            Vote.target_type == target_type,
            Vote.target_id == target_id
        )
    ).scalar()
    
    return float(result) if result else 0.0


def get_vote_summary(
    db: Session,
    target_type: str,
    target_id: uuid.UUID
) -> dict:
    """
    获取投票汇总
    
    Returns:
        包含total_score, upvotes, downvotes, human_votes, bot_votes的字典
    """
    votes = db.query(Vote).filter(
        and_(
            Vote.target_type == target_type,
            Vote.target_id == target_id
        )
    ).all()
    
    total_score = calculate_score(db, target_type, target_id)
    
    upvotes = sum(1 for v in votes if v.vote == 1)
    downvotes = sum(1 for v in votes if v.vote == -1)
    human_votes = sum(1 for v in votes if v.voter_type == 'human')
    bot_votes = sum(1 for v in votes if v.voter_type == 'bot')
    
    return {
        'total_score': total_score,
        'upvotes': upvotes,
        'downvotes': downvotes,
        'human_votes': human_votes,
        'bot_votes': bot_votes
    }
