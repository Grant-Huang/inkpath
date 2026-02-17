"""重写投票模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class RewriteVote(Base):
    """重写投票"""
    __tablename__ = 'rewrite_votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rewrite_id = Column(UUID(as_uuid=True), ForeignKey('rewrite_segments.id'), nullable=False, index=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    vote = Column(Integer, nullable=False)  # 1 或 -1
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    rewrite_segment = relationship('RewriteSegment', back_populates='votes')
    
    @property
    def is_human(self) -> bool:
        return self.user_id is not None
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'rewrite_id': str(self.rewrite_id),
            'bot_id': str(self.bot_id) if self.bot_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'vote': self.vote,
            'is_human': self.is_human,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
