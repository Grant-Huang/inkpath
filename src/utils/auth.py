"""认证工具函数"""
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from src.database import get_db
from src.services.bot_service import authenticate_bot
from src.services.api_token_service import validate_api_token
from src.models.user import User


def init_jwt(app):
    """初始化JWT"""
    jwt = JWTManager(app)
    return jwt


def get_bot_from_token(token: str):
    """从token获取Bot对象"""
    from flask import current_app
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        db = current_app.config['TEST_DB']
    else:
        db = next(get_db())
    return authenticate_bot(db, token)


def api_token_auth_required(f):
    """API Token 认证装饰器（简化认证，用于外部 Agent）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 优先从 X-API-Key Header 获取
        api_token = request.headers.get('X-API-Key')
        
        # 也支持 Authorization: Bearer 格式
        if not api_token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_token = auth_header[7:]
        
        if not api_token:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '缺少 API Token，请在 Header 中添加 X-API-Key'
                }
            }), 401
        
        # 验证 Token
        from flask import current_app
        if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
            db = current_app.config['TEST_DB']
        else:
            db = next(get_db())
        
        user = validate_api_token(db, api_token)
        
        if not user:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '无效或已过期的 API Token'
                }
            }), 401
        
        # 将用户对象存储到 g 对象中
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated_function


def bot_auth_required(f):
    """Bot认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从Header获取API Key
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '缺少或无效的Authorization header'
                }
            }), 401
        
        api_key = auth_header.replace('Bearer ', '', 1)
        
        # 验证API Key
        from flask import current_app
        if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
            db = current_app.config['TEST_DB']
        else:
            db = next(get_db())
        bot = authenticate_bot(db, api_key)
        
        if not bot:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '无效的API Key'
                }
            }), 401
        
        if bot.status != 'active':
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'Bot已被暂停'
                }
            }), 403
        
        # 将Bot对象存储到g对象中
        g.current_bot = bot
        
        return f(*args, **kwargs)
    
    return decorated_function


def user_auth_required(f):
    """用户认证装饰器（使用JWT）"""
    @jwt_required()
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        user_id = get_jwt_identity()
        if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
            db = current_app.config['TEST_DB']
        else:
            db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '用户不存在'
                }
            }), 401
        
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated_function
