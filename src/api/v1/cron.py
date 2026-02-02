"""定时任务API"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.cron_service import (
    check_bot_timeouts,
    update_activity_scores,
    cleanup_expired_data
)
import os


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


cron_bp = Blueprint('cron', __name__)


def verify_cron_secret():
    """验证Cron Secret"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    
    token = auth_header.replace('Bearer ', '', 1)
    expected_secret = os.getenv('CRON_SECRET', 'dev-cron-secret-change-in-production')
    
    return token == expected_secret


@cron_bp.route('/cron/check-bot-timeouts', methods=['POST', 'GET'])
def check_bot_timeouts_endpoint():
    """
    检查Bot超时任务（定时任务端点）
    
    需要CRON_SECRET认证
    """
    # 验证Cron Secret
    if not verify_cron_secret():
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '无效的Cron Secret'
            }
        }), 401
    
    db: Session = get_db_session()
    
    try:
        results = check_bot_timeouts(db)
        
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
    
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'执行定时任务失败: {str(e)}'
            }
        }), 500


@cron_bp.route('/cron/update-activity-scores', methods=['POST', 'GET'])
def update_activity_scores_endpoint():
    """
    更新活跃度得分任务（定时任务端点）
    
    需要CRON_SECRET认证
    """
    # 验证Cron Secret
    if not verify_cron_secret():
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '无效的Cron Secret'
            }
        }), 401
    
    db: Session = get_db_session()
    
    try:
        results = update_activity_scores(db)
        
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
    
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'执行定时任务失败: {str(e)}'
            }
        }), 500


@cron_bp.route('/cron/cleanup-expired-data', methods=['POST', 'GET'])
def cleanup_expired_data_endpoint():
    """
    清理过期数据任务（定时任务端点）
    
    需要CRON_SECRET认证
    """
    # 验证Cron Secret
    if not verify_cron_secret():
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '无效的Cron Secret'
            }
        }), 401
    
    db: Session = get_db_session()
    
    try:
        results = cleanup_expired_data(db)
        
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
    
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'执行定时任务失败: {str(e)}'
            }
        }), 500
