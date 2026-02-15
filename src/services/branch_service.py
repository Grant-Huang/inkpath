"""分支服务"""
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.models.branch import Branch
from src.models.story import Story
from src.models.segment import Segment
from src.models.bot_branch_membership import BotBranchMembership
from src.models.bot import Bot
from src.utils.cache import cache_service, cache_key


def create_branch(
    db: Session,
    story_id: uuid.UUID,
    title: str,
    description: Optional[str],
    creator_bot_id: Optional[uuid.UUID] = None,
    fork_at_segment_id: Optional[uuid.UUID] = None,
    parent_branch_id: Optional[uuid.UUID] = None
) -> Branch:
    """
    创建分支
    
    Returns:
        Branch对象
    """
    # 验证故事存在
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise ValueError("故事不存在")
    
    # 如果指定了分叉点，验证续写段存在
    if fork_at_segment_id:
        segment = db.query(Segment).filter(Segment.id == fork_at_segment_id).first()
        if not segment:
            raise ValueError("分叉点续写段不存在")
        # 确保分叉点属于该故事的分支
        if segment.branch_id != (parent_branch_id if parent_branch_id else story.branches[0].id if story.branches else None):
            raise ValueError("分叉点续写段不属于该故事")
    
    # 创建分支
    branch = Branch(
        story_id=story_id,
        parent_branch=parent_branch_id,
        title=title,
        description=description,
        creator_bot_id=creator_bot_id,
        fork_at_segment_id=fork_at_segment_id,
        status='active'
    )
    
    db.add(branch)
    db.commit()
    db.refresh(branch)
    
    # 更新Bot活动时间（如果创建者是Bot）
    if creator_bot_id:
        from src.services.cron_service import update_bot_activity
        try:
            update_bot_activity(db, creator_bot_id)
        except Exception as e:
            import logging
            logging.warning(f"Failed to update bot activity: {str(e)}")
    
    # 如果创建者是Bot，自动加入分支
    if creator_bot_id:
        # 计算join_order（当前分支的Bot数量）
        existing_count = db.query(BotBranchMembership).filter(
            BotBranchMembership.branch_id == branch.id
        ).count()
        
        membership = BotBranchMembership(
            bot_id=creator_bot_id,
            branch_id=branch.id,
            join_order=existing_count + 1
        )
        db.add(membership)
        db.commit()
    
    # 分支创建时自动生成摘要
    from src.services.summary_service import generate_summary
    try:
        generate_summary(db, branch.id, force=True)
    except Exception as e:
        # 摘要生成失败不影响分支创建
        import logging
        logging.warning(f"Failed to generate summary for new branch: {str(e)}")
    
    # 发送新分支创建通知给故事的所有参与Bot
    from src.models.bot_branch_membership import BotBranchMembership as BBM
    from src.models.bot import Bot
    story_branches = db.query(Branch).filter(Branch.story_id == story_id).all()
    all_bot_ids = set()
    for b in story_branches:
        memberships = db.query(BBM).filter(BBM.branch_id == b.id).all()
        for m in memberships:
            all_bot_ids.add(m.bot_id)
    
    # 发送通知（排除创建者自己）
    from src.utils.notification_queue import enqueue_new_branch_notification
    for bot_id in all_bot_ids:
        if bot_id != creator_bot_id:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if bot and bot.webhook_url:
                try:
                    enqueue_new_branch_notification(str(bot_id), str(branch.id))
                except Exception as e:
                    # 通知失败不影响分支创建
                    import logging
                    logging.warning(f"Failed to enqueue new branch notification: {str(e)}")
    
    # 清除故事相关缓存
    cache_service.invalidate_story(story_id)
    
    return branch


def create_branch_with_initial_segment(
    db: Session,
    story_id: uuid.UUID,
    title: str,
    description: Optional[str],
    creator_bot_id: Optional[uuid.UUID],
    fork_at_segment_id: Optional[uuid.UUID],
    parent_branch_id: Optional[uuid.UUID],
    initial_segment_content: str
) -> tuple[Branch, Segment]:
    """
    创建分支并自动创建第一段续写
    
    Returns:
        (Branch对象, Segment对象)
    """
    # 先创建分支
    branch = create_branch(
        db=db,
        story_id=story_id,
        title=title,
        description=description,
        creator_bot_id=creator_bot_id,
        fork_at_segment_id=fork_at_segment_id,
        parent_branch_id=parent_branch_id
    )
    
    # 创建第一段续写
    if creator_bot_id:
        segment = Segment(
            branch_id=branch.id,
            bot_id=creator_bot_id,
            content=initial_segment_content,
            sequence_order=1
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)
        
        return branch, segment
    
    return branch, None


def get_branch_by_id(db: Session, branch_id: uuid.UUID) -> Optional[Branch]:
    """根据ID获取分支"""
    return db.query(Branch).filter(Branch.id == branch_id).first()


def get_branches_by_story(
    db: Session,
    story_id: uuid.UUID,
    limit: int = 6,
    offset: int = 0,
    sort: str = 'activity',
    include_all: bool = False
) -> tuple[List[Branch], int]:
    """
    获取故事的所有分支（带缓存）
    
    Returns:
        (分支列表, 总数)
    """
    cache_key_str = cache_key("branches:story", story_id, limit, offset, sort)
    
    # 尝试从缓存获取
    cached = cache_service.get(cache_key_str)
    if cached:
        branch_ids = [uuid.UUID(bid) for bid in cached.get('ids', [])]
        if branch_ids:
            branches = db.query(Branch).filter(Branch.id.in_(branch_ids)).all()
            branch_dict = {str(b.id): b for b in branches}
            ordered_branches = [branch_dict[bid] for bid in cached['ids'] if bid in branch_dict]
            if ordered_branches:
                return ordered_branches, cached.get('total', len(ordered_branches))
    
    query = db.query(Branch).filter(Branch.story_id == story_id, Branch.status == 'active')
    
    total = query.count()
    
    # 排序
    if sort == 'activity':
        # 按活跃度排序（需要计算，暂时按创建时间）
        query = query.order_by(desc(Branch.created_at))
    elif sort == 'created_at':
        query = query.order_by(desc(Branch.created_at))
    elif sort == 'vote_score':
        # 按投票得分排序（暂时按创建时间）
        query = query.order_by(desc(Branch.created_at))
    else:
        query = query.order_by(desc(Branch.created_at))
    
    # 分页
    if not include_all:
        query = query.limit(limit).offset(offset)
    
    branches = query.all()
    
    # 存入缓存
    if branches:
        branch_ids = [str(b.id) for b in branches]
        cache_service.set(cache_key_str, {'ids': branch_ids, 'total': total}, ttl=180)  # 3分钟
    
    return branches, total


def get_branch_tree(db: Session, story_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    获取分支树（递归查询）
    
    Returns:
        分支树结构列表
    """
    def build_tree(branch_id: Optional[uuid.UUID] = None, visited: set = None) -> List[Dict[str, Any]]:
        """递归构建分支树"""
        if visited is None:
            visited = set()
        
        if branch_id and branch_id in visited:
            # 循环引用防护
            return []
        
        if branch_id:
            visited.add(branch_id)
        
        # 查询子分支
        if branch_id:
            children = db.query(Branch).filter(
                Branch.story_id == story_id,
                Branch.parent_branch == branch_id,
                Branch.status == 'active'
            ).all()
        else:
            # 根分支（没有parent_branch的分支）
            children = db.query(Branch).filter(
                Branch.story_id == story_id,
                Branch.parent_branch.is_(None),
                Branch.status == 'active'
            ).all()
        
        result = []
        for branch in children:
            branch_data = {
                'id': str(branch.id),
                'title': branch.title,
                'description': branch.description,
                'parent_branch_id': str(branch.parent_branch) if branch.parent_branch else None,
                'created_at': branch.created_at.isoformat() if branch.created_at else None,
                'children': build_tree(branch.id, visited.copy())
            }
            result.append(branch_data)
        
        return result
    
    return build_tree()


def join_branch(
    db: Session,
    branch_id: uuid.UUID,
    bot_id: uuid.UUID
) -> BotBranchMembership:
    """
    Bot加入分支
    
    Returns:
        BotBranchMembership对象
    """
    # 验证分支存在
    branch = get_branch_by_id(db, branch_id)
    if not branch:
        raise ValueError("分支不存在")
    
    # 检查是否已加入
    existing = db.query(BotBranchMembership).filter(
        BotBranchMembership.bot_id == bot_id,
        BotBranchMembership.branch_id == branch_id
    ).first()
    
    if existing:
        # 已加入，返回现有记录
        return existing
    
    # 计算join_order
    max_order = db.query(func.max(BotBranchMembership.join_order)).filter(
        BotBranchMembership.branch_id == branch_id
    ).scalar() or 0
    
    membership = BotBranchMembership(
        bot_id=bot_id,
        branch_id=branch_id,
        join_order=max_order + 1
    )
    
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    # TODO: 临时禁用这些后置操作（可能导致超时）
    # 更新Bot活动时间
    # from src.services.cron_service import update_bot_activity
    # try:
    #     update_bot_activity(db, bot_id)
    # except Exception as e:
    #     import logging
    #     logging.warning(f"Failed to update bot activity: {str(e)}")
    
    # 更新活跃度得分缓存
    # from src.services.activity_service import update_activity_score_cache
    # try:
    #     update_activity_score_cache(db, branch_id)
    # except Exception as e:
    #     import logging
    #     logging.warning(f"Failed to update activity score cache: {str(e)}")
    
    return membership


def leave_branch(
    db: Session,
    branch_id: uuid.UUID,
    bot_id: uuid.UUID
) -> bool:
    """
    Bot离开分支
    
    Returns:
        是否成功离开
    """
    membership = db.query(BotBranchMembership).filter(
        BotBranchMembership.bot_id == bot_id,
        BotBranchMembership.branch_id == branch_id
    ).first()
    
    if not membership:
        return False
    
    db.delete(membership)
    db.commit()
    
    return True


def get_next_bot_in_queue(db: Session, branch_id: uuid.UUID) -> Optional[Bot]:
    """
    获取轮次队列中的下一个Bot
    
    轮次计算逻辑：
    1. 如果没有续写段，返回第一个加入的Bot
    2. 如果有续写段，计算当前应该轮到谁：
       - 获取最后一个续写段的Bot
       - 计算: (总段数 - 1) % Bot数量 = 当前索引
       - 下一位是 (currentIndex + 1) % Bot数量
    
    Returns:
        Bot对象或None
    """
    # 获取所有参与的Bot（按join_order排序）
    members = db.query(BotBranchMembership).filter(
        BotBranchMembership.branch_id == branch_id
    ).order_by(BotBranchMembership.join_order.asc()).all()
    
    if not members:
        return None
    
    # 获取当前分支的所有续写段
    segments = db.query(Segment).filter(
        Segment.branch_id == branch_id
    ).order_by(Segment.sequence_order.desc()).all()
    
    if not segments:
        # 没有续写段，返回第一个加入的Bot
        first_member = members[0]
        return db.query(Bot).filter(Bot.id == first_member.bot_id).first()
    
    # 获取最后一个续写段的sequence_order
    last_segment = segments[0]
    
    # 计算当前应该轮到谁: (总段数 - 1) % Bot数量 = 当前索引
    total_segments = len(segments)
    current_index = (total_segments - 1) % len(members)
    
    # 下一位是 (currentIndex + 1) % Bot数量
    next_index = (current_index + 1) % len(members)
    next_member = members[next_index]
    
    return db.query(Bot).filter(Bot.id == next_member.bot_id).first()


def update_branch_summary(
    db: Session,
    branch_id: uuid.UUID,
    current_summary: str
) -> Optional[Branch]:
    """更新分支当前进展提要"""
    branch = get_branch_by_id(db, branch_id)
    if not branch:
        return None
    from datetime import datetime
    branch.current_summary = current_summary
    branch.summary_updated_at = datetime.utcnow()
    all_count = db.query(Segment).filter(Segment.branch_id == branch_id).count()
    branch.summary_covers_up_to = all_count
    db.commit()
    db.refresh(branch)
    cache_service.invalidate_story(branch.story_id)
    return branch
