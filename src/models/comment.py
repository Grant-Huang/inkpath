"""评论模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class Comment(Base):
    """评论表"""
    __tablename__ = 'comments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id = Column(UUID(as_uuid=True), ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    author_type = Column(String, nullable=False)  # 'bot' | 'human'
    author_id = Column(UUID(as_uuid=True), nullable=False)
    parent_comment = Column(UUID(as_uuid=True), ForeignKey('comments.id', ondelete='CASCADE'), nullable=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    branch = relationship('Branch', backref='comments')
    parent = relationship('Comment', remote_side=[id], backref='replies')

    def __repr__(self):
        return f'<Comment on branch {self.branch_id}>'
