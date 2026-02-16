"""Agent 模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class Agent(Base):
    """Agent 表
    
    存储 Agent 账号信息
    """
    __tablename__ = 'agents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    api_key_hash = Column(Text, nullable=False, unique=True, index=True)
    status = Column(String, default='idle', index=True)  # 'idle' | 'running' | 'error'
    config = Column(Text, nullable=True)  # JSON 配置
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship('User', backref='agents')
    stories = relationship('AgentStory', back_populates='agent', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Agent {self.name}>'


class AgentStory(Base):
    """Agent-Story 关联表
    
    记录 Agent 分配了哪些故事
    """
    __tablename__ = 'agent_stories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 不使用外键约束，避免迁移问题
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    story_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    auto_continue = Column(Boolean, default=True)  # 是否自动续写
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 唯一约束
    __table_args__ = (
        {'schema': None},
    )

    # 关系
    agent = relationship('Agent', back_populates='stories')

    def __repr__(self):
        return f'<AgentStory {self.agent_id} -> {self.story_id}>'


class AgentProgress(Base):
    """Agent 故事进度表
    
    记录 Agent 对每个故事的进度追踪
    """
    __tablename__ = 'agent_progress'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 不使用外键约束
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    story_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    summary = Column(Text, nullable=True)  # 故事进展摘要
    next_action = Column(Text, nullable=True)  # 下一步计划
    last_action = Column(String, nullable=True)  # 最后操作类型
    segments_count = Column(Integer, default=0)  # 片段数量
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 唯一约束
    __table_args__ = (
        {'schema': None},
    )

    def __repr__(self):
        return f'<AgentProgress {self.agent_id} -> {self.story_id}>'
