"""Bot分支参与模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class BotBranchMembership(Base):
    """Bot分支参与表"""
    __tablename__ = 'bot_branch_membership'

    bot_id = Column(UUID(as_uuid=True), ForeignKey('bots.id', ondelete='CASCADE'), primary_key=True, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey('branches.id', ondelete='CASCADE'), primary_key=True, index=True)
    join_order = Column(Integer, nullable=False)  # 加入顺序，用于轮次队列
    role = Column(String, nullable=True)  # 'narrator' | 'challenger' | 'voice' | NULL（可选，参与者身份）
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f'<BotBranchMembership bot={self.bot_id} branch={self.branch_id}>'
