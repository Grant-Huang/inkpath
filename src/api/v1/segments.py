"""续写管理API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.segment_service import (
    create_segment, get_segments_by_branch, get_segment_by_id,
    count_segments_by_branch, log_segment_creation
)
from src.services.branch_service import get_next_bot_in_queue
from src.utils.auth import bot_auth_required, api_token_auth_required
from src.utils.rate_limit import create_segment_rate_limit
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


segments_bp = Blueprint('segments', __name__)


def _create_segment_inner(db, branch_uuid, user_id=None, bot_id=None, bot_name=None, bot_model=None, content=None, is_starter=False):
    """内部创建片段逻辑"""
    from src.models.bot import Bot
    
    # 确定作者信息
    author_id = bot_id or user_id
    author_name = bot_name
    author_model = bot_model
    
    # 如果有 user_id，尝试获取用户信息
    if user_id:
        from src.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            author_name = user.name or user.email
            author_model = None  # 用户不是 Bot，没有 model
    
    # 如果有 bot_id，尝试获取 Bot 信息
    if bot_id and not bot_name:
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if bot:
            author_name = bot.name
            author_model = bot.model
    
    return create_segment(
        db=db,
        branch_id=branch_uuid,
        bot_id=author_id,
        content=content,
        is_starter=is_starter
    )


@segments_bp.route('/branches/<branch_id>/segments', methods=['POST'])
def create_segment_endpoint(branch_id):
    """提交续写API（支持 API Token 或 JWT 认证）"""
    import logging
    logger = logging.getLogger(__name__)
    
    # 尝试 JWT 认证
    user = None
    bot_id = None
    is_admin = False
    
    # 首先检查 Authorization header
    auth_header = request.headers.get('Authorization', '')
    logger.info(f"Auth header: {auth_header[:50]}...")
    
    try:
        # 验证 JWT
        verify_jwt_in_request(optional=True)
        jwt_identity = get_jwt_identity()
        
        if jwt_identity:
            logger.info(f"JWT identity: {jwt_identity}")
            
            # 获取 JWT claims
            jwt_claims = get_jwt()
            logger.info(f"JWT claims: {jwt_claims}")
            
            # 检查是否是 admin
            if jwt_claims and jwt_claims.get('user_type') == 'admin':
                is_admin = True
                logger.info("Admin认证成功")
            else:
                # 尝试查找 bot
                from src.models.bot import Bot
                db = get_db_session()
                bot = db.query(Bot).filter(Bot.id == jwt_identity).first()
                if bot:
                    bot_id = jwt_identity
                    logger.info(f"Bot认证成功: {bot.name}")
                else:
                    # 尝试查找用户
                    from src.models.user import User
                    try:
                        user = db.query(User).filter(User.id == jwt_identity).first()
                        logger.info(f"User认证成功: {user}")
                    except Exception as e:
                        logger.warning(f"用户查询失败: {e}")
        else:
            logger.info("没有JWT identity")
            
    except Exception as e:
        logger.warning(f"JWT验证异常: {e}")
        import traceback
        logger.warning(traceback.format_exc())
    
    # 如果没有 JWT，尝试 API Token
    if not user and not bot_id and not is_admin:
        from src.utils.auth import api_token_auth_required as _api_auth
        # 手动检查 API Token
        api_token = request.headers.get('X-API-Key')
        if not api_token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_token = auth_header[7:]
        
        if api_token:
            from src.services.api_token_service import validate_api_token
            db = get_db_session()
            user = validate_api_token(db, api_token)
            if not user:
                return jsonify({
                    'status': 'error',
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': '无效或已过期的 API Token'
                    }
                }), 401
        else:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '缺少认证信息，请使用 X-API-Key 或 JWT Token'
                }
            }), 401
    
    # 如果是 admin 或 bot，无需速率限制
    if not bot_id and not is_admin:
        # 检查速率限制（每用户每小时5次）
        from src.utils.rate_limit_helper import check_rate_limit
        rate_limit_result = check_rate_limit('segment:create', user_id=user.id)
        if rate_limit_result:
            return rate_limit_result
    
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
    is_starter = data.get('is_starter', False)
    
    db: Session = get_db_session()
    
    # 获取作者名称
    author_name = "Admin"
    user_id_for_segment = None
    
    if bot_id:
        from src.models.agent import Agent
        bot = db.query(Agent).filter(Agent.id == bot_id).first()
        author_name = bot.name if bot else "Bot"
        user_id_for_segment = None
    elif is_admin:
        author_name = "Admin"
        user_id_for_segment = None
    elif user:
        user_id_for_segment = user.id
        from src.models.user import User
        user_obj = db.query(User).filter(User.id == user.id).first()
        author_name = user_obj.name if user_obj else "Unknown"
    else:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '无法确定用户身份'
            }
        }), 401
    
    try:
        segment = _create_segment_inner(
            db=db,
            branch_uuid=branch_uuid,
            user_id=user_id_for_segment,
            bot_id=bot_id,
            bot_name=author_name,
            content=content,
            is_starter=is_starter
        )
        
        # 获取分支信息（用于日志）
        from src.models.branch import Branch
        branch_obj = db.query(Branch).filter(Branch.id == branch_uuid).first()
        
        # 记录创作日志
        try:
            author_type = 'bot' if bot_id else 'human'
            log_segment_creation(
                db=db,
                segment_id=segment.id,
                story_id=branch_obj.story_id if branch_obj else branch_uuid,
                branch_id=branch_uuid,
                author_id=bot_id or user.id,
                author_type=author_type,
                author_name=author_name or ('Bot' if bot_id else '未知用户'),
                content_length=len(content) if content else 0,
                is_continuation='new' if is_starter else 'continuation'
            )
        except Exception as log_error:
            import logging
            logging.warning(f"Failed to log segment creation: {log_error}")
        
        # 获取下一个 Bot
        next_bot = get_next_bot_in_queue(db, branch_uuid)
        
        # 通知下一个 Bot（异步）
        if next_bot and next_bot.webhook_url:
            try:
                from src.utils.notification_queue import enqueue_your_turn_notification
                enqueue_your_turn_notification(
                    bot_id=str(next_bot.id),
                    branch_id=str(branch_uuid)
                )
            except Exception as e:
                import logging
                logging.warning(f"Failed to enqueue your_turn notification: {str(e)}")
        
        author_id_str = str(bot_id) if bot_id else str(user.id)
        
        response_data = {
            'segment': {
                'id': str(segment.id),
                'content': segment.content,
                'sequence_order': segment.sequence_order,
                'author_id': author_id_str,
                'author_name': author_name,
                'author_type': 'bot' if bot_id else 'user',
                'created_at': segment.created_at.isoformat() if segment.created_at else None
            }
        }
        
        if next_bot:
            response_data['next_bot'] = {
                'id': str(next_bot.id),
                'name': next_bot.name,
                'model': next_bot.model
            }
        
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
    """获取续写列表API（公开，无需认证）"""
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
