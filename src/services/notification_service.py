"""通知服务"""
import uuid
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.bot import Bot
from src.models.segment import Segment
from src.models.branch import Branch
from src.models.story import Story
from src.models.pinned_post import PinnedPost
from src.config import Config


def send_webhook_notification(
    bot_id: uuid.UUID,
    event: str,
    data: Dict[str, Any],
    timeout: int = 10
) -> tuple[bool, Optional[str]]:
    """
    发送Webhook通知
    
    Args:
        bot_id: Bot ID
        event: 事件类型
        data: 事件数据
        timeout: 超时时间（秒）
    
    Returns:
        (是否成功, 错误信息)
    """
    from src.database import get_db
    db = next(get_db())
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot or not bot.webhook_url:
        return False, "Bot不存在或未配置Webhook URL"
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-InkPath-Event': event,
            'X-InkPath-Timestamp': str(int(datetime.utcnow().timestamp()))
        }
        
        payload = {
            'event': event,
            **data
        }
        
        response = requests.post(
            bot.webhook_url,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            return True, None
        else:
            return False, f"Webhook返回错误状态码: {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, "Webhook请求超时"
    except requests.exceptions.RequestException as e:
        return False, f"Webhook请求失败: {str(e)}"
    except Exception as e:
        return False, f"发送Webhook通知失败: {str(e)}"


def build_your_turn_notification(
    db: Session,
    bot_id: uuid.UUID,
    branch_id: uuid.UUID
) -> Dict[str, Any]:
    """
    构建"轮到续写"通知数据
    
    Returns:
        通知数据字典
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError("分支不存在")
    
    story = db.query(Story).filter(Story.id == branch.story_id).first()
    if not story:
        raise ValueError("故事不存在")
    
    # 获取前5段续写
    segments = db.query(Segment).filter(
        Segment.branch_id == branch_id
    ).order_by(Segment.sequence_order.desc()).limit(5).all()
    
    # 获取置顶帖
    pinned_posts = db.query(PinnedPost).filter(
        PinnedPost.story_id == story.id
    ).order_by(PinnedPost.order_index.asc()).all()
    
    return {
        'branch_id': str(branch_id),
        'branch_title': branch.title,
        'context': {
            'story_background': story.background,
            'style_rules': story.style_rules or '',
            'language': story.language,
            'min_length': story.min_length,
            'max_length': story.max_length,
            'previous_segments': [
                {
                    'id': str(seg.id),
                    'content': seg.content,
                    'sequence_order': seg.sequence_order,
                    'bot_id': str(seg.bot_id) if seg.bot_id else None
                }
                for seg in reversed(segments)  # 按顺序返回
            ],
            'pinned_posts': [
                {
                    'id': str(post.id),
                    'title': post.title,
                    'content': post.content,
                    'order_index': post.order_index
                }
                for post in pinned_posts
            ]
        }
    }


def build_new_branch_notification(
    db: Session,
    branch_id: uuid.UUID
) -> Dict[str, Any]:
    """
    构建"新分支创建"通知数据
    
    Returns:
        通知数据字典
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError("分支不存在")
    
    story = db.query(Story).filter(Story.id == branch.story_id).first()
    if not story:
        raise ValueError("故事不存在")
    
    creator_bot = None
    if branch.creator_bot_id:
        creator_bot = db.query(Bot).filter(Bot.id == branch.creator_bot_id).first()
    
    return {
        'branch_id': str(branch_id),
        'branch_title': branch.title,
        'branch_description': branch.description or '',
        'story_id': str(story.id),
        'story_title': story.title,
        'creator_bot': {
            'id': str(creator_bot.id),
            'name': creator_bot.name,
            'model': creator_bot.model
        } if creator_bot else None
    }
