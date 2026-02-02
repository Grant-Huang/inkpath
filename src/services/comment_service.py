"""评论服务"""
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.models.comment import Comment
from src.models.branch import Branch
from src.models.bot import Bot
from src.models.user import User


def create_comment(
    db: Session,
    branch_id: uuid.UUID,
    author_id: uuid.UUID,
    author_type: str,
    content: str,
    parent_comment_id: Optional[uuid.UUID] = None
) -> Comment:
    """
    创建评论
    
    Args:
        branch_id: 分支ID
        author_id: 作者ID（Bot ID或User ID）
        author_type: 作者类型 ('bot' | 'human')
        content: 评论内容
        parent_comment_id: 父评论ID（可选，用于回复）
    
    Returns:
        Comment对象
    """
    # 验证分支存在
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise ValueError("分支不存在")
    
    # 验证author_type
    if author_type not in ['bot', 'human']:
        raise ValueError("author_type必须是'bot'或'human'")
    
    # 验证作者存在
    if author_type == 'bot':
        author = db.query(Bot).filter(Bot.id == author_id).first()
        if not author:
            raise ValueError("Bot不存在")
    else:
        author = db.query(User).filter(User.id == author_id).first()
        if not author:
            raise ValueError("用户不存在")
    
    # 验证内容长度
    if not content or len(content.strip()) == 0:
        raise ValueError("评论内容不能为空")
    
    if len(content) > 1000:
        raise ValueError("评论内容不能超过1000字符")
    
    # 如果指定了父评论，验证父评论存在且属于同一分支
    if parent_comment_id:
        parent_comment = db.query(Comment).filter(Comment.id == parent_comment_id).first()
        if not parent_comment:
            raise ValueError("父评论不存在")
        if parent_comment.branch_id != branch_id:
            raise ValueError("父评论不属于该分支")
    
    # 创建评论
    comment = Comment(
        branch_id=branch_id,
        author_id=author_id,
        author_type=author_type,
        content=content.strip(),
        parent_comment=parent_comment_id
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment


def get_comments_by_branch(
    db: Session,
    branch_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """
    获取分支的评论树
    
    Returns:
        评论树列表（树形结构）
    """
    # 获取所有评论
    comments = db.query(Comment).filter(
        Comment.branch_id == branch_id
    ).order_by(Comment.created_at.asc()).all()
    
    # 构建评论树
    comment_dict = {}
    root_comments = []
    
    # 第一遍：创建所有评论的字典
    for comment in comments:
        comment_dict[str(comment.id)] = {
            'id': str(comment.id),
            'content': comment.content,
            'author_type': comment.author_type,
            'author_id': str(comment.author_id),
            'parent_comment_id': str(comment.parent_comment) if comment.parent_comment else None,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
            'children': []
        }
        
        # 获取作者信息
        if comment.author_type == 'bot':
            bot = db.query(Bot).filter(Bot.id == comment.author_id).first()
            if bot:
                comment_dict[str(comment.id)]['author'] = {
                    'id': str(bot.id),
                    'name': bot.name,
                    'type': 'bot'
                }
        else:
            user = db.query(User).filter(User.id == comment.author_id).first()
            if user:
                comment_dict[str(comment.id)]['author'] = {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email,
                    'type': 'human'
                }
    
    # 第二遍：构建树形结构
    for comment in comments:
        comment_data = comment_dict[str(comment.id)]
        
        if comment.parent_comment:
            # 有父评论，添加到父评论的children中
            parent_id = str(comment.parent_comment)
            if parent_id in comment_dict:
                comment_dict[parent_id]['children'].append(comment_data)
        else:
            # 根评论
            root_comments.append(comment_data)
    
    return root_comments


def get_comment_by_id(db: Session, comment_id: uuid.UUID) -> Optional[Comment]:
    """根据ID获取评论"""
    return db.query(Comment).filter(Comment.id == comment_id).first()
