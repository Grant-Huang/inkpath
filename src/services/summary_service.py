"""摘要生成服务 - 使用 MiniMax LLM"""
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
    """
    检查是否应该生成摘要
    
    触发条件：
    1. 新增段数 >= 配置值 SUMMARY_TRIGGER_COUNT（自上次摘要更新后）
    2. 分支创建时（还没有摘要）
    
    配置：
    - SUMMARY_TRIGGER_COUNT: 每N个续写后生成摘要（默认5）
    
    Returns:
        是否应该生成摘要
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        return False
    
    # 条件1: 分支创建时（还没有摘要）
    if not branch.summary_updated_at:
        return True
    
    # 条件2: 新增段数 >= 配置值
    trigger_count = getattr(Config, 'SUMMARY_TRIGGER_COUNT', 5)
    new_segments_count = db.query(Segment).filter(
        Segment.branch_id == branch_id,
        Segment.created_at > branch.summary_updated_at
    ).count()
    
    if new_segments_count >= trigger_count:
        return True
    
    return False


def format_segments(segments: list[Segment]) -> str:
    """
    格式化续写段为文本
    """
    lines = []
    for seg in segments:
        lines.append(f"【第{seg.sequence_order}段】\n{seg.content}")
    return "\n\n".join(lines)


def generate_summary_with_minimax(
    db: Session,
    branch_id: uuid.UUID,
    force: bool = False
) -> Optional[str]:
    """
    使用 MiniMax LLM 生成分支摘要
    
    配置：
    - MINIMAX_API_KEY: MiniMax API 密钥
    - SUMMARY_MAX_SEGMENTS: 生成摘要时最多包含的段数（默认20）
    
    Args:
        db: 数据库会话
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
    
    # 获取续写段
    max_segments = getattr(Config, 'SUMMARY_MAX_SEGMENTS', 20)
    segments = db.query(Segment).filter(
        Segment.branch_id == branch_id
    ).order_by(Segment.sequence_order.asc()).all()
    
    if not segments:
        return None
    
    # 如果段数 > max_segments，只取最近N段，并使用上次摘要作为前因
    previous_summary = ""
    start_index = 0
    if len(segments) > max_segments:
        previous_summary = branch.current_summary or ""
        start_index = len(segments) - max_segments
    
    recent_segments = segments[start_index:]
    
    # 构建Prompt
    story_info = f"""## 故事信息
标题：{story.title}
背景：{story.background[:500] if story.background else '无'}
风格规则：{story.style_rules[:500] if story.style_rules else '无'}
"""
    
    segments_text = format_segments(recent_segments)
    
    # 修复 Python 3.12 walrus operator 在 f-string 中的问题
    prev_summary_text = previous_summary if recent_segments else '（无）'
    
    prompt = f"""{story_info}

## 前文摘要（如有）
{prev_summary_text}

## 最近续写内容（共{len(recent_segments)}段）
{segments_text}

请生成一段**300-500字**的故事进展摘要，要求：
1. 客观描述当前故事发展到哪里了（情节状态）
2. 列出当前涉及的主要角色及其处境
3. 说明现在悬而未决的问题或冲突是什么
4. 语气要简洁，只概述当前进展，不要剧透未来

请直接输出摘要正文，不要有前缀或后缀说明。"""
    
    # 调用 MiniMax API 生成摘要
    try:
        api_key = getattr(Config, 'MINIMAX_API_KEY', '')
        if not api_key:
            return "[需要配置MINIMAX_API_KEY才能生成AI摘要]"
        
        # MiniMax Chat Completion API
        url = f"{getattr(Config, 'MINIMAX_BASE_URL', 'https://api.minimax.chat/v1')}/text/chatcompletion_v2"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "abab6.5s-chat",  # MiniMax 聊天模型
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的故事编辑，擅长用简洁客观的语言总结故事进展。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "tokens_to_generate": 512,
            "temperature": 0.5,
            "top_p": 0.95
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析 MiniMax 响应格式
        if data.get("base_resp", {}).get("status_code") == 0:
            summary = data["choices"][0]["message"]["content"]
        else:
            # 旧格式兼容
            summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not summary:
            return None
        
        # 清理摘要文本（移除可能的引号）
        summary = summary.strip().strip('"').strip("'")
        
        # 更新数据库
        all_segments_count = db.query(Segment).filter(
            Segment.branch_id == branch_id
        ).count()
        
        branch.current_summary = summary
        branch.summary_updated_at = datetime.utcnow()
        branch.summary_covers_up_to = all_segments_count
        
        db.commit()
        db.refresh(branch)
        
        return summary
    
    except requests.exceptions.RequestException as e:
        import logging
        logging.error(f"MiniMax API 请求失败: {str(e)}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        import logging
        logging.error(f"解析 MiniMax 响应失败: {str(e)}")
        return None
    except Exception as e:
        import logging
        logging.error(f"摘要生成失败: {str(e)}")
        return None


def generate_summary(
    db: Session,
    branch_id: uuid.UUID,
    force: bool = False
) -> Optional[str]:
    """
    生成分支摘要（统一入口，优先使用 MiniMax）
    
    Args:
        db: 数据库会话
        branch_id: 分支ID
        force: 是否强制生成
    
    Returns:
        生成的摘要文本，失败返回None
    """
    return generate_summary_with_minimax(db, branch_id, force)


def get_branch_summary(
    db: Session,
    branch_id: uuid.UUID,
    force_refresh: bool = False
) -> dict:
    """
    获取分支摘要（懒刷新）
    
    Args:
        db: 数据库会话
        branch_id: 分支ID
        force_refresh: 是否强制刷新
    
    Returns:
        包含summary, updated_at, covers_up_to的字典
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError("分支不存在")
    
    # 如果有新续写段，触发懒刷新
    if not force_refresh and should_generate_summary(db, branch_id):
        try:
            generate_summary(db, branch_id, force=True)
        except Exception as e:
            import logging
            logging.warning(f"懒刷新摘要生成失败: {str(e)}")
    
    return {
        'summary': branch.current_summary,
        'updated_at': branch.summary_updated_at.isoformat() if branch.summary_updated_at else None,
        'covers_up_to': branch.summary_covers_up_to or 0
    }
