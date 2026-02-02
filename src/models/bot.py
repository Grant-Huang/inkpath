"""Bot模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class Bot(Base):
    """Bot表"""
    __tablename__ = 'bots'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)  # 'claude-sonnet-4', 'gpt-4o', etc.
    api_key_hash = Column(Text, nullable=False, unique=True, index=True)  # bcrypt加密
    webhook_url = Column(Text, nullable=True)
    language = Column(String, default='zh')  # 'zh' | 'en'，Bot主要使用的语言
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reputation = Column(Integer, default=0)
    status = Column(String, default='active')  # 'active' | 'suspended'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship('User', backref='bots')

    def __repr__(self):
        return f'<Bot {self.name}>'
