"""Agent 模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text
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
    model = Column(String, nullable=False, default='claude-sonnet-4')  # 'claude-sonnet-4', 'gpt-4o', etc.
    webhook_url = Column(Text, nullable=True)
    language = Column(String, default='zh')  # 'zh' | 'en'，Agent主要使用的语言
    reputation = Column(Integer, default=0)
    status = Column(String, default='active', index=True)  # 'active' | 'suspended' | 'idle' | 'running' | 'error'
    config = Column(Text, nullable=True)  # JSON 配置
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship('User', backref='agents')

    def __repr__(self):
        return f'<Agent {self.name}>'


class AgentStory(Base):
    """Agent-Story 关联表
    
    记录 Agent 分配了哪些故事
    """
    __tablename__ = 'agent_stories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    story_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    auto_continue = Column(Boolean, default=True)  # 是否自动续写
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        {'schema': None},
    )

    def __repr__(self):
        return f'<AgentStory {self.agent_id} -> {self.story_id}>'


class AgentProgress(Base):
    """Agent 故事进度表
    
    记录 Agent 对每个故事的进度追踪
    """
    __tablename__ = 'agent_progress'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    story_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    summary = Column(Text, nullable=True)  # 故事进展摘要
    next_action = Column(Text, nullable=True)  # 下一步计划
    last_action = Column(String, nullable=True)  # 最后操作类型
    segments_count = Column(Integer, default=0)  # 片段数量
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        {'schema': None},
    )

    def __repr__(self):
        return f'<AgentProgress {self.agent_id} -> {self.story_id}>'
