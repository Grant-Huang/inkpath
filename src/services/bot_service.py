"""Bot服务"""
import uuid
import secrets
import bcrypt
import logging
from typing import Optional
from sqlalchemy.orm import Session
from src.models.bot import Bot

logger = logging.getLogger(__name__)


def generate_api_key() -> str:
    """生成API Key"""
    # 生成32字节的随机token，转换为URL安全的base64字符串
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """加密API Key - 使用SHA256"""
    import hashlib
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()


def verify_api_key(api_key: str, hashed: str) -> bool:
    """验证API Key - 支持 SHA256 和 bcrypt"""
    import hashlib
    import logging
    logger = logging.getLogger(__name__)
    
    if not api_key or not hashed:
        logger.warning(f"API key 或 hashed 为空: key={bool(api_key)}, hash={bool(hashed)}")
        return False
    
    # 先尝试 SHA256（新增的Bot）
    try:
        hashed_key = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
        if hashed_key == hashed:
            logger.info(f"SHA256验证成功")
            return True
    except Exception as e:
        logger.warning(f"SHA256验证失败: {e}")
    
    # 尝试 bcrypt（旧 Bot 兼容）
    try:
        if hashed.startswith('$2'):
            import bcrypt
            if bcrypt.checkpw(api_key.encode('utf-8'), hashed.encode('utf-8')):
                logger.info(f"bcrypt验证成功")
                return True
    except Exception as e:
        logger.warning(f"bcrypt验证失败: {e}")
    
    logger.info(f"验证失败: 不匹配")
    return False


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


def get_bot_by_name(db: Session, bot_name: str) -> Optional[Bot]:
    """根据名称获取Bot"""
    return db.query(Bot).filter(Bot.name == bot_name).first()


def authenticate_bot(db: Session, api_key: str) -> Optional[Bot]:
    """通过API Key认证Bot"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 查询所有活跃或空闲的Bot
        bots = db.query(Bot).filter(Bot.status.in_(['active', 'idle'])).limit(10).all()
        logger.info(f"找到 {len(bots)} 个Bot")
        
        # 验证API Key
        for bot in bots:
            logger.info(f"尝试验证 Bot: {bot.name}, hash: {bot.api_key_hash[:20]}...")
            if verify_api_key(api_key, bot.api_key_hash):
                logger.info(f"Bot验证成功: {bot.name}")
                return bot
            logger.info(f"Bot验证失败: {bot.name}")
    except Exception as e:
        logger.error(f"Bot认证失败: {e}")
    
    return None
