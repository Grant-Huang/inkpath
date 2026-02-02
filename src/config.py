"""应用配置"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置"""
    # 数据库
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/inkpath')
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))
    
    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Feature Flags
    ENABLE_COHERENCE_CHECK = os.getenv('ENABLE_COHERENCE_CHECK', 'false').lower() == 'true'
    COHERENCE_THRESHOLD = int(os.getenv('COHERENCE_THRESHOLD', 4))
    
    # Server
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
