"""摘要生成服务 - 使用 MiniMax 或 Google Gemini LLM"""
import uuid
import json
import requests
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.branch import Branch
from src.models.segment import Segment
from src.models.story import Story
from src.config import Config


def should_generate_summary(db: Session, branch_id: uuid.UUID) -> bool:
    """检查是否应该生成摘要"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        return False
    
    if not branch.summary_updated_at:
        return True
    
    trigger_count = getattr(Config, 'SUMMARY_TRIGGER_COUNT', 5)
    new_segments_count = db.query(Segment).filter(
        Segment.branch_id == branch_id,
        Segment.created_at > branch.summary_updated_at
    ).count()
    
    return new_segments_count >= trigger_count


def format_segments(segments: list[Segment]) -> str:
    """格式化续写段为文本"""
    lines = []
    for seg in segments:
        lines.append(f"【第{seg.sequence_order}段】\n{seg.content}")
    return "\n\n".join(lines)


def generate_summary_with_minimax(db: Session, branch_id: uuid.UUID) -> Optional[str]:
    """使用 MiniMax LLM 生成摘要"""
    api_key = getattr(Config, 'MINIMAX_API_KEY', '')
    if not api_key:
        return None
    
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    story = db.query(Story).filter(Story.id == branch.story_id).first() if branch else None
    if not branch or not story:
        return None
    
    max_segments = getattr(Config, 'SUMMARY_MAX_SEGMENTS', 20)
    segments = db.query(Segment).filter(
        Segment.branch_id == branch_id
    ).order_by(Segment.sequence_order.asc()).all()
    
    if not segments:
        return None
    
    previous_summary = ""
    start_index = 0
    if len(segments) > max_segments:
        previous_summary = branch.current_summary or ""
        start_index = len(segments) - max_segments
    
    recent_segments = segments[start_index:]
    
    story_info = f"""## 故事信息
标题：{story.title}
背景：{story.background[:500] if story.background else '无'}
风格规则：{story.style_rules[:500] if story.style_rules else '无'}
"""
    
    segments_text = format_segments(recent_segments)
    prev_text = previous_summary if recent_segments else '（无）'
    
    prompt = f"""{story_info}

## 前文摘要
{prev_text}

## 最近续写内容（共{len(recent_segments)}段）
{segments_text}

请生成一段**300-500字**的故事进展摘要，要求：
1. 客观描述当前故事发展到哪里了
2. 列出当前涉及的主要角色及其处境
3. 说明现在悬而未决的问题或冲突

请直接输出摘要正文。"""
    
    try:
        url = f"{getattr(Config, 'MINIMAX_BASE_URL', 'https://api.minimax.chat/v1')}/text/chatcompletion_v2"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": getattr(Config, 'MINIMAX_MODEL', 'abab6.5s-chat'),
            "messages": [
                {"role": "system", "content": "你是一个专业的故事编辑。"},
                {"role": "user", "content": prompt}
            ],
            "tokens_to_generate": 512,
            "temperature": 0.5
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not summary:
            return None
        
        return summary.strip()
    
    except Exception as e:
        print(f"MiniMax API 错误: {e}")
        return None


def generate_summary_with_gemini(db: Session, branch_id: uuid.UUID) -> Optional[str]:
    """使用 Google Gemini LLM 生成摘要"""
    api_key = getattr(Config, 'GEMINI_API_KEY', '')
    if not api_key:
        return None
    
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    story = db.query(Story).filter(Story.id == branch.story_id).first() if branch else None
    if not branch or not story:
        return None
    
    max_segments = getattr(Config, 'SUMMARY_MAX_SEGMENTS', 20)
    segments = db.query(Segment).filter(
        Segment.branch_id == branch_id
    ).order_by(Segment.sequence_order.asc()).all()
    
    if not segments:
        return None
    
    previous_summary = ""
    start_index = 0
    if len(segments) > max_segments:
        previous_summary = branch.current_summary or ""
        start_index = len(segments) - max_segments
    
    recent_segments = segments[start_index:]
    
    story_info = f"""故事标题：{story.title}
故事背景：{story.background[:500] if story.background else '无'}
风格：{story.style_rules[:500] if story.style_rules else '无'}"""
    
    segments_text = format_segments(recent_segments)
    prev_text = previous_summary if recent_segments else '（无）'
    
    prompt = f"""{story_info}

前文摘要：{prev_text}

最近续写（共{len(recent_segments)}段）：
{segments_text}

请用中文生成300-500字的故事进展摘要，包括：
1. 当前故事发展到哪里
2. 主要角色及处境
3. 悬而未决的问题

只输出摘要正文。"""
    
    try:
        model = getattr(Config, 'GEMINI_MODEL', 'gemini-2.5-flash-preview-04-17')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 512,
                "temperature": 0.5
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        summary = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        if not summary:
            return None
        
        return summary.strip()
    
    except Exception as e:
        print(f"Gemini API 错误: {e}")
        return None


def get_branch_summary(db: Session, branch_id: uuid.UUID, force_refresh: bool = False) -> dict:
    """获取分支摘要"""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError(f"分支 {branch_id} 不存在")
    
    # 如果强制刷新或没有摘要，生成新摘要
    if force_refresh or not branch.current_summary:
        summary = generate_summary(db, branch_id, force=True)
    else:
        summary = branch.current_summary
    
    return {
        'summary': summary or '暂无摘要',
        'updated_at': branch.summary_updated_at.isoformat() if branch.summary_updated_at else None,
        'covers_up_to': branch.summary_covers_up_to or 0
    }


def generate_summary(db: Session, branch_id: uuid.UUID, force: bool = False) -> Optional[str]:
    """生成摘要（统一入口）"""
    # 检查触发条件
    if not force and not should_generate_summary(db, branch_id):
        return None
    
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        return None
    
    # 根据配置选择 LLM Provider
    provider = getattr(Config, 'LLM_PROVIDER', 'minimax')
    
    if provider == 'gemini':
        summary = generate_summary_with_gemini(db, branch_id)
    else:
        summary = generate_summary_with_minimax(db, branch_id)
    
    if not summary:
        return None
    
    # 更新数据库
    all_count = db.query(Segment).filter(Segment.branch_id == branch_id).count()
    branch.current_summary = summary
    branch.summary_updated_at = datetime.utcnow()
    branch.summary_covers_up_to = all_count
    db.commit()
    db.refresh(branch)
    
    return summary
