"""重写片段模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class RewriteSegment(Base):
    """重写片段"""
    __tablename__ = 'rewrite_segments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey('segments.id'), nullable=False, index=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey('bots.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系 - 暂时移除
    segment = relationship('Segment', back_populates='rewrites')
    # bot = relationship('Bot')
    votes = relationship('RewriteVote', back_populates='rewrite_segment', cascade='all, delete-orphan')
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'segment_id': str(self.segment_id),
            'bot_id': str(self.bot_id),
            'bot_name': self.bot.name if self.bot else 'Unknown',
            'bot_color': getattr(self.bot, 'color', '#6B5B95') if self.bot else '#6B5B95',
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'vote_score': self.calculate_vote_score(),
        }
    
    def calculate_vote_score(self) -> float:
        """计算投票总分"""
        human_up = sum(1 for v in self.votes if v.vote == 1 and v.is_human)
        human_down = sum(1 for v in self.votes if v.vote == -1 and v.is_human)
        bot_up = sum(1 for v in self.votes if v.vote == 1 and not v.is_human)
        bot_down = sum(1 for v in self.votes if v.vote == -1 and not v.is_human)
        
        return human_up * 1.0 - human_down * 1.0 + bot_up * 0.5 - bot_down * 0.5
