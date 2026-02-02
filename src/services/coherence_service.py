"""连续性校验服务"""
import uuid
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from src.models.segment import Segment
from src.models.branch import Branch
from src.config import Config
import anthropic
import logging


def get_previous_segments(
    db: Session,
    branch_id: uuid.UUID,
    limit: int = 5
) -> list[Segment]:
    """
    获取前N段续写作为上下文
    
    Args:
        branch_id: 分支ID
        limit: 获取的段数，默认5段
    
    Returns:
        续写段列表（按sequence_order升序）
    """
    segments = db.query(Segment).filter(
        Segment.branch_id == branch_id
    ).order_by(Segment.sequence_order.desc()).limit(limit).all()
    
    # 反转顺序，使其按sequence_order升序
    return list(reversed(segments))


def format_segments_for_coherence(segments: list[Segment]) -> str:
    """
    格式化续写段为连续性校验的上下文
    
    Returns:
        格式化后的文本
    """
    if not segments:
        return "（暂无前面的续写内容）"
    
    lines = []
    for seg in segments:
        lines.append(f"第{seg.sequence_order}段：{seg.content}")
    return "\n\n".join(lines)


def check_coherence(
    db: Session,
    branch_id: uuid.UUID,
    new_content: str
) -> Tuple[bool, float, Optional[str]]:
    """
    检查续写内容的连续性
    
    Args:
        db: 数据库会话
        branch_id: 分支ID
        new_content: 新的续写内容
    
    Returns:
        (是否通过, 评分, 错误信息)
        如果LLM调用失败，返回(True, 0.0, None)（不阻塞续写）
    """
    # 检查是否启用连续性校验
    if not Config.ENABLE_COHERENCE_CHECK:
        return True, 0.0, None
    
    # 检查API Key
    if not Config.ANTHROPIC_API_KEY:
        logging.warning("连续性校验已启用但未配置ANTHROPIC_API_KEY，跳过校验")
        return True, 0.0, None
    
    try:
        # 获取前5段续写
        previous_segments = get_previous_segments(db, branch_id, limit=5)
        previous_text = format_segments_for_coherence(previous_segments)
        
        # 构建Prompt
        prompt = f"""请评估以下续写内容与前面内容的连贯性，给出1-10分的评分（只返回数字，不要其他文字）。

前{len(previous_segments)}段续写内容：
{previous_text}

新续写内容：
{new_content}

评分标准：
- 1-3分：完全不连贯，矛盾明显，与前面内容冲突
- 4-6分：基本连贯，但有一些不自然或突兀的地方
- 7-8分：连贯性良好，与前面内容衔接自然
- 9-10分：非常连贯，完美衔接前面内容

请只返回一个1-10之间的整数分数，不要其他文字。"""
        
        # 调用LLM（使用Claude Haiku，成本较低）
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # 使用Haiku模型，成本较低
            max_tokens=10,  # 只需要返回一个数字
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 解析评分
        score_text = response.content[0].text.strip()
        try:
            score = float(score_text)
            # 确保评分在1-10范围内
            score = max(1.0, min(10.0, score))
        except ValueError:
            logging.error(f"无法解析连续性评分: {score_text}")
            # 解析失败，不阻塞续写
            return True, 0.0, None
        
        # 检查是否通过阈值
        threshold = Config.COHERENCE_THRESHOLD
        passed = score >= threshold
        
        if not passed:
            error_msg = f"连续性校验未通过，评分：{score:.1f}（阈值：{threshold}）"
            return False, score, error_msg
        
        return True, score, None
    
    except Exception as e:
        # LLM调用失败，不阻塞续写，记录错误
        logging.error(f"连续性校验失败: {str(e)}")
        return True, 0.0, None
