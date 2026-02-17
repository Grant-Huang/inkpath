"""故事管理API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.story_service import (
    create_story, get_story_by_id, get_stories,
    update_story_style_rules, update_story_metadata
)
from src.utils.auth import api_token_auth_required
from src.models.branch import Branch
from src.models.bot_branch_membership import BotBranchMembership


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


stories_bp = Blueprint('stories', __name__)


@stories_bp.route('/stories', methods=['POST'])
def create_story_endpoint():
    """创建故事API（支持 API Token 或 JWT 认证）"""
    # 检查认证方式
    bot_id = None
    user = None
    user_type = None
    
    # 尝试 JWT 认证
    try:
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, get_jwt
        verify_jwt_in_request(optional=True)
        jwt_identity = get_jwt_identity()
        jwt_claims = get_jwt()
        
        # 检查 user_type
        if jwt_claims and jwt_claims.get('user_type') == 'agent':
            # Bot 认证
            bot_id = jwt_identity
            user_type = 'bot'
        elif jwt_claims and jwt_claims.get('user_type') == 'admin':
            # Admin 用户
            user_type = 'admin'
        elif jwt_identity:
            # 其他 JWT 用户
            user_type = 'human'
    except:
        pass
    
    # 如果没有 JWT，尝试 API Token 认证 (人类用户)
    if not bot_id and not user_type:
        from src.utils.auth import verify_api_token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            user = verify_api_token(token)
            if user:
                user_type = user.get('user_type', 'human')
            else:
                return jsonify({'status': 'error', 'error': {'code': 'UNAUTHORIZED', 'message': '无效的认证凭证'}}), 401
        else:
            return jsonify({'status': 'error', 'error': {'code': 'UNAUTHORIZED', 'message': '需要认证'}}), 401
    
    data = request.get_json()
    
    # 验证必需字段
    if not data or 'title' not in data or 'background' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: title, background'
            }
        }), 400
    
    title = data.get('title')
    background = data.get('background')
    style_rules = data.get('style_rules')
    starter = data.get('starter')
    language = data.get('language', 'zh')
    min_length = data.get('min_length', 150)
    max_length = data.get('max_length', 500)
    story_pack = data.get('story_pack')
    initial_segments = data.get('initial_segments')  # 初始续写片段列表（可选，3-5个）
    
    # 处理故事包
    story_pack_json = None
    if story_pack:
        story_pack_json = {
            'meta': story_pack.get('meta'),
            'evidence_pack': story_pack.get('evidence_pack'),
            'stance_pack': story_pack.get('stance_pack'),
            'cast': story_pack.get('cast'),
            'plot_outline': story_pack.get('plot_outline'),
            'constraints': story_pack.get('constraints'),
            'sources': story_pack.get('sources'),
            'starter': story_pack.get('starter')
        }
        if starter is None and story_pack_json.get('starter'):
            starter = story_pack_json.get('starter')
    
    db: Session = get_db_session()
    
    try:
        # 确定所有者
        if bot_id:
            # Bot 创建故事，自动成为所有者
            from src.models.agent import Agent
            bot = db.query(Agent).filter(Agent.id == bot_id).first()
            owner_id = bot_id
            owner_type = 'bot'
            owner_name = bot.name if bot else 'Unknown Bot'
        elif user_type == 'admin':
            # Admin 用户创建 - 不设置 owner_id（允许为 NULL）
            owner_id = None
            owner_type = 'human'
            owner_name = 'Admin'
        elif user:
            # 人类用户创建
            owner_id = user.id
            owner_type = 'human'
            owner_name = user.username or user.email or 'Anonymous'
        else:
            # 匿名用户
            owner_id = None
            owner_type = 'human'
            owner_name = 'Anonymous'
        
        story = create_story(
            db=db,
            title=title,
            background=background,
            owner_id=owner_id,
            owner_type=owner_type,
            style_rules=style_rules,
            starter=starter,
            language=language,
            min_length=min_length,
            max_length=max_length,
            story_pack_json=story_pack_json,
            initial_segments=initial_segments
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': str(story.id),
                'title': story.title,
                'background': story.background,
                'starter': story.starter,
                'style_rules': story.style_rules,
                'language': story.language,
                'min_length': story.min_length,
                'max_length': story.max_length,
                'owner_id': str(story.owner_id),
                'owner_type': story.owner_type,
                'created_at': story.created_at.isoformat() if story.created_at else None
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
                'message': f'创建故事失败: {str(e)}'
            }
        }), 500


@stories_bp.route('/stories', methods=['GET'])
def list_stories():
    """获取故事列表API（公开，无需认证）"""
    status = request.args.get('status', 'active')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    db: Session = get_db_session()
    stories = get_stories(db, status=status, limit=limit, offset=offset)
    
    story_list = []
    for story in stories:
        try:
            branches_count = db.query(Branch).filter(Branch.story_id == story.id).count()
            bots_count = 0
            try:
                bots_count = db.query(BotBranchMembership.bot_id).join(
                    Branch, BotBranchMembership.branch_id == Branch.id
                ).filter(Branch.story_id == story.id).distinct().count()
            except Exception as e:
                logger.warning(f"获取 bots_count 失败: {e}")
        except Exception as e:
            logger.warning(f"获取 branches_count 失败: {e}")
            branches_count = 0
        
        story_list.append({
            'id': str(story.id),
            'title': story.title,
            'background': story.background[:100] + '...' if len(story.background) > 100 else story.background,
            'language': story.language,
            'owner_type': story.owner_type,
            'status': story.status,
            'branches_count': branches_count,
            'bots_count': bots_count,
            'created_at': story.created_at.isoformat() if story.created_at else None
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            'stories': story_list,
            'count': len(stories)
        }
    }), 200


@stories_bp.route('/stories/<story_id>', methods=['GET'])
def get_story_detail(story_id):
    """获取故事详情API（公开）"""
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
    story = get_story_by_id(db, story_uuid)
    
    if not story:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': '故事不存在'
            }
        }), 404
    
    # 获取分支数量
    branches_count = db.query(Branch).filter(Branch.story_id == story.id).count()
    
    # 获取参与该故事所有分支的唯一 Bot 总数
    bots_count = db.query(BotBranchMembership.bot_id).join(
        Branch, BotBranchMembership.branch_id == Branch.id
    ).filter(Branch.story_id == story.id).distinct().count()
    
    return jsonify({
        'status': 'success',
        'data': {
            'id': str(story.id),
            'title': story.title,
            'background': story.background,
            'starter': story.starter,
            'style_rules': story.style_rules,
            'language': story.language,
            'min_length': story.min_length,
            'max_length': story.max_length,
            'owner_type': story.owner_type,
            'status': story.status,
            'branches_count': branches_count,
            'bots_count': bots_count,
            'created_at': story.created_at.isoformat() if story.created_at else None
        }
    }), 200


@stories_bp.route('/stories/<story_id>/branches', methods=['POST'])
@api_token_auth_required
def create_branch(story_id):
    """创建分支API"""
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
    
    user = g.current_user
    
    data = request.get_json()
    title = data.get('title', '')
    parent_branch_id = data.get('parent_branch_id')  # 可选，复制分支
    starter = data.get('starter', '')  # 分支开篇内容
    
    db: Session = get_db_session()
    
    try:
        branch = create_branch(
            db=db,
            story_id=story_uuid,
            parent_branch_id=parent_branch_id and uuid.UUID(parent_branch_id),
            starter=starter,
            owner_id=user.id,
            title=title
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': str(branch.id),
                'title': branch.title,
                'story_id': str(story_id),
                'created_at': branch.created_at.isoformat() if branch.created_at else None
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
                'message': f'创建分支失败: {str(e)}'
            }
        }), 500


@stories_bp.route('/stories/<story_id>/branches', methods=['GET'])
def list_branches(story_id):
    """获取故事的所有分支（公开）"""
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
    
    from src.services.branch_service import get_branches_by_story
    from src.services.segment_service import count_segments_by_branch
    
    db: Session = get_db_session()
    branches, _ = get_branches_by_story(db, story_uuid)
    
    # 为每个分支添加统计信息
    branch_data = []
    for b in branches:
        segments_count = count_segments_by_branch(db, b.id)
        # 简化：bots_count 从分支关联表获取
        branch_data.append({
            'id': str(b.id),
            'title': b.title,
            'parent_branch_id': str(b.parent_branch) if b.parent_branch else None,
            'created_at': b.created_at.isoformat() if b.created_at else None,
            'segments_count': segments_count,
            'bots_count': 1,  # 简化：至少有一个 Bot（创建者）
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            'branches': branch_data
        }
    }), 200
