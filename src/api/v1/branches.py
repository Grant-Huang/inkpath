"""分支管理API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.branch_service import (
    create_branch, get_branch_by_id, get_branches_by_story,
    get_branch_tree, join_branch, leave_branch, get_next_bot_in_queue
)
from src.models.segment import Segment
from src.models.bot_branch_membership import BotBranchMembership
from src.utils.rate_limit import create_branch_rate_limit, create_join_branch_rate_limit
from src.utils.auth import bot_auth_required


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


branches_bp = Blueprint('branches', __name__)


def get_auth_user_or_bot():
    """获取认证的用户或Bot"""
    # 尝试Bot认证
    bot = getattr(g, 'current_bot', None)
    user = getattr(g, 'current_user', None)
    
    # 如果没有通过装饰器设置，手动尝试认证
    if not bot and not user:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '', 1)
            
            # 尝试JWT
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
            
            # 尝试Bot API Key
            if not user:
                from src.services.bot_service import authenticate_bot
                db = get_db_session()
                bot = authenticate_bot(db, token)
    
    return bot, user


@branches_bp.route('/stories/<story_id>/branches', methods=['POST'])
def create_branch_endpoint(story_id):
    """创建分支API（需要Bot或用户认证）"""
    # 先进行认证，将bot或user设置到g中
    bot, user = get_auth_user_or_bot()
    
    if bot:
        g.current_bot = bot
    if user:
        g.current_user = user
    
    # 检查速率限制（仅对Bot）
    if bot:
        from src.utils.rate_limit_helper import check_rate_limit
        rate_limit_result = check_rate_limit('branch:create', bot.id, None)
        if rate_limit_result:
            return rate_limit_result
    
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
    
    if not data or 'title' not in data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: title'
            }
        }), 400
    
    title = data.get('title')
    description = data.get('description')
    fork_at_segment_id = data.get('fork_at_segment_id')
    parent_branch_id = data.get('parent_branch_id')
    initial_segment = data.get('initial_segment')  # 创建者的第一段续写
    
    creator_bot_id = bot.id if bot else None
    
    # 处理UUID
    fork_at_segment_uuid = None
    if fork_at_segment_id:
        try:
            fork_at_segment_uuid = uuid.UUID(fork_at_segment_id)
        except ValueError:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '无效的分叉点ID格式'
                }
            }), 400
    
    parent_branch_uuid = None
    if parent_branch_id:
        try:
            parent_branch_uuid = uuid.UUID(parent_branch_id)
        except ValueError:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '无效的父分支ID格式'
                }
            }), 400
    
    db: Session = get_db_session()
    
    try:
        # 如果提供了初始续写段且创建者是Bot，使用带初始段的创建方法
        if initial_segment and creator_bot_id:
            from src.services.branch_service import create_branch_with_initial_segment
            branch, segment = create_branch_with_initial_segment(
                db=db,
                story_id=story_uuid,
                title=title,
                description=description,
                creator_bot_id=creator_bot_id,
                fork_at_segment_id=fork_at_segment_uuid,
                parent_branch_id=parent_branch_uuid,
                initial_segment_content=initial_segment
            )
            
            response_data = {
                'id': str(branch.id),
                'story_id': str(branch.story_id),
                'title': branch.title,
                'description': branch.description,
                'parent_branch_id': str(branch.parent_branch) if branch.parent_branch else None,
                'creator_bot_id': str(branch.creator_bot_id) if branch.creator_bot_id else None,
                'fork_at_segment_id': str(branch.fork_at_segment_id) if branch.fork_at_segment_id else None,
                'created_at': branch.created_at.isoformat() if branch.created_at else None
            }
            
            if segment:
                response_data['initial_segment'] = {
                    'id': str(segment.id),
                    'content': segment.content,
                    'sequence_order': segment.sequence_order
                }
            
            return jsonify({
                'status': 'success',
                'data': response_data
            }), 201
        else:
            # 普通创建分支
            branch = create_branch(
                db=db,
                story_id=story_uuid,
                title=title,
                description=description,
                creator_bot_id=creator_bot_id,
                fork_at_segment_id=fork_at_segment_uuid,
                parent_branch_id=parent_branch_uuid
            )
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': str(branch.id),
                    'story_id': str(branch.story_id),
                    'title': branch.title,
                    'description': branch.description,
                    'parent_branch_id': str(branch.parent_branch) if branch.parent_branch else None,
                    'creator_bot_id': str(branch.creator_bot_id) if branch.creator_bot_id else None,
                    'fork_at_segment_id': str(branch.fork_at_segment_id) if branch.fork_at_segment_id else None,
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


@branches_bp.route('/branches/<branch_id>', methods=['GET'])
def get_branch_detail(branch_id):
    """获取分支详情API"""
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
    branch = get_branch_by_id(db, branch_uuid)
    
    if not branch:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': '分支不存在'
            }
        }), 404
    
    # 获取统计信息
    segments_count = db.query(Segment).filter(Segment.branch_id == branch.id).count()
    active_bots_count = db.query(BotBranchMembership).filter(
        BotBranchMembership.branch_id == branch.id
    ).count()
    
    # 获取前10个 segment（预览用）
    from src.services.segment_service import get_segments_by_branch
    preview_segments, _ = get_segments_by_branch(
        db=db, branch_id=branch_uuid, limit=10, offset=0
    )
    
    return jsonify({
        'status': 'success',
        'data': {
            'id': str(branch.id),
            'story_id': str(branch.story_id),
            'title': branch.title,
            'description': branch.description,
            'parent_branch_id': str(branch.parent_branch) if branch.parent_branch else None,
            'creator_bot_id': str(branch.creator_bot_id) if branch.creator_bot_id else None,
            'fork_at_segment_id': str(branch.fork_at_segment_id) if branch.fork_at_segment_id else None,
            'status': branch.status,
            'segments_count': segments_count,
            'active_bots_count': active_bots_count,
            'created_at': branch.created_at.isoformat() if branch.created_at else None,
            'segments_preview': [
                {
                    'id': str(segment.id),
                    'content': segment.content[:200] + '...' if len(segment.content) > 200 else segment.content,
                    'sequence_order': segment.sequence_order,
                    'bot_name': segment.bot.name if segment.bot else None,
                    'bot_id': str(segment.bot_id) if segment.bot_id else None,
                }
                for segment in preview_segments
            ]
        }
    }), 200


@branches_bp.route('/branches/<branch_id>/participants', methods=['GET'])
def get_branch_participants(branch_id):
    """获取分支参与者列表API
    
    返回所有参与该分支的 Bot 和人类用户
    """
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
        # 检查分支是否存在
        branch = get_branch_by_id(db, branch_uuid)
        if not branch:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'NOT_FOUND',
                    'message': '分支不存在'
                }
            }), 404
        
        participants = []
        
        # 获取 Bot 参与者
        from src.models.bot import Bot
        bot_memberships = db.query(BotBranchMembership).filter(
            BotBranchMembership.branch_id == branch_uuid
        ).all()
        
        for membership in bot_memberships:
            try:
                bot = db.query(Bot).filter(Bot.id == membership.bot_id).first()
                if bot:
                    participants.append({
                        'id': str(bot.id),
                        'name': bot.name,
                        'type': 'bot',
                        'role': membership.role or 'participant',
                        'model': bot.model,
                        'joined_at': membership.joined_at.isoformat() if membership.joined_at else None,
                        'join_order': membership.join_order
                    })
            except Exception as e:
                current_app.logger.error(f"获取 Bot 信息失败: {e}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'participants': participants,
                'count': len(participants)
            }
        }), 200
    
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取参与者失败: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'获取参与者失败: {str(e)}'
            }
        }), 500


@branches_bp.route('/stories/<story_id>/branches', methods=['GET'])
def list_branches(story_id):
    """获取故事的所有分支API"""
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
    
    limit = int(request.args.get('limit', 6))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'activity')
    include_all = request.args.get('include_all', 'false').lower() == 'true'
    
    db: Session = get_db_session()
    branches, total = get_branches_by_story(
        db=db,
        story_id=story_uuid,
        limit=limit,
        offset=offset,
        sort=sort,
        include_all=include_all
    )
    
    # 构建响应数据
    from src.services.activity_service import get_activity_score_cached
    branches_data = []
    for branch in branches:
        segments_count = db.query(Segment).filter(Segment.branch_id == branch.id).count()
        active_bots_count = db.query(BotBranchMembership).filter(
            BotBranchMembership.branch_id == branch.id
        ).count()
        
        # 获取活跃度得分
        try:
            activity_score = get_activity_score_cached(db, branch.id)
        except Exception as e:
            activity_score = 0.0
        
        branches_data.append({
            'id': str(branch.id),
            'title': branch.title,
            'description': branch.description,
            'parent_branch_id': str(branch.parent_branch) if branch.parent_branch else None,
            'creator_bot_id': str(branch.creator_bot_id) if branch.creator_bot_id else None,
            'segments_count': segments_count,
            'active_bots_count': active_bots_count,
            'activity_score': activity_score,
            'created_at': branch.created_at.isoformat() if branch.created_at else None
        })
    
    # 如果按活跃度排序，对结果进行排序
    if sort == 'activity':
        branches_data.sort(key=lambda x: x['activity_score'], reverse=True)
    
    return jsonify({
        'status': 'success',
        'data': {
            'branches': branches_data,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total,
                'has_more': (offset + len(branches)) < total
            }
        }
    }), 200


@branches_bp.route('/stories/<story_id>/branches/tree', methods=['GET'])
def get_branch_tree_endpoint(story_id):
    """获取分支树API"""
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
    tree = get_branch_tree(db, story_uuid)
    
    return jsonify({
        'status': 'success',
        'data': {
            'tree': tree
        }
    }), 200


@branches_bp.route('/branches/<branch_id>/join', methods=['POST'])
@bot_auth_required
def join_branch_endpoint(branch_id):
    """Bot加入分支API"""
    bot = g.current_bot
    
    # 检查速率限制
    from src.utils.rate_limit_helper import check_rate_limit
    rate_limit_result = check_rate_limit('branch:join', bot_id=bot.id)
    if rate_limit_result:
        return rate_limit_result
    
    # 只有Bot可以加入分支（用于续写）
    if not bot:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'FORBIDDEN',
                'message': '只有Bot可以加入分支'
            }
        }), 403
    
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
        membership = join_branch(db, branch_uuid, bot.id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'bot_id': str(membership.bot_id),
                'branch_id': str(membership.branch_id),
                'join_order': membership.join_order,
                'joined_at': membership.joined_at.isoformat() if membership.joined_at else None
            }
        }), 200
    
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
                'message': f'加入分支失败: {str(e)}'
            }
        }), 500


@branches_bp.route('/branches/<branch_id>/leave', methods=['POST'])
def leave_branch_endpoint(branch_id):
    """Bot离开分支API"""
    bot, user = get_auth_user_or_bot()
    
    # 只有Bot可以离开分支
    if not bot:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'FORBIDDEN',
                'message': '只有Bot可以离开分支'
            }
        }), 403
    
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
    
    success = leave_branch(db, branch_uuid, bot.id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Bot未加入该分支'
            }
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': '已离开分支'
    }), 200


@branches_bp.route('/branches/<branch_id>/next-bot', methods=['GET'])
def get_next_bot_endpoint(branch_id):
    """获取轮次队列中的下一个Bot API"""
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
    next_bot = get_next_bot_in_queue(db, branch_uuid)
    
    if not next_bot:
        return jsonify({
            'status': 'success',
            'data': {
                'bot': None,
                'message': '没有可用的Bot'
            }
        }), 200
    
    return jsonify({
        'status': 'success',
        'data': {
            'bot': {
                'id': str(next_bot.id),
                'name': next_bot.name,
                'model': next_bot.model
            }
        }
    }), 200
