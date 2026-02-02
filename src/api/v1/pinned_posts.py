"""置顶帖管理API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.pinned_post_service import (
    create_pinned_post, get_pinned_posts_by_story,
    get_pinned_post_by_id, update_pinned_post
)
from src.utils.auth import bot_auth_required, user_auth_required


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


pinned_posts_bp = Blueprint('pinned_posts', __name__)


@pinned_posts_bp.route('/stories/<story_id>/pins', methods=['POST'])
def create_pinned_post_endpoint(story_id):
    """创建置顶帖API（需要Bot或用户认证）"""
    # 尝试用户认证（JWT）- 优先尝试JWT
    user = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '', 1)
        
        # 先尝试JWT验证
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                db = get_db_session()
                from src.models.user import User
                user = db.query(User).filter(User.id == user_id).first()
        except:
            pass
        
        # 如果JWT验证失败，尝试Bot API Key
        bot = None
        if not user:
            from src.services.bot_service import authenticate_bot
            db = get_db_session()
            bot = authenticate_bot(db, token)
    else:
        bot = None
    
    if not user and not bot:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '需要认证'
            }
        }), 401
    
    try:
        story_uuid = uuid.UUID(story_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的故事ID格式'
            }
        }), 400
    
    data = request.get_json()
    
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: title, content'
            }
        }), 400
    
    title = data.get('title')
    content = data.get('content')
    order_index = data.get('order_index', 0)
    
    # 确定pinned_by
    if user:
        pinned_by = user.id
    else:
        # Bot不能直接创建置顶帖，需要用户
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'FORBIDDEN',
                'message': '只有用户才能创建置顶帖'
            }
        }), 403
    
    db: Session = get_db_session()
    
    try:
        pinned_post = create_pinned_post(
            db=db,
            story_id=story_uuid,
            title=title,
            content=content,
            pinned_by=pinned_by,
            order_index=order_index
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': str(pinned_post.id),
                'story_id': str(pinned_post.story_id),
                'title': pinned_post.title,
                'content': pinned_post.content,
                'order_index': pinned_post.order_index,
                'created_at': pinned_post.created_at.isoformat() if pinned_post.created_at else None
            }
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
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'创建置顶帖失败: {str(e)}'
            }
        }), 500


@pinned_posts_bp.route('/stories/<story_id>/pins', methods=['GET'])
def get_pinned_posts_endpoint(story_id):
    """获取置顶帖列表API"""
    try:
        story_uuid = uuid.UUID(story_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的故事ID格式'
            }
        }), 400
    
    db: Session = get_db_session()
    pinned_posts = get_pinned_posts_by_story(db, story_uuid)
    
    return jsonify({
        'status': 'success',
        'data': {
            'pinned_posts': [
                {
                    'id': str(post.id),
                    'title': post.title,
                    'content': post.content,
                    'order_index': post.order_index,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'updated_at': post.updated_at.isoformat() if post.updated_at else None
                }
                for post in pinned_posts
            ],
            'count': len(pinned_posts)
        }
    }), 200


@pinned_posts_bp.route('/stories/<story_id>/pins/<pin_id>', methods=['PUT'])
def update_pinned_post_endpoint(story_id, pin_id):
    """更新置顶帖API（需要Bot或用户认证）"""
    # 尝试Bot认证
    bot = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        api_key = auth_header.replace('Bearer ', '', 1)
        from src.services.bot_service import authenticate_bot
        db = get_db_session()
        bot = authenticate_bot(db, api_key)
    
    # 尝试用户认证（JWT）
    user = None
    if not bot:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                db = get_db_session()
                from src.models.user import User
                user = db.query(User).filter(User.id == user_id).first()
        except:
            pass
    
    if not bot and not user:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '需要认证'
            }
        }), 401
    
    try:
        story_uuid = uuid.UUID(story_id)
        pin_uuid = uuid.UUID(pin_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的ID格式'
            }
        }), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少更新数据'
            }
        }), 400
    
    title = data.get('title')
    content = data.get('content')
    order_index = data.get('order_index')
    
    db: Session = get_db_session()
    pinned_post = update_pinned_post(
        db=db,
        pinned_post_id=pin_uuid,
        title=title,
        content=content,
        order_index=order_index
    )
    
    if not pinned_post:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': '置顶帖不存在'
            }
        }), 404
    
    # 验证置顶帖属于该故事
    if pinned_post.story_id != story_uuid:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '置顶帖不属于该故事'
            }
        }), 400
    
    return jsonify({
        'status': 'success',
        'data': {
            'id': str(pinned_post.id),
            'title': pinned_post.title,
            'content': pinned_post.content,
            'order_index': pinned_post.order_index,
            'updated_at': pinned_post.updated_at.isoformat() if pinned_post.updated_at else None
        }
    }), 200
