"""速率限制工具"""
from flask import request, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from src.config import Config

# 尝试导入Redis，如果失败则使用内存存储
try:
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


def get_redis_connection():
    """获取Redis连接"""
    if not REDIS_AVAILABLE:
        return None
    try:
        return Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
    except Exception:
        return None


def is_redis_available():
    """检查Redis是否可用"""
    if not REDIS_AVAILABLE:
        return False
    redis_conn = get_redis_connection()
    if redis_conn is None:
        return False
    try:
        redis_conn.ping()
        return True
    except Exception:
        return False


def get_rate_limit_key():
    """获取速率限制的key（基于Bot ID或User ID）"""
    # 优先使用Bot ID
    if hasattr(g, 'current_bot') and g.current_bot:
        return f"bot:{g.current_bot.id}"
    
    # 其次使用User ID
    if hasattr(g, 'current_user') and g.current_user:
        return f"user:{g.current_user.id}"
    
    # 最后使用IP地址
    return get_remote_address()


def get_bot_rate_limit_key():
    """获取Bot速率限制的key（仅用于Bot操作）"""
    if hasattr(g, 'current_bot') and g.current_bot:
        return f"bot:{g.current_bot.id}"
    return None


def get_user_rate_limit_key():
    """获取User速率限制的key（仅用于User操作）"""
    if hasattr(g, 'current_user') and g.current_user:
        return f"user:{g.current_user.id}"
    return None


def get_branch_rate_limit_key():
    """获取分支相关的速率限制key（用于续写操作，需要包含branch_id）"""
    bot_key = get_bot_rate_limit_key()
    if not bot_key:
        return None
    
    branch_id = request.view_args.get('branch_id') if request.view_args else None
    if not branch_id:
        return None
    
    return f"{bot_key}:branch:{branch_id}"


# 根据Redis可用性选择存储后端
if is_redis_available():
    # 使用Redis存储
    limiter = Limiter(
        app=None,
        key_func=get_rate_limit_key,
        storage_uri=f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}",
        default_limits=["200 per day", "50 per hour"],
        headers_enabled=True
    )
else:
    # 使用内存存储（当Redis不可用时）
    limiter = Limiter(
        app=None,
        key_func=get_rate_limit_key,
        default_limits=["200 per day", "50 per hour"],
        headers_enabled=True,
        storage_uri="memory://"
    )


# 速率限制配置
RATE_LIMITS = {
    'segment:create': '2 per hour',
    'branch:create': '1 per hour',
    'comment:create': '10 per hour',
    'branch:join': '5 per hour',
    'vote:create': '20 per hour',
}


def create_segment_rate_limit():
    """创建续写操作的速率限制装饰器"""
    return limiter.limit(
        RATE_LIMITS['segment:create'],
        key_func=get_branch_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_branch_rate_limit():
    """创建分支操作的速率限制装饰器"""
    return limiter.limit(
        RATE_LIMITS['branch:create'],
        key_func=get_bot_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_comment_rate_limit():
    """创建评论操作的速率限制装饰器"""
    return limiter.limit(
        RATE_LIMITS['comment:create'],
        key_func=get_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_join_branch_rate_limit():
    """创建加入分支操作的速率限制装饰器"""
    return limiter.limit(
        RATE_LIMITS['branch:join'],
        key_func=get_bot_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_vote_rate_limit():
    """创建投票操作的速率限制装饰器"""
    return limiter.limit(
        RATE_LIMITS['vote:create'],
        key_func=get_rate_limit_key,
        per_method=True,
        methods=['POST']
    )
