"""置顶帖服务"""
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from src.models.pinned_post import PinnedPost
from src.models.story import Story


def create_pinned_post(
    db: Session,
    story_id: uuid.UUID,
    title: str,
    content: str,
    pinned_by: uuid.UUID,
    order_index: int = 0
) -> PinnedPost:
    """
    创建置顶帖
    
    Returns:
        PinnedPost对象
    """
    # 验证故事存在
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise ValueError("故事不存在")
    
    # 创建置顶帖
    pinned_post = PinnedPost(
        story_id=story_id,
        title=title,
        content=content,
        pinned_by=pinned_by,
        order_index=order_index
    )
    
    db.add(pinned_post)
    db.commit()
    db.refresh(pinned_post)
    
    return pinned_post


def get_pinned_posts_by_story(
    db: Session,
    story_id: uuid.UUID
) -> list[PinnedPost]:
    """获取故事的所有置顶帖（按更新时间排序）"""
    return db.query(PinnedPost).filter(
        PinnedPost.story_id == story_id
    ).order_by(PinnedPost.updated_at.desc()).all()


def get_pinned_post_by_id(
    db: Session,
    pinned_post_id: uuid.UUID
) -> Optional[PinnedPost]:
    """根据ID获取置顶帖"""
    return db.query(PinnedPost).filter(PinnedPost.id == pinned_post_id).first()


def update_pinned_post(
    db: Session,
    pinned_post_id: uuid.UUID,
    title: Optional[str] = None,
    content: Optional[str] = None,
    order_index: Optional[int] = None
) -> Optional[PinnedPost]:
    """更新置顶帖"""
    pinned_post = get_pinned_post_by_id(db, pinned_post_id)
    
    if not pinned_post:
        return None
    
    if title is not None:
        pinned_post.title = title
    if content is not None:
        pinned_post.content = content
    if order_index is not None:
        pinned_post.order_index = order_index
    
    db.commit()
    db.refresh(pinned_post)
    
    return pinned_post
