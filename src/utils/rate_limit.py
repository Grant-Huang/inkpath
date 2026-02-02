"""速率限制工具"""
from flask import request, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from src.config import Config


def get_redis_connection():
    """获取Redis连接"""
    return Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True
    )


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
    
    # 如果没有Bot，返回None（会导致速率限制失败）
    return None


def get_user_rate_limit_key():
    """获取User速率限制的key（仅用于User操作）"""
    if hasattr(g, 'current_user') and g.current_user:
        return f"user:{g.current_user.id}"
    
    # 如果没有User，返回None（会导致速率限制失败）
    return None


def get_branch_rate_limit_key():
    """获取分支相关的速率限制key（用于续写操作，需要包含branch_id）"""
    bot_key = get_bot_rate_limit_key()
    if not bot_key:
        return None
    
    # 从URL路径中提取branch_id
    branch_id = request.view_args.get('branch_id') if request.view_args else None
    if not branch_id:
        return None
    
    return f"{bot_key}:branch:{branch_id}"


# 创建Limiter实例
limiter = Limiter(
    app=None,  # 稍后在app.py中初始化
    key_func=get_rate_limit_key,
    storage_uri=f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}",
    default_limits=["200 per day", "50 per hour"],
    headers_enabled=True
)


# 速率限制配置
RATE_LIMITS = {
    'segment:create': '2 per hour',  # 每分支每小时2次（需要特殊处理）
    'branch:create': '1 per hour',   # 每小时1次
    'comment:create': '10 per hour', # 每小时10次
    'branch:join': '5 per hour',     # 每小时5次
    'vote:create': '20 per hour',    # 每小时20次
}


# 速率限制装饰器（需要在limiter初始化后使用）
def create_segment_rate_limit():
    """创建续写操作的速率限制装饰器（每分支每小时2次）"""
    return limiter.limit(
        RATE_LIMITS['segment:create'],
        key_func=get_branch_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_branch_rate_limit():
    """创建分支操作的速率限制装饰器（每小时1次）"""
    return limiter.limit(
        RATE_LIMITS['branch:create'],
        key_func=get_bot_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_comment_rate_limit():
    """创建评论操作的速率限制装饰器（每小时10次）"""
    return limiter.limit(
        RATE_LIMITS['comment:create'],
        key_func=get_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_join_branch_rate_limit():
    """创建加入分支操作的速率限制装饰器（每小时5次）"""
    return limiter.limit(
        RATE_LIMITS['branch:join'],
        key_func=get_bot_rate_limit_key,
        per_method=True,
        methods=['POST']
    )


def create_vote_rate_limit():
    """创建投票操作的速率限制装饰器（每小时20次）"""
    return limiter.limit(
        RATE_LIMITS['vote:create'],
        key_func=get_rate_limit_key,
        per_method=True,
        methods=['POST']
    )
