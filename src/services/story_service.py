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
    owner_id: uuid.UUID,
    owner_type: str,  # 'human' | 'bot'
    style_rules: Optional[str] = None,
    starter: Optional[str] = None,
    language: str = 'zh',
    min_length: int = 150,
    max_length: int = 500,
    story_pack_json: Optional[Dict[str, Any]] = None
) -> Story:
    """
    创建故事
    
    Args:
        starter: 开篇内容（第一个片段，由作者手动创作）
    
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
