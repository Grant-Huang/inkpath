"""通知队列工具"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from redis import Redis
from rq import Queue
from src.config import Config


def get_notification_queue() -> Queue:
    """
    获取通知队列
    
    Returns:
        RQ队列对象
    """
    redis_conn = Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True
    )
    
    return Queue('notifications', connection=redis_conn)


def enqueue_notification(
    bot_id: str,
    event: str,
    data: dict,
    retry_count: int = 3
) -> str:
    """
    将通知加入队列
    
    Args:
        bot_id: Bot ID
        event: 事件类型
        data: 事件数据
        retry_count: 重试次数
    
    Returns:
        Job ID
    """
    from src.workers.notification_worker import send_notification_job
    
    queue = get_notification_queue()
    
    job = queue.enqueue(
        send_notification_job,
        bot_id,
        event,
        data,
        job_timeout=30,  # 30秒超时
        retry=retry_count,
        retry_backoff=True,  # 指数退避
        retry_backoff_max=90  # 最大90秒
    )
    
    return job.id


def enqueue_your_turn_notification(
    bot_id: str,
    branch_id: str
) -> str:
    """
    将"轮到续写"通知加入队列
    
    Returns:
        Job ID
    """
    from src.workers.notification_worker import send_your_turn_notification_job
    
    queue = get_notification_queue()
    
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


def enqueue_new_branch_notification(
    bot_id: str,
    branch_id: str
) -> str:
    """
    将"新分支创建"通知加入队列
    
    Returns:
        Job ID
    """
    from src.workers.notification_worker import send_new_branch_notification_job
    
    queue = get_notification_queue()
    
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
