"""定时任务调度器"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
import os
import requests
from src.config import Config


def init_scheduler(app: Flask):
    """
    初始化定时任务调度器
    
    如果设置了CRON_ENABLED=true，则启动本地调度器
    否则依赖外部Cron服务（如Vercel Cron）调用API端点
    """
    cron_enabled = os.getenv('CRON_ENABLED', 'false').lower() == 'true'
    
    if not cron_enabled:
        app.logger.info("定时任务调度器已禁用，将使用外部Cron服务")
        return None
    
    scheduler = BackgroundScheduler()
    cron_secret = os.getenv('CRON_SECRET', 'dev-cron-secret-change-in-production')
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # 每5分钟检查Bot超时
    def check_bot_timeouts_job():
        """检查Bot超时任务"""
        try:
            url = f"{base_url}/api/v1/cron/check-bot-timeouts"
            response = requests.post(
                url,
                headers={'Authorization': f'Bearer {cron_secret}'},
                timeout=60
            )
            if response.status_code == 200:
                app.logger.info(f"Bot超时检查任务执行成功: {response.json()}")
            else:
                app.logger.error(f"Bot超时检查任务执行失败: {response.status_code} - {response.text}")
        except Exception as e:
            app.logger.error(f"Bot超时检查任务执行异常: {e}")
    
    scheduler.add_job(
        func=check_bot_timeouts_job,
        trigger=CronTrigger(minute='*/5'),  # 每5分钟
        id='check_bot_timeouts',
        name='检查Bot超时',
        replace_existing=True
    )
    
    # 每小时更新活跃度得分
    def update_activity_scores_job():
        """更新活跃度得分任务"""
        try:
            url = f"{base_url}/api/v1/cron/update-activity-scores"
            response = requests.post(
                url,
                headers={'Authorization': f'Bearer {cron_secret}'},
                timeout=300  # 5分钟超时
            )
            if response.status_code == 200:
                app.logger.info(f"活跃度得分更新任务执行成功: {response.json()}")
            else:
                app.logger.error(f"活跃度得分更新任务执行失败: {response.status_code} - {response.text}")
        except Exception as e:
            app.logger.error(f"活跃度得分更新任务执行异常: {e}")
    
    scheduler.add_job(
        func=update_activity_scores_job,
        trigger=CronTrigger(minute=0),  # 每小时（整点）
        id='update_activity_scores',
        name='更新活跃度得分',
        replace_existing=True
    )
    
    # 每天清理过期数据
    def cleanup_expired_data_job():
        """清理过期数据任务"""
        try:
            url = f"{base_url}/api/v1/cron/cleanup-expired-data"
            response = requests.post(
                url,
                headers={'Authorization': f'Bearer {cron_secret}'},
                timeout=300
            )
            if response.status_code == 200:
                app.logger.info(f"清理过期数据任务执行成功: {response.json()}")
            else:
                app.logger.error(f"清理过期数据任务执行失败: {response.status_code} - {response.text}")
        except Exception as e:
            app.logger.error(f"清理过期数据任务执行异常: {e}")
    
    scheduler.add_job(
        func=cleanup_expired_data_job,
        trigger=CronTrigger(hour=2, minute=0),  # 每天凌晨2点
        id='cleanup_expired_data',
        name='清理过期数据',
        replace_existing=True
    )
    
    scheduler.start()
    app.logger.info("定时任务调度器已启动")
    
    return scheduler
