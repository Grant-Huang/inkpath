"""续写日志 API"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
import uuid

from src.database import get_db
from src.models import SegmentLog, Story, Branch, Segment

logs_bp = Blueprint('logs', __name__, url_prefix='/logs')


def check_auth():
    """检查认证"""
    try:
        verify_jwt_in_request(optional=True)
        return True
    except:
        return False


@logs_bp.route('/', methods=['GET'])
@jwt_required()
def get_logs():
    """获取续写日志列表（需登录）"""
    db: Session = next(get_db())
    
    # 查询参数
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    story_id = request.args.get('story_id')
    author_type = request.args.get('author_type')  # 'human' | 'bot'
    days = request.args.get('days', 7, type=int)  # 默认最近7天
    
    query = db.query(SegmentLog).filter(
        SegmentLog.created_at >= datetime.utcnow() - timedelta(days=days)
    )
    
    if story_id:
        query = query.filter(SegmentLog.story_id == uuid.UUID(story_id))
    
    if author_type:
        query = query.filter(SegmentLog.author_type == author_type)
    
    total = query.count()
    logs = query.order_by(desc(SegmentLog.created_at)).limit(limit).offset((page - 1) * limit).all()
    
    # 获取故事名称映射
    story_ids = set(log.story_id for log in logs)
    story_names = {}
    for sid in story_ids:
        story = db.query(Story).filter(Story.id == sid).first()
        if story:
            story_names[sid] = story.title
    
    return jsonify({
        'status': 'success',
        'data': {
            'logs': [{
                'id': str(log.id),
                'story_id': str(log.story_id),
                'story_title': story_names.get(log.story_id, '未知'),
                'branch_id': str(log.branch_id),
                'segment_id': str(log.segment_id),
                'author_id': str(log.author_id) if log.author_id else None,
                'author_type': log.author_type,
                'author_name': log.author_name,
                'content_length': log.content_length,
                'is_continuation': log.is_continuation,
                'parent_segment_id': str(log.parent_segment_id) if log.parent_segment_id else None,
                'created_at': log.created_at.isoformat() if log.created_at else None,
            } for log in logs],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }
    }), 200


@logs_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """获取日志统计"""
    db: Session = next(get_db())
    
    # 按作者类型统计
    human_count = db.query(SegmentLog).filter(SegmentLog.author_type == 'human').count()
    bot_count = db.query(SegmentLog).filter(SegmentLog.author_type == 'bot').count()
    
    # 最近7天统计
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_logs = db.query(SegmentLog).filter(SegmentLog.created_at >= week_ago).all()
    
    # 按天统计
    daily_stats = {}
    for log in recent_logs:
        date_key = log.created_at.strftime('%Y-%m-%d')
        if date_key not in daily_stats:
            daily_stats[date_key] = {'human': 0, 'bot': 0, 'total': 0}
        daily_stats[date_key][log.author_type] += 1
        daily_stats[date_key]['total'] += 1
    
    return jsonify({
        'status': 'success',
        'data': {
            'total': {
                'human': human_count,
                'bot': bot_count,
                'all': human_count + bot_count
            },
            'last_week': daily_stats
        }
    }), 200
