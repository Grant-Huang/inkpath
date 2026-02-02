"""故事模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.database import Base


class Story(Base):
    """故事表"""
    __tablename__ = 'stories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    background = Column(Text, nullable=False)
    style_rules = Column(Text, nullable=True)
    language = Column(String, nullable=False, default='zh')  # 'zh' | 'en'，故事语言
    min_length = Column(Integer, default=150)  # 最小续写长度（字/单词）
    max_length = Column(Integer, default=500)  # 最大续写长度（字/单词）
    story_pack_json = Column(JSONB, nullable=True)  # 故事包内容（MD文件解析后的JSON）
    owner_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # 可为NULL（Bot创建时）
    owner_type = Column(String, nullable=False)  # 'human' | 'bot'
    status = Column(String, default='active', index=True)  # 'active' | 'archived'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Story {self.title}>'
