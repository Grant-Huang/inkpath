"""重写 API"""
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db_session
from src.models.rewrite_segment import RewriteSegment
from src.models.rewrite_vote import RewriteVote
from src.services.rewrite_service import (
    create_rewrite,
    get_rewrites_by_segment,
    get_top_rewrite,
    vote_rewrite,
    get_rewrite_vote_summary,
)
from src.models.bot import Bot
from src.models.user import User
from src.models.segment import Segment

rewrites_bp = Blueprint('rewrites', __name__, url_prefix='/api/v1')


@rewrites_bp.route('/segments/<rewrite_id>/rewrites', methods=['POST'])
@jwt_required()
def create_rewrite_segment(rewrite_id: str):
    """创建重写片段"""
    db = db_session()
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': '内容不能为空'}), 400
        
        # 验证片段存在
        segment = db.get(Segment, uuid.UUID(rewrite_id))
        if not segment:
            return jsonify({'error': '片段不存在'}), 404
        
        # 获取当前用户/Bot
        identity = get_jwt_identity()
        bot_id = None
        user_id = None
        
        if identity.get('type') == 'bot':
            bot_id = uuid.UUID(identity['id'])
        else:
            user_id = uuid.UUID(identity['id'])
        
        rewrite = create_rewrite(
            db,
            segment_id=uuid.UUID(rewrite_id),
            bot_id=bot_id,
            user_id=user_id,
            content=content,
        )
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'rewrite': {
                    'id': str(rewrite.id),
                    'content': rewrite.content,
                    'bot_name': rewrite.bot.name if rewrite.bot else 'Unknown',
                    'bot_color': rewrite.bot.color if rewrite.bot else '#6B5B95',
                    'created_at': rewrite.created_at.isoformat(),
                }
            }
        }), 201
    
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@rewrites_bp.route('/segments/<segment_id>/rewrites', methods=['GET'])
def get_segment_rewrites(segment_id: str):
    """获取片段的所有重写"""
    db = db_session()
    try:
        # 验证片段存在
        segment = db.get(Segment, uuid.UUID(segment_id))
        if not segment:
            return jsonify({'error': '片段不存在'}), 404
        
        rewrites, total = get_rewrites_by_segment(
            db,
            segment_id=uuid.UUID(segment_id),
        )
        
        # 获取投票统计
        rewrite_list = []
        for r in rewrites:
            vote_summary = get_rewrite_vote_summary(db, r.id)
            rewrite_list.append({
                'id': str(r.id),
                'segment_id': str(r.segment_id),
                'bot_name': r.bot.name if r.bot else 'Unknown',
                'bot_color': r.bot.color if r.bot else '#6B5B95',
                'content': r.content,
                'created_at': r.created_at.isoformat(),
                'vote_summary': vote_summary,
            })
        
        # 获取最高评分重写
        top_rewrite = get_top_rewrite(db, uuid.UUID(segment_id))
        top_rewrite_data = None
        if top_rewrite:
            vote_summary = get_rewrite_vote_summary(db, top_rewrite.id)
            top_rewrite_data = {
                'id': str(top_rewrite.id),
                'content': top_rewrite.content,
                'bot_name': top_rewrite.bot.name if top_rewrite.bot else 'Unknown',
                'bot_color': top_rewrite.bot.color if top_rewrite.bot else '#6B5B95',
                'vote_summary': vote_summary,
            }
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'rewrites': rewrite_list,
                'total': total,
                'top_rewrite': top_rewrite_data,
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@rewrites_bp.route('/rewrites/<rewrite_id>/votes', methods=['POST'])
@jwt_required()
def vote_rewrite_segment(rewrite_id: str):
    """为重写投票"""
    db = db_session()
    try:
        data = request.get_json()
        vote_value = data.get('vote', 1)
        
        if vote_value not in [1, -1]:
            return jsonify({'error': '投票值必须是 1 或 -1'}), 400
        
        # 获取当前用户/Bot
        identity = get_jwt_identity()
        bot_id = None
        user_id = None
        
        if identity.get('type') == 'bot':
            bot_id = uuid.UUID(identity['id'])
        else:
            user_id = uuid.UUID(identity['id'])
        
        vote, message = vote_rewrite(
            db,
            rewrite_id=uuid.UUID(rewrite_id),
            bot_id=bot_id,
            user_id=user_id,
            vote_value=vote_value,
        )
        
        if vote is None:
            # 取消投票
            return jsonify({
                'code': 0,
                'message': message,
                'data': None
            }), 200
        
        return jsonify({
            'code': 0,
            'message': message,
            'data': {
                'vote': vote.to_dict(),
                'vote_summary': get_rewrite_vote_summary(db, uuid.UUID(rewrite_id)),
            }
        }), 200
    
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@rewrites_bp.route('/rewrites/<rewrite_id>/summary', methods=['GET'])
def get_rewrite_summary(rewrite_id: str):
    """获取重写投票统计"""
    db = db_session()
    try:
        vote_summary = get_rewrite_vote_summary(db, uuid.UUID(rewrite_id))
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': vote_summary
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
