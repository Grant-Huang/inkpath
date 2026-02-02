"""置顶帖模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class PinnedPost(Base):
    """置顶帖表"""
    __tablename__ = 'pinned_posts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey('stories.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    pinned_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    order_index = Column(Integer, default=0)  # 排序字段
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    story = relationship('Story', backref='pinned_posts')
    user = relationship('User', backref='pinned_posts')

    def __repr__(self):
        return f'<PinnedPost {self.title}>'
