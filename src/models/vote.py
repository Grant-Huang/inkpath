"""投票模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base


class Vote(Base):
    """投票表"""
    __tablename__ = 'votes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voter_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    voter_type = Column(String, nullable=False, index=True)  # 'human' | 'bot'
    target_type = Column(String, nullable=False, index=True)  # 'branch' | 'segment'
    target_id = Column(UUID(as_uuid=True), nullable=False)
    vote = Column(Integer, nullable=False)  # -1 或 1
    effective_weight = Column(Numeric(4, 2), nullable=False)  # 存储计算后的权重
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 约束
    __table_args__ = (
        CheckConstraint('vote IN (-1, 1)', name='check_vote_value'),
        UniqueConstraint('voter_id', 'voter_type', 'target_type', 'target_id', name='uq_vote'),
    )

    def __repr__(self):
        return f'<Vote {self.vote} on {self.target_type} {self.target_id}>'
