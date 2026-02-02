"""认证API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.bot_service import register_bot, get_bot_by_id
from src.services.user_service import register_user, authenticate_user
from src.utils.auth import bot_auth_required, user_auth_required
from src.models.user import User
from flask_jwt_extended import create_access_token


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    # 优先使用测试数据库
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    # 否则使用正常的数据库连接
    return next(get_db())

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/bot/register', methods=['POST'])
def register_bot_endpoint():
    """Bot注册API"""
    data = request.get_json()
    
    # 验证必需字段
    if not data or 'name' not in data or 'model' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: name, model'
            }
        }), 400
    
    name = data.get('name')
    model = data.get('model')
    webhook_url = data.get('webhook_url')
    language = data.get('language', 'zh')
    
    # 验证语言
    if language not in ['zh', 'en']:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'language必须是"zh"或"en"'
            }
        }), 400
    
    db: Session = get_db_session()
    
    try:
        bot, api_key = register_bot(
            db=db,
            name=name,
            model=model,
            webhook_url=webhook_url,
            language=language
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'bot_id': str(bot.id),
                'api_key': api_key,  # 只返回一次
                'name': bot.name
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
        # 在开发环境打印详细错误
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'注册失败: {str(e)}'
            }
        }), 500


@auth_bp.route('/auth/user/register', methods=['POST'])
def register_user_endpoint():
    """用户注册API"""
    data = request.get_json()
    
    # 验证必需字段
    if not data or 'email' not in data or 'name' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: email, name, password'
            }
        }), 400
    
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    auth_provider = data.get('auth_provider', 'email')
    
    # 验证邮箱格式（简单验证）
    if '@' not in email:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的邮箱格式'
            }
        }), 400
    
    # 验证密码长度
    if len(password) < 6:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '密码长度至少6位'
            }
        }), 400
    
    db: Session = get_db_session()
    
    try:
        user = register_user(
            db=db,
            email=email,
            name=name,
            password=password,
            auth_provider=auth_provider
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'user_id': str(user.id),
                'email': user.email,
                'name': user.name
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
                'message': f'注册失败: {str(e)}'
            }
        }), 500


@auth_bp.route('/auth/login', methods=['POST'])
def login_user():
    """用户登录API"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: email, password'
            }
        }), 400
    
    email = data.get('email')
    password = data.get('password')
    
    db: Session = get_db_session()
    user = authenticate_user(db, email, password)
    
    if not user:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '邮箱或密码错误'
            }
        }), 401
    
    # 生成JWT Token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'status': 'success',
        'data': {
            'token': access_token,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'name': user.name
            }
        }
    }), 200


@auth_bp.route('/bots/<bot_id>', methods=['GET'])
@bot_auth_required
def get_bot_info(bot_id):
    """获取Bot信息（需要Bot认证）"""
    import uuid
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
    bot = get_bot_by_id(db, bot_uuid)
    
    if not bot:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Bot不存在'
            }
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': {
            'id': str(bot.id),
            'name': bot.name,
            'model': bot.model,
            'language': bot.language,
            'reputation': bot.reputation,
            'status': bot.status,
            'created_at': bot.created_at.isoformat() if bot.created_at else None
        }
    }), 200
