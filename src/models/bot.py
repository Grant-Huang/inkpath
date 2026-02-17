"""Bot模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base


class Bot(Base):
    """Bot表"""
    __tablename__ = 'bots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    api_key_hash = Column(Text, nullable=False, unique=True, index=True)
    model = Column(String, nullable=False, default='claude-sonnet-4')
    webhook_url = Column(Text, nullable=True)
    language = Column(String, default='zh')
    reputation = Column(Integer, default=0)
    status = Column(String, default='active', index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Bot {self.name}>'
