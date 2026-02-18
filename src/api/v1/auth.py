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

from src.database import get_db
from src.models.user import User
from src.services import user_service

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
    """用户注册（人类写入 User 表，agent/admin 仍用内存）"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体为空"}), 400

    required_fields = ['username', 'email', 'password', 'user_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400

    if data['user_type'] not in ['human', 'agent', 'admin']:
        return jsonify({"error": "无效的用户类型"}), 400

    # 人类用户：写入数据库 User 表
    if data['user_type'] == 'human':
        db = next(get_db())
        try:
            user = user_service.register_user(
                db,
                email=data['email'],
                name=data.get('username') or data['email'],
                password=data['password']
            )
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={'user_type': 'human', 'username': user.name, 'email': user.email}
            )
            return jsonify({
                "message": "注册成功",
                "user": {
                    "id": str(user.id),
                    "username": user.name,
                    "email": user.email,
                    "user_type": "human"
                },
                "access_token": access_token
            }), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            db.close()

    # agent / admin：保留内存存储
    for user in users_db.values():
        if user['username'] == data['username']:
            return jsonify({"error": "用户名已存在"}), 400
        if user['email'] == data['email']:
            return jsonify({"error": "邮箱已存在"}), 400

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
    """用户登录（人类查 User 表，admin/agent 查内存）"""
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "邮箱和密码必填"}), 400

    # 先查数据库人类用户
    db = next(get_db())
    try:
        human_user = user_service.authenticate_user(db, data['email'], data['password'])
        if human_user:
            access_token = create_access_token(
                identity=str(human_user.id),
                additional_claims={
                    'user_type': 'human',
                    'username': human_user.name,
                    'email': human_user.email
                }
            )
            return jsonify({
                "message": "登录成功",
                "user": {
                    "id": str(human_user.id),
                    "username": human_user.name,
                    "email": human_user.email,
                    "user_type": "human"
                },
                "access_token": access_token
            }), 200
    finally:
        db.close()

    # 再查内存 admin/agent
    user = None
    for u in users_db.values():
        if u['email'] == data['email']:
            user = u
            break
    if not user:
        return jsonify({"error": "用户不存在"}), 401
    if not check_password_hash(user['password_hash'], data['password']):
        return jsonify({"error": "密码错误"}), 401
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
    """获取当前用户信息（先查 User 表，再查内存）"""
    user_id = get_jwt_identity()
    try:
        uid = uuid.UUID(str(user_id)) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        uid = None
    if uid is not None:
        db = next(get_db())
        try:
            user_obj = user_service.get_user_by_id(db, uid)
            if user_obj:
                return jsonify({
                    "id": str(user_obj.id),
                    "username": user_obj.name,
                    "email": user_obj.email,
                    "user_type": "human"
                }), 200
        finally:
            db.close()
    user = users_db.get(str(user_id))
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "user_type": user['user_type'],
        "created_at": user.get('created_at')
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
    """Bot/Agent 使用 API Key 登录，获取 JWT Token（兼容 Agent 与 Bot 模型）"""
    from src.database import get_db
    from src.services.bot_service import authenticate_bot

    data = request.get_json() or {}
    if not data.get('api_key'):
        return jsonify({"error": "API Key 必填"}), 400

    db = next(get_db())
    try:
        bot = authenticate_bot(db, data['api_key'])
        if not bot:
            return jsonify({"error": "无效的 API Key"}), 401

        # Agent 表 status 为 idle/running/error，Bot 表为 active/suspended；均允许 active 或 idle 登录
        if bot.status not in ('active', 'idle'):
            return jsonify({"error": "Bot 已被暂停"}), 403

        # Agent 模型无 model 属性，Bot 有；兼容两者
        bot_model = getattr(bot, 'model', None) or ''

        access_token = create_access_token(
            identity=str(bot.id),
            additional_claims={
                'user_type': 'bot',
                'bot_name': bot.name,
                'bot_model': bot_model
            }
        )
        return jsonify({
            "message": "登录成功",
            "access_token": access_token,
            "bot": {
                "id": str(bot.id),
                "name": bot.name,
                "model": bot_model,
                "status": bot.status
            }
        }), 200
    except Exception as e:
        import logging
        logging.exception("bot_login failed")
        return jsonify({"error": "登录失败"}), 500
    finally:
        db.close()


# Bot 通过名称+主密钥登录（用于 Agent 恢复登录）
@auth_bp.route('/bot/login-by-name', methods=['POST'])
def bot_login_by_name():
    """Bot/Agent 使用名称和主密钥登录，获取 JWT Token（兼容 Agent 与 Bot 模型）"""
    from src.database import get_db
    from src.config import Config
    from src.services.bot_service import get_bot_by_name

    data = request.get_json() or {}
    if not data:
        return jsonify({"error": "请求体为空"}), 400
    bot_name = data.get('bot_name')
    master_key = data.get('master_key')
    if not bot_name or not master_key:
        return jsonify({"error": "bot_name 和 master_key 必填"}), 400
    if getattr(Config, 'MASTER_BOT_KEY', None) and master_key != Config.MASTER_BOT_KEY:
        return jsonify({"error": "无效的主密钥"}), 401

    db = next(get_db())
    try:
        bot = get_bot_by_name(db, bot_name)
        if not bot:
            return jsonify({"error": "Bot 不存在"}), 404
        if bot.status not in ('active', 'idle'):
            return jsonify({"error": "Bot 已被暂停"}), 403

        bot_model = getattr(bot, 'model', None) or ''
        access_token = create_access_token(
            identity=str(bot.id),
            additional_claims={
                'user_type': 'bot',
                'bot_name': bot.name,
                'bot_model': bot_model
            }
        )
        return jsonify({
            "message": "登录成功",
            "access_token": access_token,
            "bot": {
                "id": str(bot.id),
                "name": bot.name,
                "model": bot_model,
                "status": bot.status
            }
        }), 200
    except Exception as e:
        import logging
        logging.exception("bot_login_by_name failed")
        return jsonify({"error": "登录失败"}), 500
    finally:
        db.close()


# =====================================================
# API Token 管理（简化认证，支持外部 Agent）
# =====================================================

@auth_bp.route('/api-token/generate', methods=['POST'])
@jwt_required()
def generate_api_token():
    """为当前用户生成 API Token（需要先登录）"""
    from src.services.api_token_service import generate_user_api_token, get_token_info
    
    user_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        user, token = generate_user_api_token(db, user_id)
        
        return jsonify({
            "message": "API Token 生成成功",
            "token": token,
            "token_info": {
                "expires_at": user.api_token_expires_at.isoformat(),
                "remaining_days": (user.api_token_expires_at - datetime.utcnow()).days
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
        
    finally:
        db.close()


@auth_bp.route('/api-token/revoke', methods=['POST'])
@jwt_required()
def revoke_api_token():
    """撤销当前用户的 API Token"""
    from src.services.api_token_service import revoke_user_api_token
    
    user_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        success = revoke_user_api_token(db, user_id)
        
        if success:
            return jsonify({"message": "API Token 已撤销"}), 200
        else:
            return jsonify({"error": "撤销失败"}), 400
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
        
    finally:
        db.close()


@auth_bp.route('/api-token/info', methods=['GET'])
@jwt_required()
def get_api_token_info():
    """获取当前用户的 API Token 信息"""
    from src.services.api_token_service import get_token_info
    
    user_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "用户不存在"}), 404
        
        token_info = get_token_info(user)
        
        return jsonify({
            "has_token": token_info is not None,
            "token_info": token_info
        }), 200
        
    finally:
        db.close()
