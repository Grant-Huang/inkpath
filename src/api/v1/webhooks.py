"""Webhook管理API"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.webhook_service import update_webhook_url, get_webhook_status, validate_webhook_url
from src.utils.auth import bot_auth_required


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/bots/<bot_id>/webhook', methods=['PUT'])
@bot_auth_required
def update_webhook_endpoint(bot_id):
    """更新Bot的Webhook URL API（需要Bot认证）"""
    from flask import g
    bot = g.current_bot
    
    # 验证Bot ID匹配
    try:
        bot_uuid = uuid.UUID(bot_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的Bot ID格式'
            }
        }), 400
    
    if bot.id != bot_uuid:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'FORBIDDEN',
                'message': '只能更新自己的Webhook URL'
            }
        }), 403
    
    data = request.get_json()
    
    if not data or 'webhook_url' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: webhook_url'
            }
        }), 400
    
    webhook_url = data.get('webhook_url')
    
    db: Session = get_db_session()
    
    try:
        updated_bot = update_webhook_url(db, bot_uuid, webhook_url)
        
        return jsonify({
            'status': 'success',
            'data': {
                'bot_id': str(updated_bot.id),
                'webhook_url': updated_bot.webhook_url
            }
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'更新Webhook URL失败: {str(e)}'
            }
        }), 500


@webhooks_bp.route('/bots/<bot_id>/webhook/status', methods=['GET'])
@bot_auth_required
def get_webhook_status_endpoint(bot_id):
    """获取Bot的Webhook状态API（需要Bot认证）"""
    from flask import g
    bot = g.current_bot
    
    try:
        bot_uuid = uuid.UUID(bot_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的Bot ID格式'
            }
        }), 400
    
    if bot.id != bot_uuid:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'FORBIDDEN',
                'message': '只能查看自己的Webhook状态'
            }
        }), 403
    
    db: Session = get_db_session()
    
    try:
        status = get_webhook_status(db, bot_uuid)
        
        return jsonify({
            'status': 'success',
            'data': status
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'获取Webhook状态失败: {str(e)}'
            }
        }), 500
