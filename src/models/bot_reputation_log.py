"""Bot声誉日志模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class BotReputationLog(Base):
    """Bot声誉日志表"""
    __tablename__ = 'bot_reputation_log'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey('bots.id', ondelete='CASCADE'), nullable=False, index=True)
    change = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    related_type = Column(String, nullable=True)  # 'segment' | 'branch' | 'vote'
    related_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f'<BotReputationLog bot={self.bot_id} change={self.change}>'
