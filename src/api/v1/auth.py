# 用户认证模块

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    jwt_required, get_jwt_identity,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

auth_bp = Blueprint('auth', __name__)
jwt = JWTManager()

# 存储（生产环境应使用数据库）
users_db = {}

# 预置管理员用户
ADMIN_EMAIL = "jacer.huang@gmail.com"
ADMIN_PASSWORD = "80fd7e9b-27ae-4704-8789-0202b8fe6739"

def init_admin_user():
    """初始化管理员用户"""
    global users_db
    admin_id = "admin-00000000-0000-0000-0000-000000000000"
    users_db[admin_id] = {
        'id': admin_id,
        'username': 'admin',
        'email': ADMIN_EMAIL,
        'password_hash': generate_password_hash(ADMIN_PASSWORD),
        'user_type': 'admin',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    print(f"✅ 管理员用户已初始化: {ADMIN_EMAIL}")

# 初始化管理员
init_admin_user()

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['username', 'email', 'password', 'user_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400
    
    # 检查用户名/邮箱是否已存在
    for user in users_db.values():
        if user['username'] == data['username']:
            return jsonify({"error": "用户名已存在"}), 400
        if user['email'] == data['email']:
            return jsonify({"error": "邮箱已存在"}), 400
    
    # 验证用户类型
    if data['user_type'] not in ['human', 'agent', 'admin']:
        return jsonify({"error": "无效的用户类型"}), 400
    
    # 创建用户
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        'id': user_id,
        'username': data['username'],
        'email': data['email'],
        'password_hash': generate_password_hash(data['password']),
        'user_type': data['user_type'],
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # 生成 token
    access_token = create_access_token(
        identity=user_id,
        additional_claims={'user_type': data['user_type']}
    )
    
    return jsonify({
        "message": "注册成功",
        "user": {
            "id": user_id,
            "username": data['username'],
            "email": data['email'],
            "user_type": data['user_type']
        },
        "access_token": access_token
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "邮箱和密码必填"}), 400
    
    # 查找用户
    user = None
    for u in users_db.values():
        if u['email'] == data['email']:
            user = u
            break
    
    if not user:
        return jsonify({"error": "用户不存在"}), 401
    
    # 验证密码
    if not check_password_hash(user['password_hash'], data['password']):
        return jsonify({"error": "密码错误"}), 401
    
    # 生成 token
    access_token = create_access_token(
        identity=user['id'],
        additional_claims={'user_type': user['user_type']}
    )
    
    return jsonify({
        "message": "登录成功",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "user_type": user['user_type']
        },
        "access_token": access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """获取当前用户信息"""
    user_id = get_jwt_identity()
    user = users_db.get(user_id)
    
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "user_type": user['user_type'],
        "created_at": user['created_at']
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出（客户端删除 token 即可）"""
    return jsonify({"message": "已登出"}), 200


# Agent 注册（需要管理员权限）
@auth_bp.route('/register_agent', methods=['POST'])
@jwt_required()
def register_agent():
    """Agent 注册"""
    current_user_id = get_jwt_identity()
    
    # 检查是否是管理员
    user = users_db.get(current_user_id, {})
    if user.get('user_type') != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    data = request.get_json()
    
    required_fields = ['username', 'email', 'agent_name']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400
    
    # 创建 Agent
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        'id': user_id,
        'username': data['username'],
        'email': data['email'],
        'password_hash': generate_password_hash(data['password']),
        'user_type': 'agent',
        'agent_name': data['agent_name'],
        'assigned_stories': data.get('assigned_stories', []),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    access_token = create_access_token(
        identity=user_id,
        additional_claims={'user_type': 'agent'}
    )
    
    return jsonify({
        "message": "Agent 注册成功",
        "agent_id": user_id,
        "agent_name": data['agent_name'],
        "access_token": access_token
    }), 201


# Bot API Key 登录（用于 InkPath Agent）
@auth_bp.route('/bot/login', methods=['POST'])
def bot_login():
    """Bot 使用 API Key 登录，获取 JWT Token"""
    from src.database import get_db
    from src.services.bot_service import authenticate_bot
    
    data = request.get_json()
    
    if not data.get('api_key'):
        return jsonify({"error": "API Key 必填"}), 400
    
    db = next(get_db())
    try:
        bot = authenticate_bot(db, data['api_key'])
        
        if not bot:
            return jsonify({"error": "无效的 API Key"}), 401
        
        if bot.status != 'active':
            return jsonify({"error": "Bot 已被暂停"}), 403
        
        # 生成 JWT Token
        access_token = create_access_token(
            identity=str(bot.id),
            additional_claims={
                'user_type': 'bot',
                'bot_name': bot.name,
                'bot_model': bot.model
            }
        )
        
        return jsonify({
            "message": "登录成功",
            "access_token": access_token,
            "bot": {
                "id": str(bot.id),
                "name": bot.name,
                "model": bot.model,
                "status": bot.status
            }
        }), 200
        
    finally:
        db.close()
