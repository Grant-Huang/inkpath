"""摘要生成服务"""
import uuid
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.branch import Branch
from src.models.segment import Segment
from src.models.story import Story
from src.config import Config
import anthropic


def should_generate_summary(db: Session, branch_id: uuid.UUID) -> bool:
    """
    检查是否应该生成摘要
    
    触发条件：
    1. 新增段数 >= 3（自上次摘要更新后）
    2. 分支创建时（还没有摘要）
    
    Returns:
        是否应该生成摘要
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        return False
    
    # 条件1: 分支创建时（还没有摘要）
    if not branch.summary_updated_at:
        return True
    
    # 条件2: 新增段数 >= 3
    new_segments_count = db.query(Segment).filter(
        Segment.branch_id == branch_id,
        Segment.created_at > branch.summary_updated_at
    ).count()
    
    if new_segments_count >= 3:
        return True
    
    return False


def format_segments(segments: list[Segment]) -> str:
    """
    格式化续写段为文本
    
    Returns:
        格式化后的文本
    """
    lines = []
    for seg in segments:
        lines.append(f"第{seg.sequence_order}段：{seg.content}")
    return "\n\n".join(lines)


def generate_summary(
    db: Session,
    branch_id: uuid.UUID,
    force: bool = False
) -> Optional[str]:
    """
    生成分支摘要
    
    Args:
        branch_id: 分支ID
        force: 是否强制生成（忽略触发条件）
    
    Returns:
        生成的摘要文本，失败返回None
    """
    # 检查触发条件
    if not force and not should_generate_summary(db, branch_id):
        return None
    
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        return None
    
    story = db.query(Story).filter(Story.id == branch.story_id).first()
    if not story:
        return None
    
    # 获取续写段（最多20段）
    segments = db.query(Segment).filter(
        Segment.branch_id == branch_id
    ).order_by(Segment.sequence_order.asc()).all()
    
    if not segments:
        return None
    
    # 如果段数 > 20，只取最近20段，并使用上次摘要作为前因
    previous_summary = ""
    if len(segments) > 20:
        previous_summary = branch.current_summary or ""
        segments = segments[-20:]  # 只取最近20段
    
    # 构建Prompt
    segments_text = format_segments(segments)
    
    prompt = f"""你是一个故事编辑助手。以下是一条进行中的故事分支的续写内容。

{previous_summary if previous_summary else ""}

续写内容:
{segments_text}

请生成一段300-500字的"当前进展摘要"，包含：
- 故事现在发展到哪里了（情节状态）
- 当前涉及哪些主要角色及其处境
- 现在悬而未决的问题或冲突是什么

摘要语气要客观，不要剧透未来，只概述当前。"""
    
    # 调用LLM生成摘要
    try:
        if not Config.ANTHROPIC_API_KEY:
            # 如果没有配置API Key，返回占位符
            return "摘要生成功能需要配置ANTHROPIC_API_KEY"
        
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        summary = response.content[0].text
        
        # 更新数据库
        branch.current_summary = summary
        branch.summary_updated_at = datetime.utcnow()
        branch.summary_covers_up_to = len(segments) if len(segments) <= 20 else len(db.query(Segment).filter(Segment.branch_id == branch_id).count())
        
        # 计算实际覆盖的段数（所有段数）
        all_segments_count = db.query(Segment).filter(
            Segment.branch_id == branch_id
        ).count()
        branch.summary_covers_up_to = all_segments_count
        
        db.commit()
        db.refresh(branch)
        
        return summary
    
    except Exception as e:
        # LLM调用失败，不阻塞，返回None
        import logging
        logging.error(f"摘要生成失败: {str(e)}")
        return None


def get_branch_summary(
    db: Session,
    branch_id: uuid.UUID,
    force_refresh: bool = False
) -> dict:
    """
    获取分支摘要（懒刷新）
    
    Args:
        branch_id: 分支ID
        force_refresh: 是否强制刷新
    
    Returns:
        包含summary, updated_at, covers_up_to的字典
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError("分支不存在")
    
    # 如果有新续写段，触发懒刷新（异步，不阻塞）
    if not force_refresh and should_generate_summary(db, branch_id):
        # 异步生成，不阻塞请求
        # 在实际应用中，可以使用队列异步处理
        try:
            generate_summary(db, branch_id, force=True)
        except Exception as e:
            # 失败不影响返回，返回旧摘要
            import logging
            logging.warning(f"懒刷新摘要生成失败: {str(e)}")
    
    return {
        'summary': branch.current_summary,
        'updated_at': branch.summary_updated_at.isoformat() if branch.summary_updated_at else None,
        'covers_up_to': branch.summary_covers_up_to or 0
    }
