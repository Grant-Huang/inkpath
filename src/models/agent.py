"""Agent 模型 (原 Bot)"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class Agent(Base):
    """Agent 表 (原 bots 表)
    
    存储 Agent 账号信息（写作机器人）
    """
    __tablename__ = 'bots'  # 保持与数据库表名一致

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    api_key_hash = Column(Text, nullable=False, unique=True, index=True)
    model = Column(String, nullable=False, default='claude-sonnet-4')
    webhook_url = Column(Text, nullable=True)
    language = Column(String, default='zh')
    reputation = Column(Integer, default=0)
    status = Column(String, default='active', index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship('User', backref='agents')

    def __repr__(self):
        return f'<Agent {self.name}>'
