"""投票API"""
from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.vote_service import (
    create_or_update_vote, get_vote_summary
)
from src.utils.auth import api_token_auth_required, verify_api_token


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


def _token_looks_like_jwt(token: str) -> bool:
    """粗略判断是否为 JWT"""
    if not token or len(token) < 50:
        return False
    return token.count('.') == 2


votes_bp = Blueprint('votes', __name__)


@votes_bp.route('/votes', methods=['POST'])
def create_vote_endpoint():
    """投票API（支持人类 API Token 与 Agent JWT）"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({
            'status': 'error',
            'error': {'code': 'UNAUTHORIZED', 'message': '需要 Authorization: Bearer <token>'}
        }), 401
    token = auth_header[7:].strip()

    voter_id = None
    voter_type = None

    if _token_looks_like_jwt(token):
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
            jwt_claims = get_jwt()
            if jwt_identity and jwt_claims and jwt_claims.get('user_type') in ('bot', 'agent'):
                voter_id = uuid.UUID(str(jwt_identity)) if isinstance(jwt_identity, str) else jwt_identity
                voter_type = 'bot'
        except Exception:
            pass

    if not voter_id:
        user = verify_api_token(token)
        if user:
            voter_id = user.id
            voter_type = 'human'

    if not voter_id or not voter_type:
        return jsonify({
            'status': 'error',
            'error': {'code': 'UNAUTHORIZED', 'message': '无效的认证凭证'}
        }), 401

    if voter_type == 'human':
        from src.utils.rate_limit_helper import check_rate_limit
        rate_limit_result = check_rate_limit('vote:create', user_id=voter_id)
        if rate_limit_result:
            return rate_limit_result

    data = request.get_json()
    if not data:
        return jsonify({
            'status': 'error',
            'error': {'code': 'VALIDATION_ERROR', 'message': '缺少请求体'}
        }), 400

    target_type = data.get('target_type')
    target_id = data.get('target_id')
    vote_value = data.get('vote')
    if not target_type or not target_id or vote_value is None:
        return jsonify({
            'status': 'error',
            'error': {'code': 'VALIDATION_ERROR', 'message': '缺少必需字段: target_type, target_id, vote'}
        }), 400
    if target_type not in ['branch', 'segment']:
        return jsonify({
            'status': 'error',
            'error': {'code': 'VALIDATION_ERROR', 'message': "target_type必须是'branch'或'segment'"}
        }), 400
    if vote_value not in [-1, 1]:
        return jsonify({
            'status': 'error',
            'error': {'code': 'VALIDATION_ERROR', 'message': 'vote必须是-1或1'}
        }), 400
    try:
        target_uuid = uuid.UUID(target_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {'code': 'VALIDATION_ERROR', 'message': '无效的target_id格式'}
        }), 400

    db: Session = get_db_session()
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
                    'created_at': vote.created_at.isoformat() if vote.created_at else None
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
    """获取分支投票汇总API（公开）"""
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
    """获取续写段投票汇总API（公开）"""
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
