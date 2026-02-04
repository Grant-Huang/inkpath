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
    
    # Anthropic API (Claude)
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # MiniMax API (LLM摘要生成)
    MINIMAX_API_KEY = os.getenv('MINIMAX_API_KEY', '')
    MINIMAX_BASE_URL = os.getenv('MINIMAX_BASE_URL', 'https://api.minimax.chat/v1')
    MINIMAX_MODEL = os.getenv('MINIMAX_MODEL', 'abab6.5s-chat')
    
    # Google Gemini API (LLM摘要生成)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
    
    # LLM Provider 选择: 'minimax' 或 'gemini'
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')
    
    # 摘要生成配置
    SUMMARY_TRIGGER_COUNT = int(os.getenv('SUMMARY_TRIGGER_COUNT', 5))  # 每N个续写后生成摘要
    SUMMARY_MAX_SEGMENTS = int(os.getenv('SUMMARY_MAX_SEGMENTS', 20))  # 生成摘要时最多包含的段数
    
    # Feature Flags
    ENABLE_COHERENCE_CHECK = False  # 禁用，避免超时
    COHERENCE_THRESHOLD = int(os.getenv('COHERENCE_THRESHOLD', 4))
    ENABLE_SUMMARY_AUTO = False  # 禁用自动摘要，避免超时
    
    # Server
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
