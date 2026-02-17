"""Dashboard 统计 API：故事维度、作者维度"""
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from src.database import get_db
from src.models.story import Story
from src.models.branch import Branch
from src.models.segment import Segment
from src.models.bot import Bot
from src.models.vote import Vote
from src.models.user import User


def get_db_session():
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


def admin_required(fn):
    from flask_jwt_extended import verify_jwt_in_request
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if get_jwt().get('user_type') != 'admin':
            return jsonify({'status': 'error', 'error': {'code': 'FORBIDDEN', 'message': '需要管理员权限'}}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    返回 Dashboard 所需统计（公开访问，无需登录）：
    - 故事：总数、最活跃、点赞最多、续写最多
    - 作者：总人数(人类/Bot)、近一周活跃、创作Top10、被点赞Top10
    """
    db: Session = get_db_session()
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # ----- 故事维度 -----
    stories_total = db.query(Story).filter(Story.status == 'active').count()

    # 各故事的续写段总数（用于“续写最多”和“最活跃”）
    branch_segment_count = (
        db.query(Branch.story_id, func.count(Segment.id).label('seg_count'))
        .join(Segment, Segment.branch_id == Branch.id)
        .group_by(Branch.story_id)
    ).subquery()
    story_segment_total = (
        db.query(
            branch_segment_count.c.story_id,
            func.sum(branch_segment_count.c.seg_count).label('total'),
        )
        .group_by(branch_segment_count.c.story_id)
    ).subquery()

    # 最活跃：按该故事下总续写段数排序，取第一
    most_active_story = (
        db.query(Story)
        .join(story_segment_total, story_segment_total.c.story_id == Story.id)
        .order_by(desc(story_segment_total.c.total))
        .first()
    )
    # 续写最多：同逻辑，取第一（可与最活跃一致或按分支维度）
    most_continued_story = most_active_story

    # 点赞最多故事：按 segment 投票汇总到 story
    segment_scores = (
        db.query(Vote.target_id, func.sum(Vote.vote * Vote.effective_weight).label('score'))
        .filter(Vote.target_type == 'segment')
        .group_by(Vote.target_id)
    ).all()
    seg_id_to_score = {str(sid): float(sc) for sid, sc in segment_scores}
    story_scores = {}
    if seg_id_to_score:
        segs = db.query(Segment.id, Segment.branch_id).filter(
            Segment.id.in_([uuid.UUID(sid) for sid in seg_id_to_score.keys()])
        ).all()
        branch_to_story = {str(b.id): str(b.story_id) for b in db.query(Branch.id, Branch.story_id).all()}
        for seg_id, branch_id in segs:
            sid, bid = str(seg_id), str(branch_id)
            story_id = branch_to_story.get(bid)
            if story_id:
                story_scores[story_id] = story_scores.get(story_id, 0) + seg_id_to_score.get(sid, 0)
    most_upvoted_story = None
    if story_scores:
        top_story_id = max(story_scores, key=story_scores.get)
        most_upvoted_story = db.query(Story).filter(Story.id == uuid.UUID(top_story_id)).first()

    def _story_brief(s):
        if not s:
            return None
        return {'id': str(s.id), 'title': s.title}

    # ----- 作者维度：人类用 User 表，Bot 用 Bot 表 -----
    authors_human_total = db.query(User).count()
    authors_bot_total = db.query(Bot).count()
    authors_total = authors_human_total + authors_bot_total

    # 近一周活跃：有续写段的 bot_id / 或人类（人类暂无续写，仅 Bot 有 segment）
    active_bots_week = (
        db.query(Segment.bot_id)
        .filter(Segment.created_at >= week_ago, Segment.bot_id.isnot(None))
        .distinct()
        .count()
    )
    # 人类近一周活跃：若有 human_branch_membership 或 vote 可算，此处简化为 0
    active_humans_week = 0

    # 创作最多作者 Top10：按 bot 的 segment 数
    seg_per_bot = (
        db.query(Segment.bot_id, func.count(Segment.id).label('cnt'))
        .filter(Segment.bot_id.isnot(None))
        .group_by(Segment.bot_id)
    ).subquery()
    top_creators = (
        db.query(Bot, seg_per_bot.c.cnt)
        .join(seg_per_bot, seg_per_bot.c.bot_id == Bot.id)
        .order_by(desc(seg_per_bot.c.cnt))
        .limit(10)
        .all()
    )
    top_creators_list = [
        {'id': str(b.id), 'name': b.name, 'type': 'bot', 'segments_count': int(c)}
        for b, c in top_creators
    ]

    # 被点赞最多作者 Top10：按 segment 的 bot_id 聚合该 segment 收到的投票分
    seg_scores = (
        db.query(
            Vote.target_id,
            func.sum(Vote.vote * Vote.effective_weight).label('score'),
        )
        .filter(Vote.target_type == 'segment')
        .group_by(Vote.target_id)
    ).subquery()
    bot_received = (
        db.query(Segment.bot_id, func.sum(seg_scores.c.score).label('total'))
        .join(seg_scores, seg_scores.c.target_id == Segment.id)
        .filter(Segment.bot_id.isnot(None))
        .group_by(Segment.bot_id)
    ).subquery()
    top_upvoted = (
        db.query(Bot, bot_received.c.total)
        .join(bot_received, bot_received.c.bot_id == Bot.id)
        .order_by(desc(bot_received.c.total))
        .limit(10)
        .all()
    )
    top_upvoted_list = [
        {'id': str(b.id), 'name': b.name, 'type': 'bot', 'vote_score': float(t) if t else 0}
        for b, t in top_upvoted
    ]

    return jsonify({
        'status': 'success',
        'data': {
            'stories': {
                'total': stories_total,
                'most_active': _story_brief(most_active_story),
                'most_upvoted': _story_brief(most_upvoted_story),
                'most_continued': _story_brief(most_continued_story),
            },
            'authors': {
                'total': authors_total,
                'human_total': authors_human_total,
                'bot_total': authors_bot_total,
                'active_last_week_human': active_humans_week,
                'active_last_week_bot': active_bots_week,
                'top_creators': top_creators_list,
                'top_upvoted': top_upvoted_list,
            },
        },
    }), 200
