"""故事服务"""
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.story import Story
from src.models.branch import Branch
from src.utils.cache import cache_service, cache_key


def create_story(
    db: Session,
    title: str,
    background: str,
    owner_id: Optional[uuid.UUID],
    owner_type: str,  # 'human' | 'bot'
    style_rules: Optional[str] = None,
    starter: Optional[str] = None,
    language: str = 'zh',
    min_length: int = 150,
    max_length: int = 500,
    story_pack_json: Optional[Dict[str, Any]] = None,
    initial_segments: Optional[list[str]] = None  # 初始续写片段列表（3-5个）
) -> Story:
    """
    创建故事
    
    Args:
        starter: 开篇内容（第一个片段，由作者手动创作），会自动创建为第一个 Segment
        initial_segments: 初始续写片段列表（可选，3-5个），会在 starter 之后自动创建
    
    Returns:
        Story对象
    """
    # 验证owner_type
    if owner_type not in ['human', 'bot']:
        raise ValueError("owner_type必须是'human'或'bot'")
    
    # 验证语言
    if language not in ['zh', 'en']:
        raise ValueError("language必须是'zh'或'en'")
    
    # 验证长度范围
    if min_length < 0 or max_length < min_length:
        raise ValueError("min_length和max_length必须有效")
    
    # 创建故事
    story = Story(
        title=title,
        background=background,
        style_rules=style_rules,
        starter=starter,
        language=language,
        min_length=min_length,
        max_length=max_length,
        story_pack_json=story_pack_json,
        owner_id=owner_id,
        owner_type=owner_type,
        status='active'
    )
    
    db.add(story)
    db.commit()
    db.refresh(story)
    
    # 清除故事列表缓存
    cache_service.delete_pattern("stories:list:*")
    
    # 创建主干线分支
    main_branch = Branch(
        story_id=story.id,
        title="主干线",
        description="故事的主干线分支",
        creator_bot_id=owner_id if owner_type == 'bot' else None,
        status='active'
    )
    db.add(main_branch)
    db.commit()
    db.refresh(main_branch)
    
    # 如果创建者是Bot，自动加入主分支
    if owner_type == 'bot':
        from src.models.bot_branch_membership import BotBranchMembership
        membership = BotBranchMembership(
            bot_id=owner_id,
            branch_id=main_branch.id,
            join_order=1
        )
        db.add(membership)
        db.commit()
    
    # 获取所有者名称（用于日志）。Agent/Bot 统一用 Bot 表
    owner_name = 'Unknown'
    if owner_id:
        if owner_type == 'bot':
            from src.models.bot import Bot
            bot = db.query(Bot).filter(Bot.id == owner_id).first()
            owner_name = bot.name if bot else 'Bot'
        else:
            from src.models.user import User
            user = db.query(User).filter(User.id == owner_id).first()
            owner_name = user.name if user else 'User'
    else:
        owner_name = 'Anonymous'
    
    # 如果提供了 starter，自动创建第一个片段（Segment）
    if starter:
        from src.models.segment import Segment
        starter_segment = Segment(
            branch_id=main_branch.id,
            bot_id=owner_id if owner_type == 'bot' else None,
            content=starter,
            sequence_order=1
        )
        db.add(starter_segment)
        db.commit()
        db.refresh(starter_segment)
        
        # 记录日志
        try:
            from src.services.segment_service import log_segment_creation
            log_segment_creation(
                db=db,
                segment_id=starter_segment.id,
                story_id=story.id,
                branch_id=main_branch.id,
                author_id=owner_id,
                author_type=owner_type,
                author_name=owner_name,
                content_length=len(starter) if starter else 0,
                is_continuation='new'
            )
        except Exception as log_error:
            import logging
            logging.warning(f"记录 starter 片段日志失败: {log_error}")
        
        # 如果提供了初始续写片段列表，自动创建这些片段
        if initial_segments and isinstance(initial_segments, list):
            current_order = 1  # starter 已经是 1
            previous_segment_id = starter_segment.id  # 前一个片段的ID
            
            for idx, segment_content in enumerate(initial_segments[:5], start=1):  # 最多5个
                if segment_content and isinstance(segment_content, str):
                    current_order += 1
                    continuation_segment = Segment(
                        branch_id=main_branch.id,
                        bot_id=owner_id if owner_type == 'bot' else None,
                        content=segment_content,
                        sequence_order=current_order,
                        parent_segment=previous_segment_id  # 指向前一个片段
                    )
                    db.add(continuation_segment)
                    db.commit()
                    db.refresh(continuation_segment)
                    
                    # 记录日志
                    try:
                        log_segment_creation(
                            db=db,
                            segment_id=continuation_segment.id,
                            story_id=story.id,
                            branch_id=main_branch.id,
                            author_id=owner_id,
                            author_type=owner_type,
                            author_name=owner_name,
                            content_length=len(segment_content),
                            is_continuation='continuation',
                            parent_segment_id=previous_segment_id
                        )
                    except Exception as log_error:
                        import logging
                        logging.warning(f"记录初始续写片段日志失败: {log_error}")
                    
                    # 更新前一个片段ID，用于下一个片段的 parent_segment
                    previous_segment_id = continuation_segment.id
    
    return story


def get_story_by_id(db: Session, story_id: uuid.UUID) -> Optional[Story]:
    """根据ID获取故事（带缓存）"""
    cache_key_str = cache_key("story", story_id)
    
    # 尝试从缓存获取
    cached = cache_service.get(cache_key_str)
    if cached:
        # 从数据库重新加载以确保关系正确
        story = db.query(Story).filter(Story.id == story_id).first()
        if story:
            return story
    
    # 从数据库获取
    story = db.query(Story).filter(Story.id == story_id).first()
    
    if story:
        # 存入缓存（只缓存基本信息，不缓存关系）
        story_dict = {
            'id': str(story.id),
            'title': story.title,
            'background': story.background,
            'language': story.language,
            'status': story.status,
            'created_at': story.created_at.isoformat() if story.created_at else None,
        }
        cache_service.set(cache_key_str, story_dict, ttl=300)  # 5分钟
    
    return story


def get_stories(
    db: Session,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> list[Story]:
    """获取故事列表（带缓存）"""
    cache_key_str = cache_key("stories:list", status, limit, offset)
    
    # 尝试从缓存获取
    cached = cache_service.get(cache_key_str)
    if cached:
        # 从缓存恢复Story对象（简化版，实际使用需要重新查询）
        story_ids = [uuid.UUID(sid) for sid in cached.get('ids', [])]
        if story_ids:
            stories = db.query(Story).filter(Story.id.in_(story_ids)).all()
            # 保持原有顺序
            story_dict = {str(s.id): s for s in stories}
            return [story_dict[sid] for sid in cached['ids'] if sid in story_dict]
    
    # 从数据库获取
    query = db.query(Story)
    
    if status:
        query = query.filter(Story.status == status)
    
    stories = query.order_by(Story.created_at.desc()).limit(limit).offset(offset).all()
    
    # 存入缓存（只缓存ID列表）
    if stories:
        story_ids = [str(s.id) for s in stories]
        cache_service.set(cache_key_str, {'ids': story_ids}, ttl=180)  # 3分钟
    
    return stories


def update_story_style_rules(
    db: Session,
    story_id: uuid.UUID,
    style_rules: str
) -> Optional[Story]:
    """更新故事规范"""
    story = get_story_by_id(db, story_id)
    
    if not story:
        return None
    
    story.style_rules = style_rules
    db.commit()
    db.refresh(story)
    
    return story


def update_story_metadata(
    db: Session,
    story_id: uuid.UUID,
    background: Optional[str] = None,
    style_rules: Optional[str] = None,
    starter: Optional[str] = None,
    story_pack_json: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None
) -> Optional[Story]:
    """
    更新故事梗概及相关文档（仅故事拥有者可调用）
    可部分更新：只传需要更新的字段。
    
    Args:
        starter: 开篇内容
    """
    story = get_story_by_id(db, story_id)
    if not story:
        return None
    if background is not None:
        story.background = background
    if style_rules is not None:
        story.style_rules = style_rules
    if starter is not None:
        story.starter = starter
    if story_pack_json is not None:
        story.story_pack_json = story_pack_json
    if title is not None:
        story.title = title
    db.commit()
    db.refresh(story)
    cache_service.delete_pattern("story:*")
    cache_service.delete_pattern("stories:list:*")
    return story
