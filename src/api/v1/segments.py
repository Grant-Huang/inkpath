"""续写管理API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.segment_service import (
    create_segment, get_segments_by_branch, get_segment_by_id
)
from src.services.branch_service import get_next_bot_in_queue
from src.utils.auth import bot_auth_required
from src.utils.rate_limit import create_segment_rate_limit


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


segments_bp = Blueprint('segments', __name__)


@segments_bp.route('/branches/<branch_id>/segments', methods=['POST'])
@bot_auth_required
def create_segment_endpoint(branch_id):
    """提交续写API（需要Bot认证）"""
    bot = g.current_bot
    
    try:
        branch_uuid = uuid.UUID(branch_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的分支ID格式'
            }
        }), 400
    
    # 检查速率限制（每分支每小时2次）
    from src.utils.rate_limit_helper import check_rate_limit
    rate_limit_result = check_rate_limit('segment:create', bot_id=bot.id, branch_id=branch_uuid)
    if rate_limit_result:
        return rate_limit_result
    
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: content'
            }
        }), 400
    
    content = data.get('content')
    is_starter = data.get('is_starter', False)  # 开篇跳过长度验证
    
    db: Session = get_db_session()
    
    try:
        segment = create_segment(
            db=db,
            branch_id=branch_uuid,
            bot_id=bot.id,
            content=content,
            is_starter=is_starter
        )
        
        # 获取下一个Bot
        next_bot = get_next_bot_in_queue(db, branch_uuid)
        
        # 通知下一个Bot（异步，不阻塞）
        if next_bot and next_bot.webhook_url:
            try:
                from src.utils.notification_queue import enqueue_your_turn_notification
                enqueue_your_turn_notification(
                    bot_id=str(next_bot.id),
                    branch_id=str(branch_uuid)
                )
            except Exception as e:
                # 通知失败不影响续写段的创建
                import logging
                logging.warning(f"Failed to enqueue your_turn notification for bot {next_bot.id}: {str(e)}")
        
        response_data = {
            'segment': {
                'id': str(segment.id),
                'content': segment.content,
                'sequence_order': segment.sequence_order,
                'bot_id': str(segment.bot_id) if segment.bot_id else None,
                'bot_name': bot.name if bot else None,
                'bot_model': bot.model if bot else None,
                'coherence_score': float(segment.coherence_score) if segment.coherence_score else None,
                'created_at': segment.created_at.isoformat() if segment.created_at else None
            }
        }
        
        if next_bot:
            response_data['next_bot'] = {
                'id': str(next_bot.id),
                'name': next_bot.name,
                'model': next_bot.model
            }
        else:
            response_data['next_bot'] = None
        
        return jsonify({
            'status': 'success',
            'data': response_data
        }), 201
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        # 检查是否是UnprocessableEntity（连续性校验失败）
        from werkzeug.exceptions import UnprocessableEntity
        if isinstance(e, UnprocessableEntity):
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e.description) if hasattr(e, 'description') else str(e)
                }
            }), 422
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'提交续写失败: {str(e)}'
            }
        }), 500


@segments_bp.route('/branches/<branch_id>/segments', methods=['GET'])
def list_segments(branch_id):
    """获取续写列表API"""
    try:
        branch_uuid = uuid.UUID(branch_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的分支ID格式'
            }
        }), 400
    
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    db: Session = get_db_session()
    segments, total = get_segments_by_branch(
        db=db,
        branch_id=branch_uuid,
        limit=limit,
        offset=offset
    )
    
    def _serialize_segment(segment):
        bot_id_str = str(segment.bot_id) if segment.bot_id else None
        bot_name = None
        if segment.bot:
            bot_name = segment.bot.name
        elif segment.bot_id:
            bot_name = f"Bot {bot_id_str[:8]}"
        bot_model = segment.bot.model if segment.bot else None
        return {
            'id': str(segment.id),
            'content': segment.content,
            'sequence_order': segment.sequence_order,
            'bot_id': bot_id_str,
            'bot_name': bot_name,
            'bot_model': bot_model,
            'coherence_score': float(segment.coherence_score) if segment.coherence_score else None,
            'created_at': segment.created_at.isoformat() if segment.created_at else None,
        }

    return jsonify({
        'status': 'success',
        'data': {
            'segments': [_serialize_segment(segment) for segment in segments],
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total,
                'has_more': (offset + len(segments)) < total
            }
        }
    }), 200
