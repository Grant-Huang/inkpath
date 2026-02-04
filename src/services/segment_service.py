"""续写段服务"""
import uuid
import re
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.segment import Segment
from src.models.branch import Branch
from src.models.story import Story
from src.models.bot_branch_membership import BotBranchMembership
from src.services.branch_service import get_next_bot_in_queue
from src.utils.cache import cache_service, cache_key


def count_words(text: str, language: str = 'zh') -> int:
    """
    统计字数/单词数
    
    Args:
        text: 文本内容
        language: 语言类型 'zh' | 'en'
    
    Returns:
        字数或单词数
    """
    if language == 'zh':
        # 中文：统计中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return chinese_chars
    else:
        # 英文：统计单词数
        words = re.findall(r'\b\w+\b', text)
        return len(words)


def validate_segment_length(
    content: str,
    story: Story
) -> Tuple[bool, Optional[str]]:
    """
    验证续写段长度
    
    Returns:
        (是否有效, 错误信息)
    """
    word_count = count_words(content, story.language)
    
    if word_count < story.min_length:
        return False, f"续写内容太短，需要至少{story.min_length}字（中文）或{story.min_length}单词（英文），当前{word_count}"
    
    if word_count > story.max_length:
        return False, f"续写内容太长，最多{story.max_length}字（中文）或{story.max_length}单词（英文），当前{word_count}"
    
    return True, None


def check_turn_order(
    db: Session,
    branch_id: uuid.UUID,
    bot_id: uuid.UUID
) -> Tuple[bool, Optional[str]]:
    """
    检查是否是当前Bot的轮次
    
    ⚠️ 已关闭轮次限制：任何已加入的Bot都可以随时续写
    返回 (True, None) 总是允许
    
    Returns:
        (是否轮到, 错误信息)
    """
    # 轮次逻辑已关闭 - 允许任何已加入的Bot随时写
    return True, None


def create_segment(
    db: Session,
    branch_id: uuid.UUID,
    bot_id: uuid.UUID,
    content: str
) -> Segment:
    """
    创建续写段
    
    Returns:
        Segment对象
    """
    # 验证分支存在
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError("分支不存在")
    
    # 获取故事信息
    story = db.query(Story).filter(Story.id == branch.story_id).first()
    if not story:
        raise ValueError("故事不存在")
    
    # 验证字数
    is_valid, error_msg = validate_segment_length(content, story)
    if not is_valid:
        raise ValueError(error_msg)
    
    # 检查轮次
    is_turn, error_msg = check_turn_order(db, branch_id, bot_id)
    if not is_turn:
        raise ValueError(error_msg)
    
    # 连续性校验（如果启用）
    from src.services.coherence_service import check_coherence
    coherence_passed, coherence_score, coherence_error = check_coherence(
        db, branch_id, content
    )
    if not coherence_passed:
        # 返回422错误，允许Bot修改后重试
        from werkzeug.exceptions import UnprocessableEntity
        raise UnprocessableEntity(description=coherence_error)
    
    # 计算sequence_order
    max_order = db.query(func.max(Segment.sequence_order)).filter(
        Segment.branch_id == branch_id
    ).scalar() or 0
    
    # 创建续写段
    segment = Segment(
        branch_id=branch_id,
        bot_id=bot_id,
        content=content,
        sequence_order=max_order + 1,
        coherence_score=coherence_score if coherence_score > 0 else None  # 存储评分
    )
    
    db.add(segment)
    db.commit()
    db.refresh(segment)
    
    # 清除续写段列表缓存
    cache_service.invalidate_branch(branch_id)
    
    # 更新Bot活动时间
    from src.services.cron_service import update_bot_activity
    try:
        update_bot_activity(db, bot_id)
    except Exception as e:
        # 更新活动时间失败不影响续写提交
        import logging
        logging.warning(f"Failed to update bot activity: {str(e)}")
    
    # 禁用活跃度得分缓存更新，避免 Redis 超时
    # from src.services.activity_service import update_activity_score_cache
    # try:
    #     update_activity_score_cache(db, branch_id)
    # except Exception as e:
    #     logging.warning(f"Failed to update activity score: {str(e)}")
    
    # 禁用自动摘要生成，避免超时
    # from src.services.summary_service import should_generate_summary, generate_summary
    # if should_generate_summary(db, branch_id):
    #     try:
    #         generate_summary(db, branch_id, force=True)
    #     except Exception as e:
    #         logging.warning(f"Failed to generate summary: {str(e)}")
    
    # 禁用通知发送，避免超时
    # next_bot = get_next_bot_in_queue(db, branch_id)
    # if next_bot and next_bot.webhook_url:
    #     from src.utils.notification_queue import enqueue_your_turn_notification
    #     try:
    #         enqueue_your_turn_notification(str(next_bot.id), str(branch_id))
    #     except Exception as e:
    #         logging.warning(f"Failed to enqueue notification: {str(e)}")
    
    return segment


def get_segments_by_branch(
    db: Session,
    branch_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0
) -> Tuple[list[Segment], int]:
    """
    获取分支的续写段列表（带缓存）
    
    Returns:
        (续写段列表, 总数)
    """
    cache_key_str = cache_key("segments:branch", branch_id, limit, offset)
    
    # 尝试从缓存获取
    cached = cache_service.get(cache_key_str)
    if cached:
        segment_ids = [uuid.UUID(sid) for sid in cached.get('ids', [])]
        if segment_ids:
            segments = db.query(Segment).filter(Segment.id.in_(segment_ids)).all()
            segment_dict = {str(s.id): s for s in segments}
            ordered_segments = [segment_dict[sid] for sid in cached['ids'] if sid in segment_dict]
            if ordered_segments:
                return ordered_segments, cached.get('total', len(ordered_segments))
    
    query = db.query(Segment).filter(Segment.branch_id == branch_id)
    
    total = query.count()
    
    segments = query.order_by(Segment.sequence_order.asc()).limit(limit).offset(offset).all()
    
    # 存入缓存
    if segments:
        segment_ids = [str(s.id) for s in segments]
        cache_service.set(cache_key_str, {'ids': segment_ids, 'total': total}, ttl=120)  # 2分钟
    
    return segments, total


def get_segment_by_id(db: Session, segment_id: uuid.UUID) -> Optional[Segment]:
    """根据ID获取续写段"""
    return db.query(Segment).filter(Segment.id == segment_id).first()
