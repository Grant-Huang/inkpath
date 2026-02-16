"""API Token 服务"""
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.user import User


# Token 有效期（默认 30 天）
DEFAULT_TOKEN_LIFETIME = timedelta(days=30)


def generate_api_token() -> str:
    """生成 API Token"""
    return secrets.token_urlsafe(32)


def generate_user_api_token(
    db: Session,
    user_id: str,
    lifetime: timedelta = DEFAULT_TOKEN_LIFETIME
) -> tuple[User, str]:
    """
    为用户生成 API Token
    
    Returns:
        (User对象, token字符串)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    
    token = generate_api_token()
    user.api_token = token
    user.api_token_expires_at = datetime.utcnow() + lifetime
    
    db.commit()
    db.refresh(user)
    
    return user, token


def revoke_user_api_token(db: Session, user_id: str) -> bool:
    """撤销用户的 API Token"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    user.api_token = None
    user.api_token_expires_at = None
    
    db.commit()
    return True


def validate_api_token(db: Session, token: str) -> User | None:
    """验证 API Token，返回对应的用户"""
    if not token:
        return None
    
    user = db.query(User).filter(User.api_token == token).first()
    if not user:
        return None
    
    if not user.is_api_token_valid():
        return None
    
    return user


def refresh_user_api_token(
    db: Session,
    user_id: str,
    lifetime: timedelta = DEFAULT_TOKEN_LIFETIME
) -> tuple[User, str]:
    """刷新用户的 API Token（先撤销旧 Token，再生成新的）"""
    revoke_user_api_token(db, user_id)
    return generate_user_api_token(db, user_id, lifetime)


def get_token_info(user: User) -> dict | None:
    """获取 Token 信息"""
    if not user.is_api_token_valid():
        return None
    
    return {
        "token": user.api_token,
        "expires_at": user.api_token_expires_at.isoformat(),
        "remaining_days": (user.api_token_expires_at - datetime.utcnow()).days
    }
