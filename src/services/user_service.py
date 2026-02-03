"""用户服务"""
import uuid
import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from src.models.user import User


def hash_password(password: str) -> str:
    """加密密码"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def register_user(
    db: Session,
    email: str,
    name: str,
    password: str,
    auth_provider: str = 'email'
) -> User:
    """
    注册用户
    
    Returns:
        User对象
    """
    # 检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError(f"邮箱 '{email}' 已被注册")
    
    # 加密密码
    password_hash = hash_password(password)
    
    # 创建用户
    user = User(
        email=email,
        name=name,
        password_hash=password_hash,
        auth_provider=auth_provider
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """通过邮箱和密码认证用户"""
    user = get_user_by_email(db, email)
    
    if not user or not user.password_hash:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def update_user_profile(
    db: Session,
    user_id: uuid.UUID,
    name: Optional[str] = None,
    bio: Optional[str] = None,
    avatar_url: Optional[str] = None
) -> User:
    """
    更新用户资料
    
    Returns:
        更新后的User对象
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("用户不存在")
    
    if name is not None:
        user.name = name
    if bio is not None:
        user.bio = bio
    if avatar_url is not None:
        user.avatar_url = avatar_url
    
    db.commit()
    db.refresh(user)
    
    return user


def update_user_password(
    db: Session,
    user_id: uuid.UUID,
    old_password: str,
    new_password: str
) -> bool:
    """
    更新用户密码
    
    Returns:
        是否成功
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError("用户不存在")
    
    if user.password_hash and not verify_password(old_password, user.password_hash):
        return False
    
    user.password_hash = hash_password(new_password)
    db.commit()
    
    return True
