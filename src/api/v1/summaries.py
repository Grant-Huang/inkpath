"""摘要API"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.summary_service import get_branch_summary, generate_summary
from src.services.branch_service import get_branch_by_id, update_branch_summary


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


summaries_bp = Blueprint('summaries', __name__)


@summaries_bp.route('/branches/<branch_id>/summary', methods=['GET'])
def get_branch_summary_endpoint(branch_id):
    """获取分支摘要API"""
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
    
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    db: Session = get_db_session()
    
    try:
        summary_data = get_branch_summary(db, branch_uuid, force_refresh=force_refresh)
        
        return jsonify({
            'status': 'success',
            'data': summary_data
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'获取摘要失败: {str(e)}'
            }
        }), 500


@summaries_bp.route('/branches/<branch_id>/summary', methods=['POST'])
def generate_branch_summary_endpoint(branch_id):
    """强制生成分支摘要API"""
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
        summary = generate_summary(db, branch_uuid, force=True)
        
        if summary is None:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'GENERATION_FAILED',
                    'message': '摘要生成失败，请检查配置或稍后重试'
                }
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': summary
            }
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'生成摘要失败: {str(e)}'
            }
        }), 500


def _can_update_branch_summary(branch, bot_id=None, user_id=None):
    """
    判断当前认证者是否有权更新该分支的进展提要。
    分支拥有者可更新
    """
    if False:  # creator_bot_id removed
        return bot_id is not None and branch.creator_bot_id == bot_id
    story = branch.story
    if not story or story.owner_id is None:
        return False
    if story.owner_type == 'bot' and bot_id and story.owner_id == bot_id:
        return True
    if story.owner_type == 'human' and user_id and story.owner_id == user_id:
        return True
    return False


@summaries_bp.route('/branches/<branch_id>/summary', methods=['PATCH'])
def update_branch_summary_endpoint(branch_id):
    """
    更新分支当前进展提要（仅分支拥有者或故事拥有者可更新）
    分支有 creator_bot_id 时仅该 Bot 可更新；否则由故事拥有者更新。
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

    if not _can_update_branch_summary(
        branch,
        bot_id=bot.id if bot else None,
        user_id=user.id if user else None,
    ):
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'FORBIDDEN',
                'message': '仅分支拥有者或故事拥有者可更新当前进展提要'
            }
        }), 403

    data = request.get_json() or {}
    current_summary = data.get('current_summary')
    if current_summary is None:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: current_summary'
            }
        }), 400

    try:
        branch = update_branch_summary(db, branch_uuid, current_summary)
        return jsonify({
            'status': 'success',
            'data': {
                'branch_id': str(branch.id),
                'current_summary': branch.current_summary,
                'summary_updated_at': (
                    branch.summary_updated_at.isoformat()
                    if branch.summary_updated_at else None
                ),
                'summary_covers_up_to': branch.summary_covers_up_to,
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
                'message': str(e)
            }
        }), 500
