"""评论API"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.comment_service import create_comment, get_comments_by_branch
from src.utils.rate_limit import create_comment_rate_limit


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/branches/<branch_id>/comments', methods=['POST'])
def create_comment_endpoint(branch_id):
    """发表评论API（支持Bot和人类）"""
    # 尝试认证
    user = None
    bot = None
    auth_header = request.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '', 1)
        
        # 先尝试JWT验证（人类）
        from flask_jwt_extended import decode_token
        import uuid
        try:
            decoded = decode_token(token)
            user_id_str = decoded.get('sub')
            if user_id_str:
                user_id = uuid.UUID(user_id_str)
                db = get_db_session()
                from src.models.user import User
                user = db.query(User).filter(User.id == user_id).first()
        except:
            pass
        
        # 如果JWT验证失败，尝试Bot API Key
        if not user:
            from src.services.bot_service import authenticate_bot
            db = get_db_session()
            bot = authenticate_bot(db, token)
    
    if not user and not bot:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '需要认证'
            }
        }), 401
    
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
    parent_comment_id = data.get('parent_comment_id')
    
    # 确定作者
    if user:
        author_id = user.id
        author_type = 'human'
        g.current_user = user
    else:
        author_id = bot.id
        author_type = 'bot'
        g.current_bot = bot
    
    # 检查速率限制
    from src.utils.rate_limit_helper import check_rate_limit
    if bot:
        rate_limit_result = check_rate_limit('comment:create', bot_id=bot.id)
    elif user:
        rate_limit_result = check_rate_limit('comment:create', user_id=user.id)
    else:
        rate_limit_result = None
    
    if rate_limit_result:
        return rate_limit_result
    
    db: Session = get_db_session()
    
    try:
        # 转换parent_comment_id
        parent_uuid = None
        if parent_comment_id:
            try:
                parent_uuid = uuid.UUID(parent_comment_id)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': '无效的parent_comment_id格式'
                    }
                }), 400
        
        comment = create_comment(
            db=db,
            branch_id=branch_uuid,
            author_id=author_id,
            author_type=author_type,
            content=content,
            parent_comment_id=parent_uuid
        )
        
        # 获取作者信息
        author_info = {}
        if author_type == 'bot':
            author_info = {
                'id': str(bot.id),
                'name': bot.name,
                'type': 'bot'
            }
        else:
            author_info = {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'type': 'human'
            }
        
        return jsonify({
            'status': 'success',
            'data': {
                'comment': {
                    'id': str(comment.id),
                    'content': comment.content,
                    'author_type': comment.author_type,
                    'author': author_info,
                    'parent_comment_id': str(comment.parent_comment) if comment.parent_comment else None,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None
                }
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
                'message': f'发表评论失败: {str(e)}'
            }
        }), 500


@comments_bp.route('/branches/<branch_id>/comments', methods=['GET'])
def get_comments_endpoint(branch_id):
    """获取评论树API"""
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
    
    db: Session = get_db_session()
    
    try:
        comments = get_comments_by_branch(db, branch_uuid)
        
        return jsonify({
            'status': 'success',
            'data': {
                'comments': comments
            }
        }), 200
    
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'获取评论失败: {str(e)}'
            }
        }), 500
