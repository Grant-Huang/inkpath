"""Bot声誉API"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.reputation_service import (
    get_reputation_history, get_reputation_summary
)


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


reputation_bp = Blueprint('reputation', __name__)


@reputation_bp.route('/bots/<bot_id>/reputation', methods=['GET'])
def get_bot_reputation(bot_id):
    """获取Bot声誉信息API"""
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
    
    db: Session = get_db_session()
    
    try:
        summary = get_reputation_summary(db, bot_uuid)
        
        # 获取最近的历史记录
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        history = get_reputation_history(db, bot_uuid, limit=limit, offset=offset)
        
        return jsonify({
            'status': 'success',
            'data': {
                'current_reputation': summary['current_reputation'],
                'status': summary['status'],
                'total_changes': summary['total_changes'],
                'history': [
                    {
                        'id': str(log.id),
                        'change': log.change,
                        'reason': log.reason,
                        'related_type': log.related_type,
                        'related_id': str(log.related_id) if log.related_id else None,
                        'created_at': log.created_at.isoformat() if log.created_at else None
                    }
                    for log in history
                ]
            }
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
                'message': f'获取声誉信息失败: {str(e)}'
            }
        }), 500
