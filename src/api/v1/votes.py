"""投票API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.vote_service import (
    create_or_update_vote, get_vote_summary, calculate_score
)
from src.utils.rate_limit import create_vote_rate_limit
# 投票API支持人类和Bot两种认证，使用手动检查


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


votes_bp = Blueprint('votes', __name__)


@votes_bp.route('/votes', methods=['POST'])
def create_vote_endpoint():
    """投票API（支持人类和Bot）"""
    # 尝试认证
    user = None
    bot = None
    auth_header = request.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '', 1)
        
        # 先尝试JWT验证（人类）
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
    
    # 设置到g中
    if user:
        g.current_user = user
    if bot:
        g.current_bot = bot
    
    # 检查速率限制
    from src.utils.rate_limit_helper import check_rate_limit
    if bot:
        rate_limit_result = check_rate_limit('vote:create', bot_id=bot.id)
    elif user:
        rate_limit_result = check_rate_limit('vote:create', user_id=user.id)
    else:
        rate_limit_result = None
    
    if rate_limit_result:
        return rate_limit_result
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少请求体'
            }
        }), 400
    
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    vote_value = data.get('vote')
    
    # 验证必需字段
    if not target_type or not target_id or vote_value is None:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '缺少必需字段: target_type, target_id, vote'
            }
        }), 400
    
    # 验证target_type
    if target_type not in ['branch', 'segment']:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': "target_type必须是'branch'或'segment'"
            }
        }), 400
    
    # 验证vote值
    if vote_value not in [-1, 1]:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'vote必须是-1或1'
            }
        }), 400
    
    try:
        target_uuid = uuid.UUID(target_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的target_id格式'
            }
        }), 400
    
    db: Session = get_db_session()
    
    # 确定投票者
    if user:
        voter_id = user.id
        voter_type = 'human'
    else:
        voter_id = bot.id
        voter_type = 'bot'
    
    try:
        vote, new_score = create_or_update_vote(
            db=db,
            voter_id=voter_id,
            voter_type=voter_type,
            target_type=target_type,
            target_id=target_uuid,
            vote=vote_value
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'vote': {
                    'id': str(vote.id),
                    'voter_id': str(vote.voter_id),
                    'voter_type': vote.voter_type,
                    'target_type': vote.target_type,
                    'target_id': str(vote.target_id),
                    'vote': vote.vote,
                    'effective_weight': float(vote.effective_weight),
                    'created_at': vote.created_at.isoformat() if vote.created_at else None,
                    'updated_at': vote.updated_at.isoformat() if vote.updated_at else None
                },
                'new_score': new_score
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
                'message': f'投票失败: {str(e)}'
            }
        }), 500


@votes_bp.route('/branches/<branch_id>/votes/summary', methods=['GET'])
def get_branch_vote_summary(branch_id):
    """获取分支投票汇总API"""
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
        summary = get_vote_summary(db, 'branch', branch_uuid)
        
        return jsonify({
            'status': 'success',
            'data': summary
        }), 200
    
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'获取投票汇总失败: {str(e)}'
            }
        }), 500


@votes_bp.route('/segments/<segment_id>/votes/summary', methods=['GET'])
def get_segment_vote_summary(segment_id):
    """获取续写段投票汇总API"""
    try:
        segment_uuid = uuid.UUID(segment_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的续写段ID格式'
            }
        }), 400
    
    db: Session = get_db_session()
    
    try:
        summary = get_vote_summary(db, 'segment', segment_uuid)
        
        return jsonify({
            'status': 'success',
            'data': summary
        }), 200
    
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'获取投票汇总失败: {str(e)}'
            }
        }), 500
