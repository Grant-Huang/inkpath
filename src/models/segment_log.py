"""续写日志模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.database import Base


class SegmentLog(Base):
    """片段创作日志"""
    __tablename__ = 'segment_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    segment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # 可为 NULL（Bot 匿名时）
    author_type = Column(String, nullable=False)  # 'human' | 'bot'
    author_name = Column(String, nullable=False)
    content_length = Column(Integer, nullable=False)
    is_continuation = Column(String, nullable=False)  # 'new' | 'continuation' | 'fork'
    parent_segment_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<SegmentLog {self.id} {self.author_type}:{self.author_name}>'
