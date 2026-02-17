"""分支模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class Branch(Base):
    """分支表"""
    __tablename__ = 'branches'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey('stories.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_branch = Column(UUID(as_uuid=True), ForeignKey('branches.id', ondelete='SET NULL'), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # creator_bot_id 保留但不使用（避免循环依赖）
    creator_bot_id = Column(UUID(as_uuid=True), nullable=True)
    fork_at_segment_id = Column(UUID(as_uuid=True), ForeignKey('segments.id', ondelete='SET NULL'), nullable=True)
    status = Column(String, default='active', index=True)  # 'active' | 'archived' | 'merged'
    current_summary = Column(Text, nullable=True)
    summary_updated_at = Column(DateTime(timezone=True), nullable=True)
    summary_covers_up_to = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    story = relationship('Story', backref='branches')
    # creator_bot - removed to avoid circular dependency
    # fork_at_segment关系需要明确指定
    fork_at_segment = relationship('Segment', foreign_keys=[fork_at_segment_id], post_update=True)

    def __repr__(self):
        return f'<Branch {self.title}>'
