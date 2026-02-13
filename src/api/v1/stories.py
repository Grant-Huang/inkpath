"""故事管理API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.story_service import (
    create_story, get_story_by_id, get_stories,
    update_story_style_rules, update_story_metadata
)
from src.utils.auth import bot_auth_required, user_auth_required
from src.models.branch import Branch


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


stories_bp = Blueprint('stories', __name__)


@stories_bp.route('/stories', methods=['POST'])
@bot_auth_required
def create_story_endpoint():
    """创建故事API（需要Bot或用户认证）"""
    # 检查是否有Bot认证
    bot = getattr(g, 'current_bot', None)
    user = getattr(g, 'current_user', None)
    
    if not bot and not user:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '需要认证'
            }
        }), 401
    
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
    language = data.get('language', 'zh')
    min_length = data.get('min_length', 150)
    max_length = data.get('max_length', 500)
    story_pack = data.get('story_pack')
    
    # 确定owner
    if bot:
        owner_id = bot.id
        owner_type = 'bot'
    else:
        owner_id = user.id
        owner_type = 'human'
    
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
            'sources': story_pack.get('sources')
        }
    
    db: Session = get_db_session()
    
    try:
        story = create_story(
            db=db,
            title=title,
            background=background,
            owner_id=owner_id,
            owner_type=owner_type,
            style_rules=style_rules,
            language=language,
            min_length=min_length,
            max_length=max_length,
            story_pack_json=story_pack_json
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': str(story.id),
                'title': story.title,
                'background': story.background,
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
    """获取故事列表API"""
    status = request.args.get('status', 'active')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    db: Session = get_db_session()
    stories = get_stories(db, status=status, limit=limit, offset=offset)
    
    from src.models.branch import Branch
    from src.models.bot_branch_membership import BotBranchMembership
    
    story_list = []
    for story in stories:
        # 获取分支数量
        branches_count = db.query(Branch).filter(Branch.story_id == story.id).count()
        
        # 获取参与该故事所有分支的唯一 Bot 总数
        bots_count = db.query(BotBranchMembership.bot_id).join(
            Branch, BotBranchMembership.branch_id == Branch.id
        ).filter(Branch.story_id == story.id).distinct().count()
        
        story_list.append({
            'id': str(story.id),
            'title': story.title,
            'background': story.background[:100] + '...' if len(story.background) > 100 else story.background,
            'language': story.language,
            'owner_type': story.owner_type,
            'status': story.status,  # 添加status字段
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
    """获取故事详情API"""
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
    
    return jsonify({
        'status': 'success',
        'data': {
            'id': str(story.id),
            'title': story.title,
            'background': story.background,
            'style_rules': story.style_rules,
            'language': story.language,
            'min_length': story.min_length,
            'max_length': story.max_length,
            'owner_id': str(story.owner_id),
            'owner_type': story.owner_type,
            'status': story.status,
            'branches_count': branches_count,
            'created_at': story.created_at.isoformat() if story.created_at else None,
            'updated_at': story.updated_at.isoformat() if story.updated_at else None
        }
    }), 200


@stories_bp.route('/stories/<story_id>/style-rules', methods=['PATCH'])
@bot_auth_required
def update_story_style_rules_endpoint(story_id):
    """更新故事规范API（需要Bot或用户认证）"""
    # 检查是否有Bot或用户认证
    bot = getattr(g, 'current_bot', None)
    user = getattr(g, 'current_user', None)
    
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
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的故事ID格式'
            }
        }), 400
    
    data = request.get_json()
    
    if not data or 'style_rules' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: style_rules'
            }
        }), 400
    
    style_rules = data.get('style_rules')
    
    db: Session = get_db_session()
    story = update_story_style_rules(db, story_uuid, style_rules)
    
    if not story:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': '故事不存在'
            }
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': {
            'id': str(story.id),
            'style_rules': story.style_rules,
            'updated_at': story.updated_at.isoformat() if story.updated_at else None
        }
    }), 200


def _is_story_owner(story, bot_id=None, user_id=None):
    """判断当前认证者是否为故事拥有者"""
    if story.owner_id is None:
        return False
    if story.owner_type == 'bot' and bot_id and story.owner_id == bot_id:
        return True
    if story.owner_type == 'human' and user_id and story.owner_id == user_id:
        return True
    return False


@stories_bp.route('/stories/<story_id>', methods=['PATCH'])
def update_story_metadata_endpoint(story_id):
    """
    更新故事梗概及相关文档（仅故事拥有者）
    支持更新：title, background, style_rules, story_pack。
    需要 Bearer Token（Bot API Key 或用户 JWT）。
    """
    from src.api.v1.branches import get_auth_user_or_bot
    bot, user = get_auth_user_or_bot()
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

    if not _is_story_owner(story, bot_id=bot.id if bot else None,
                           user_id=user.id if user else None):
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'FORBIDDEN',
                'message': '仅故事拥有者可更新故事梗概与相关文档'
            }
        }), 403

    data = request.get_json() or {}
    background = data.get('background')
    style_rules = data.get('style_rules')
    story_pack = data.get('story_pack')
    title = data.get('title')

    if background is None and style_rules is None and story_pack is None and title is None:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '请提供至少一个字段: title, background, style_rules, story_pack'
            }
        }), 400

    story_pack_json = None
    if story_pack is not None:
        story_pack_json = {
            'meta': story_pack.get('meta'),
            'evidence_pack': story_pack.get('evidence_pack'),
            'stance_pack': story_pack.get('stance_pack'),
            'cast': story_pack.get('cast'),
            'plot_outline': story_pack.get('plot_outline'),
            'constraints': story_pack.get('constraints'),
            'sources': story_pack.get('sources'),
        }

    story = update_story_metadata(
        db=db,
        story_id=story_uuid,
        background=background,
        style_rules=style_rules,
        story_pack_json=story_pack_json,
        title=title,
    )
    return jsonify({
        'status': 'success',
        'data': {
            'id': str(story.id),
            'title': story.title,
            'background': story.background,
            'style_rules': story.style_rules,
            'story_pack': story.story_pack_json,
            'updated_at': story.updated_at.isoformat() if story.updated_at else None,
        }
    }), 200
