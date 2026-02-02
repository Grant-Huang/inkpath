"""Bot服务"""
import uuid
import secrets
import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from src.models.bot import Bot


def generate_api_key() -> str:
    """生成API Key"""
    # 生成32字节的随机token，转换为URL安全的base64字符串
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """加密API Key"""
    return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_api_key(api_key: str, hashed: str) -> bool:
    """验证API Key"""
    return bcrypt.checkpw(api_key.encode('utf-8'), hashed.encode('utf-8'))


def register_bot(
    db: Session,
    name: str,
    model: str,
    webhook_url: Optional[str] = None,
    language: str = 'zh'
) -> tuple[Bot, str]:
    """
    注册Bot
    
    Returns:
        (Bot对象, API Key)
    """
    # 检查名称是否已存在
    existing_bot = db.query(Bot).filter(Bot.name == name).first()
    if existing_bot:
        raise ValueError(f"Bot名称 '{name}' 已存在")
    
    # 生成API Key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # 创建Bot
    bot = Bot(
        name=name,
        model=model,
        api_key_hash=api_key_hash,
        webhook_url=webhook_url,
        language=language,
        reputation=0,
        status='active'
    )
    
    db.add(bot)
    db.commit()
    db.refresh(bot)
    
    return bot, api_key


def get_bot_by_id(db: Session, bot_id: uuid.UUID) -> Optional[Bot]:
    """根据ID获取Bot"""
    return db.query(Bot).filter(Bot.id == bot_id).first()


def authenticate_bot(db: Session, api_key: str) -> Optional[Bot]:
    """通过API Key认证Bot"""
    # 查询所有Bot
    bots = db.query(Bot).all()
    
    # 验证API Key
    for bot in bots:
        if verify_api_key(api_key, bot.api_key_hash):
            return bot
    
    return None
