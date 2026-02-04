"""续写段模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class Segment(Base):
    """续写段表"""
    __tablename__ = 'segments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id = Column(UUID(as_uuid=True), ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey('bots.id', ondelete='SET NULL'), nullable=True, index=True)
    parent_segment = Column(UUID(as_uuid=True), ForeignKey('segments.id', ondelete='SET NULL'), nullable=True)
    content = Column(Text, nullable=False)
    sequence_order = Column(Integer, nullable=False)
    coherence_score = Column(Numeric(3, 1), nullable=True)  # 连续性评分 (1-10)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    branch = relationship('Branch', foreign_keys=[branch_id], backref='segments')
    bot = relationship('Bot', backref='segments')
    rewrites = relationship('RewriteSegment', back_populates='segment', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Segment {self.sequence_order} in branch {self.branch_id}>'
