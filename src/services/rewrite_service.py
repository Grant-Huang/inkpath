"""重写服务"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.rewrite_segment import RewriteSegment
from src.models.rewrite_vote import RewriteVote
from src.models.segment import Segment
from src.models.bot import Bot
from src.models.user import User


def create_rewrite(
    db: Session,
    segment_id: uuid.UUID,
    bot_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    content: str = ""
) -> RewriteSegment:
    """创建重写片段
    
    注意：当前模型只支持 bot_id，如果提供了 user_id，需要查找或创建对应的 Bot
    """
    # 如果提供了 user_id 但没有 bot_id，需要查找或创建对应的 Bot
    if user_id and not bot_id:
        # 查找是否存在"人类用户"类型的 Bot，或者为每个用户创建对应的 Bot
        # 临时方案：查找名为 "Human User" 的 Bot，如果不存在则创建
        human_bot = db.query(Bot).filter(Bot.name == "Human User").first()
        if not human_bot:
            # 创建一个通用的"人类用户" Bot
            human_bot = Bot(
                name="Human User",
                description="人类用户重写",
                color="#6B5B95",
                status="active"
            )
            db.add(human_bot)
            db.commit()
            db.refresh(human_bot)
        bot_id = human_bot.id
    
    if not bot_id:
        raise ValueError("必须提供 bot_id 或 user_id")
    
    rewrite = RewriteSegment(
        segment_id=segment_id,
        bot_id=bot_id,
        content=content,
    )
    db.add(rewrite)
    db.commit()
    db.refresh(rewrite)
    return rewrite


def get_rewrites_by_segment(
    db: Session,
    segment_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[RewriteSegment], int]:
    """获取片段的所有重写"""
    # 计算总数
    total = db.query(func.count(RewriteSegment.id)).filter(
        RewriteSegment.segment_id == segment_id
    ).scalar()
    
    # 获取重写（按评分降序）
    rewrites = db.query(RewriteSegment).filter(
        RewriteSegment.segment_id == segment_id
    ).order_by(
        RewriteSegment.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return rewrites, total


def get_top_rewrite(
    db: Session,
    segment_id: uuid.UUID
) -> Optional[RewriteSegment]:
    """获取评分最高的重写"""
    # 临时方案：返回最新的（等投票功能上线后再改）
    return db.query(RewriteSegment).filter(
        RewriteSegment.segment_id == segment_id
    ).order_by(RewriteSegment.created_at.desc()).first()


def get_rewrite_with_votes(
    db: Session,
    rewrite_id: uuid.UUID
) -> Optional[RewriteSegment]:
    """获取重写及投票统计"""
    return db.query(RewriteSegment).filter(
        RewriteSegment.id == rewrite_id
    ).first()


def vote_rewrite(
    db: Session,
    rewrite_id: uuid.UUID,
    bot_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    vote_value: int = 1
) -> Tuple[Optional[RewriteVote], str]:
    """
    为重写投票
    
    Returns:
        (投票记录, 消息)
    """
    # 验证重写存在
    rewrite = db.query(RewriteSegment).filter(
        RewriteSegment.id == rewrite_id
    ).first()
    if not rewrite:
        return None, "重写不存在"
    
    # 检查是否已投票
    existing = None
    if bot_id:
        existing = db.query(RewriteVote).filter(
            RewriteVote.rewrite_id == rewrite_id,
            RewriteVote.bot_id == bot_id
        ).first()
    elif user_id:
        existing = db.query(RewriteVote).filter(
            RewriteVote.rewrite_id == rewrite_id,
            RewriteVote.user_id == user_id
        ).first()
    
    if existing:
        if existing.vote == vote_value:
            # 取消投票
            db.delete(existing)
            db.commit()
            return None, "投票已取消"
        else:
            # 更改投票
            existing.vote = vote_value
            db.commit()
            return existing, "投票已更改"
    
    # 创建新投票
    vote = RewriteVote(
        rewrite_id=rewrite_id,
        bot_id=bot_id,
        user_id=user_id,
        vote=vote_value,
    )
    db.add(vote)
    db.commit()
    db.refresh(vote)
    return vote, "投票成功"


def get_rewrite_vote_summary(
    db: Session,
    rewrite_id: uuid.UUID
) -> dict:
    """获取重写投票统计"""
    votes = db.query(RewriteVote).filter(
        RewriteVote.rewrite_id == rewrite_id
    ).all()
    
    human_up = sum(1 for v in votes if v.vote == 1 and v.is_human)
    human_down = sum(1 for v in votes if v.vote == -1 and v.is_human)
    bot_up = sum(1 for v in votes if v.vote == 1 and not v.is_human)
    bot_down = sum(1 for v in votes if v.vote == -1 and not v.is_human)
    
    total_score = human_up * 1.0 - human_down * 1.0 + bot_up * 0.5 - bot_down * 0.5
    
    return {
        'human_up': human_up,
        'human_down': human_down,
        'bot_up': bot_up,
        'bot_down': bot_down,
        'total_score': round(total_score, 2),
    }
