"""用户模型"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(Text, nullable=True)  # 可选，支持OAuth时可为NULL
    auth_provider = Column(String, default='email')  # 'email' | 'google' | 'github'
    avatar_url = Column(Text, nullable=True)
    
    # API Token (简单认证，支持外部 Agent)
    api_token = Column(String, unique=True, nullable=True, index=True)
    api_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_api_token_valid(self) -> bool:
        """检查 API Token 是否有效"""
        if not self.api_token or not self.api_token_expires_at:
            return False
        return datetime.utcnow() < self.api_token_expires_at

    def __repr__(self):
        return f'<User {self.email}>'
