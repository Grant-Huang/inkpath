"""人类分支参与模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class HumanBranchMembership(Base):
    """人类分支参与表"""
    __tablename__ = 'human_branch_membership'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey('branches.id', ondelete='CASCADE'), primary_key=True, index=True)
    role = Column(String, nullable=True)  # 'narrator' | 'challenger' | 'voice' | NULL（可选，参与者身份）
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    user = relationship('User', backref='branch_memberships')
    branch = relationship('Branch', backref='human_members')

    def __repr__(self):
        return f'<HumanBranchMembership user={self.user_id} branch={self.branch_id}>'
