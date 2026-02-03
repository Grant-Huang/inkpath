"""速率限制辅助函数（手动检查）"""
from flask import jsonify, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from src.config import Config
import uuid


# 单例 Redis 连接
_redis_client = None


def get_redis_connection():
    """获取Redis连接（单例模式）"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True,
                socket_timeout=5,  # 5秒超时
                socket_connect_timeout=5
            )
            # 测试连接
            _redis_client.ping()
        except Exception as e:
            import logging
            logging.error(f"Redis连接失败: {e}")
            return None
    return _redis_client


def check_rate_limit(action: str, bot_id: uuid.UUID = None, branch_id: uuid.UUID = None, user_id: uuid.UUID = None):
    """
    手动检查速率限制
    
    Args:
        action: 操作类型 ('segment:create', 'branch:create', 'comment:create', 'branch:join', 'vote:create')
        bot_id: Bot ID（可选）
        branch_id: 分支ID（可选，用于segment:create）
        user_id: User ID（可选，用于comment:create和vote:create）
    
    Returns:
        如果超过限制，返回429响应；否则返回None
    """
    from src.utils.rate_limit import RATE_LIMITS
    
    if action not in RATE_LIMITS:
        return None
    
    # 构建key
    if action == 'segment:create' and branch_id and bot_id:
        key = f"bot:{bot_id}:branch:{branch_id}"
    elif action in ['branch:create', 'branch:join'] and bot_id:
        key = f"bot:{bot_id}"
    elif action in ['comment:create', 'vote:create']:
        if bot_id:
            key = f"bot:{bot_id}"
        elif user_id:
            key = f"user:{user_id}"
        elif hasattr(g, 'current_user') and g.current_user:
            key = f"user:{g.current_user.id}"
        elif hasattr(g, 'current_bot') and g.current_bot:
            key = f"bot:{g.current_bot.id}"
        else:
            key = get_remote_address()
    else:
        return None  # 无法确定key，跳过速率限制
    
    # 检查速率限制
    try:
        limit = RATE_LIMITS[action]
        # 解析限制（例如 "2 per hour"）
        parts = limit.split()
        max_requests = int(parts[0])
        
        # 直接使用Redis来检查
        redis_client = get_redis_connection()
        if redis_client is None:
            # Redis 不可用，跳过速率限制
            return None
        
        redis_key = f"LIMITER:{key}:{action}"
        
        # 获取当前计数
        current = redis_client.get(redis_key)
        if current:
            current = int(current)
            if current >= max_requests:
                return jsonify({
                    'status': 'error',
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': '速率限制已超出，请稍后再试'
                    }
                }), 429
        
        # 增加计数
        redis_client.incr(redis_key)
        redis_client.expire(redis_key, 3600)  # 1小时过期
        
    except Exception as e:
        # 如果Redis不可用，记录错误但不阻止请求
        import logging
        logging.error(f"速率限制检查失败: {e}")
        return None
    
    return None
