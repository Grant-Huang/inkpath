"""Bot 服务（Agent 与 Bot 统一：非人类写作者仅使用 Bot 模型/表 bots）"""
import uuid
import secrets
import bcrypt
import logging
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _get_bot_model():
    """统一使用 Bot 模型（表 bots）。Agent 与 Bot 为同一概念：非人类写作者。"""
    from src.models.bot import Bot
    return Bot


def generate_api_key() -> str:
    """生成API Key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """加密API Key - 使用SHA256"""
    import hashlib
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()


def verify_api_key(api_key: str, hashed: str) -> bool:
    """验证API Key - 支持 SHA256 和 bcrypt"""
    import hashlib
    
    if not api_key or not hashed:
        logger.warning(f"API key 或 hashed 为空")
        return False
    
    # 先尝试 SHA256
    try:
        hashed_key = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
        if hashed_key == hashed:
            return True
    except Exception as e:
        logger.warning(f"SHA256验证失败: {e}")
    
    # 尝试 bcrypt（旧 Bot 兼容）
    try:
        if hashed.startswith('$2'):
            if bcrypt.checkpw(api_key.encode('utf-8'), hashed.encode('utf-8')):
                return True
    except Exception as e:
        logger.warning(f"bcrypt验证失败: {e}")
    
    return False


def register_bot(db: Session, name: str, model: str, webhook_url: Optional[str] = None, language: str = 'zh'):
    """注册Bot"""
    Bot = _get_bot_model()
    
    # 检查名称是否已存在
    existing = db.query(Bot).filter(Bot.name == name).first()
    if existing:
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


def get_bot_by_id(db: Session, bot_id: uuid.UUID):
    """根据ID获取Bot"""
    Bot = _get_bot_model()
    return db.query(Bot).filter(Bot.id == bot_id).first()


def get_bot_by_name(db: Session, bot_name: str):
    """根据名称获取Bot"""
    Bot = _get_bot_model()
    return db.query(Bot).filter(Bot.name == bot_name).first()


def authenticate_bot(db: Session, api_key: str):
    """通过API Key认证Bot"""
    Bot = _get_bot_model()
    
    try:
        bots = db.query(Bot).filter(Bot.status == 'active').all()
        
        for bot in bots:
            if verify_api_key(api_key, bot.api_key_hash):
                return bot
    except Exception as e:
        logger.error(f"Bot认证失败: {e}")
    
    return None
