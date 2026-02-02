"""Redis 缓存工具"""
import json
import uuid
from typing import Optional, Any, Dict
from redis import Redis
from src.config import Config
from functools import wraps
import hashlib


def get_redis_connection() -> Redis:
    """获取Redis连接"""
    return Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True
    )


class CacheService:
    """缓存服务"""
    
    def __init__(self):
        self.redis = get_redis_connection()
        self.default_ttl = 300  # 默认5分钟
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            # 缓存失败不影响主流程
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            return self.redis.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete_pattern error: {e}")
            return 0
    
    def invalidate_story(self, story_id: uuid.UUID):
        """使故事相关缓存失效"""
        story_id_str = str(story_id)
        self.delete_pattern(f"story:{story_id_str}*")
        self.delete_pattern(f"branches:story:{story_id_str}*")
    
    def invalidate_branch(self, branch_id: uuid.UUID):
        """使分支相关缓存失效"""
        branch_id_str = str(branch_id)
        self.delete_pattern(f"branch:{branch_id_str}*")
        self.delete_pattern(f"segments:branch:{branch_id_str}*")
        self.delete_pattern(f"comments:branch:{branch_id_str}*")
        self.delete_pattern(f"summary:branch:{branch_id_str}*")
    
    def invalidate_segment(self, segment_id: uuid.UUID, branch_id: uuid.UUID):
        """使续写段相关缓存失效"""
        self.invalidate_branch(branch_id)


# 全局缓存服务实例
cache_service = CacheService()


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键"""
    # 将参数序列化为字符串
    parts = [prefix]
    if args:
        parts.extend(str(arg) for arg in args)
    if kwargs:
        # 排序确保一致性
        sorted_kwargs = sorted(kwargs.items())
        parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
    
    key_str = ":".join(parts)
    # 如果键太长，使用hash
    if len(key_str) > 200:
        key_str = f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    return key_str


def cached(ttl: int = 300, key_prefix: str = None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            prefix = key_prefix or f"{func.__module__}:{func.__name__}"
            cache_key_str = cache_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache_service.get(cache_key_str)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache_service.set(cache_key_str, result, ttl)
            
            return result
        return wrapper
    return decorator
