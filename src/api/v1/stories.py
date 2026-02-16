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
@api_token_auth_required
def create_story_endpoint():
    """创建故事API（支持 API Token 认证）"""
    user = g.current_user
    
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
        story = create_story(
            db=db,
            title=title,
            background=background,
            owner_id=user.id,
            owner_type='human',
            style_rules=style_rules,
            starter=starter,
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
        branches_count = db.query(Branch).filter(Branch.story_id == story.id).count()
        bots_count = db.query(BotBranchMembership.bot_id).join(
            Branch, BotBranchMembership.branch_id == Branch.id
        ).filter(Branch.story_id == story.id).distinct().count()
        
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
    
    db: Session = get_db_session()
    branches = get_branches_by_story(db, story_uuid)
    
    return jsonify({
        'status': 'success',
        'data': {
            'branches': [{
                'id': str(b.id),
                'title': b.title,
                'parent_branch_id': str(b.parent_branch_id) if b.parent_branch_id else None,
                'created_at': b.created_at.isoformat() if b.created_at else None
            } for b in branches]
        }
    }), 200
