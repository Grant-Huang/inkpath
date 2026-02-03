"""通知队列工具"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.config import Config

# 尝试导入Redis和RQ
try:
    from redis import Redis
    from rq import Queue
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# 全局队列变量
_notification_queue = None


def is_queue_available() -> bool:
    """检查队列是否可用"""
    if not REDIS_AVAILABLE:
        return False
    try:
        from redis import Redis
        redis_conn = Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        redis_conn.ping()
        return True
    except Exception:
        return False


def get_notification_queue():
    """
    获取通知队列
    
    Returns:
        RQ队列对象，如果不可用返回None
    """
    global _notification_queue
    
    if not is_queue_available():
        return None
    
    if _notification_queue is None:
        try:
            from redis import Redis
            from rq import Queue
            redis_conn = Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True
            )
            _notification_queue = Queue('notifications', connection=redis_conn)
        except Exception:
            return None
    
    return _notification_queue


def enqueue_notification(
    bot_id: str,
    event: str,
    data: dict,
    retry_count: int = 3
):
    """
    将通知加入队列
    
    Args:
        bot_id: Bot ID
        event: 事件类型
        data: 事件数据
        retry_count: 重试次数
    
    Returns:
        Job ID，如果队列不可用返回None
    """
    queue = get_notification_queue()
    if queue is None:
        print(f"Notification queue unavailable, skipping: {event}")
        return None
    
    try:
        from src.workers.notification_worker import send_notification_job
        
        job = queue.enqueue(
            send_notification_job,
            bot_id,
            event,
            data,
            job_timeout=30,
            retry=retry_count,
            retry_backoff=True,
            retry_backoff_max=90
        )
        return job.id
    except Exception as e:
        print(f"Failed to enqueue notification: {e}")
        return None


def enqueue_your_turn_notification(bot_id: str, branch_id: str):
    """将"轮到续写"通知加入队列"""
    queue = get_notification_queue()
    if queue is None:
        return None
    
    try:
        from src.workers.notification_worker import send_your_turn_notification_job
        
        job = queue.enqueue(
            send_your_turn_notification_job,
            bot_id,
            branch_id,
            job_timeout=30,
            retry=3,
            retry_backoff=True,
            retry_backoff_max=90
        )
        return job.id
    except Exception:
        return None


def enqueue_new_branch_notification(bot_id: str, branch_id: str):
    """将"新分支创建"通知加入队列"""
    queue = get_notification_queue()
    if queue is None:
        return None
    
    try:
        from src.workers.notification_worker import send_new_branch_notification_job
        
        job = queue.enqueue(
            send_new_branch_notification_job,
            bot_id,
            branch_id,
            job_timeout=30,
            retry=3,
            retry_backoff=True,
            retry_backoff_max=90
        )
        return job.id
    except Exception:
        return None
