# Agent API Routes for InkPath
# 提供信息抓取接口供 Agent 客户端使用

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid
import bcrypt
import requests
import logging

from src.database import get_db
from src.models.agent import Agent, AgentStory, AgentProgress
from src.models.segment import Segment
from src.models.story import Story

agent_bp = Blueprint('agent', __name__)

logger = logging.getLogger(__name__)


# =====================================================
# 工具函数
# =====================================================

def hash_api_key(api_key: str) -> str:
    """加密 API Key"""
    return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_api_key(api_key: str, hashed: str) -> bool:
    """验证 API Key"""
    return bcrypt.checkpw(api_key.encode('utf-8'), hashed.encode('utf-8'))


def call_llm(prompt: str, bot_model: str = "qwen2.5:7b") -> str:
    """
    调用 LLM 生成续写内容
    
    注意：InkPath 后端不负责调用 LLM，这个功能由 Agent 客户端负责
    此函数仅作为存根，如果被调用会抛出异常
    """
    # 后端不应该调用 LLM - 这是 Agent 的职责
    raise Exception("后端不应调用 LLM，请使用 Agent 客户端进行续写")
    if gemini_key:
        try:
            import json
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            response = requests.post(
                gemini_url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 1000
                    }
                },
                timeout=120
            )
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                logger.warning(f"Gemini 返回错误: {response.status_code}")
        except Exception as e:
            logger.warning(f"Gemini 调用失败: {e}")
    
    # 3. 尝试 MiniMax
    minimax_key = current_app.config.get('MINIMAX_API_KEY', '')
    minimax_secret = current_app.config.get('MINIMAX_API_SECRET', '')
    if minimax_key and minimax_secret:
        try:
            import time
            import hmac
            import hashlib
            # MiniMax 需要签名
            timestamp = str(int(time.time()))
            signature = hmac.new(
                minimax_secret.encode(),
                f"{timestamp}.{minimax_key}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            response = requests.post(
                "https://api.minimax.chat/v1/text/chatcompletion_pro",
                headers={
                    "Authorization": f"Bearer {minimax_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "abab6.5s-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=120
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"MiniMax 调用失败: {e}")
    
    raise Exception("无法调用 LLM，请检查配置 (OPENAI_API_KEY 或 GEMINI_API_KEY)")


# =====================================================
# 客户端首页信息接口
# =====================================================

@agent_bp.route('/home', methods=['GET'])
@jwt_required()
def get_home_data():
    """
    获取 Agent 首页信息
    客户端登录后首先调用此接口获取必要数据
    """
    agent_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        # 获取 Agent 信息
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent 不存在'}), 404
        
        # 获取分配的故事
        agent_stories = db.query(AgentStory).filter(AgentStory.agent_id == agent_id).all()
        
        # 构建统计
        stories_summary = {
            'total': len(agent_stories),
            'running': sum(1 for s in agent_stories if s.auto_continue),
            'idle': sum(1 for s in agent_stories if not s.auto_continue),
            'needs_attention': 0
        }
        
        recent_activity = []
        alerts = []
        
        for as_record in agent_stories:
            progress = db.query(AgentProgress).filter(
                AgentProgress.agent_id == agent_id,
                AgentProgress.story_id == as_record.story_id
            ).first()
            
            if progress:
                # 检查是否需要关注（24小时无更新）
                if progress.last_updated:
                    last_time = progress.last_updated
                    if datetime.utcnow() - last_time > timedelta(hours=24):
                        stories_summary['needs_attention'] += 1
                        alerts.append({
                            'story_id': str(as_record.story_id),
                            'type': 'stale',
                            'message': f"故事 {as_record.story_id} 24小时无更新"
                        })
                
                # 最近活动
                if progress.last_action:
                    recent_activity.append({
                        'story_id': str(as_record.story_id),
                        'action': progress.last_action,
                        'time': progress.last_updated.isoformat() if progress.last_updated else None
                    })
        
        # 限制最近活动数量
        recent_activity = sorted(recent_activity, key=lambda x: x['time'] or '', reverse=True)[:10]
        
        return jsonify({
            'data': {
                'agent': {
                    'id': str(agent.id),
                    'name': agent.name,
                    'status': agent.status,
                    'created_at': agent.created_at.isoformat() if agent.created_at else None
                },
                'stories_summary': stories_summary,
                'recent_activity': recent_activity,
                'alerts': alerts,
                'server_time': datetime.utcnow().isoformat()
            }
        }), 200
        
    finally:
        db.close()


@agent_bp.route('/stories', methods=['GET'])
@jwt_required()
def get_stories_list():
    """
    获取分配给 Agent 的故事列表（分页）
    包括：1) 分配的故事 2) 自己创建的故事
    """
    agent_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 20, type=int), 100)
        status_filter = request.args.get('status', 'all')
        
        stories = []
        
        # 1. 获取 Agent 分配的故事
        try:
            agent_stories = db.query(AgentStory).filter(AgentStory.agent_id == agent_id).all()
            for as_record in agent_stories:
                progress = db.query(AgentProgress).filter(
                    AgentProgress.agent_id == agent_id,
                    AgentProgress.story_id == as_record.story_id
                ).first()
                
                auto_continue = as_record.auto_continue
                
                if status_filter == 'running' and not auto_continue:
                    continue
                if status_filter == 'idle' and auto_continue:
                    continue
                    
                story = db.query(Story).filter(Story.id == as_record.story_id).first()
                if story:
                    stories.append({
                        'id': str(story.id),
                        'title': story.title,
                        'owner_type': story.owner_type,
                        'auto_continue': auto_continue,
                        'progress': {
                            'summary': progress.summary if progress else None,
                            'next_action': progress.next_action if progress else None,
                            'last_action': progress.last_action if progress else None,
                            'segments_count': progress.segments_count if progress else 0
                        } if progress else None
                    })
        except Exception as e:
            logger.warning(f"查询分配故事失败: {e}")
        
        # 2. 获取 Agent 自己创建的故事
        try:
            owned_stories = db.query(Story).filter(
                Story.owner_id == agent_id,
                Story.owner_type == 'bot'
            ).all()
            
            for story in owned_stories:
                # 跳过已添加的
                if any(s['id'] == str(story.id) for s in stories):
                    continue
                    
                progress = db.query(AgentProgress).filter(
                    AgentProgress.agent_id == agent_id,
                    AgentProgress.story_id == story.id
                ).first()
                
                stories.append({
                    'id': str(story.id),
                    'title': story.title,
                    'owner_type': story.owner_type,
                    'auto_continue': True,  # 自己创建的故事默认自动续写
                    'progress': {
                        'summary': progress.summary if progress else None,
                        'next_action': progress.next_action if progress else None,
                        'last_action': progress.last_action if progress else None,
                        'segments_count': progress.segments_count if progress else 0
                    } if progress else None
                })
        except Exception as e:
            logger.warning(f"查询拥有故事失败: {e}")
        
        # 分页
        total = len(stories)
        start = (page - 1) * limit
        end = start + limit
        paginated_stories = stories[start:end]
        
        return jsonify({
            'data': {
                'stories': paginated_stories,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            }
        }), 200
        
    finally:
        db.close()


@agent_bp.route('/stories/<story_id>', methods=['GET'])
@jwt_required()
def get_story_detail(story_id):
    """
    获取故事详情
    """
    agent_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        # 验证权限
        agent_story = db.query(AgentStory).filter(
            AgentStory.agent_id == agent_id,
            AgentStory.story_id == story_id
        ).first()
        
        if not agent_story:
            return jsonify({'error': '无权访问此故事'}), 403
        
        # 获取进度
        progress = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id,
            AgentProgress.story_id == story_id
        ).first()
        
        return jsonify({
            'data': {
                'id': str(story_id),
                'auto_continue': agent_story.auto_continue,
                'progress': {
                    'summary': progress.summary if progress else None,
                    'next_action': progress.next_action if progress else None,
                    'segments_count': progress.segments_count if progress else 0,
                    'auto_continue': agent_story.auto_continue
                }
            }
        }), 200
        
    finally:
        db.close()


@agent_bp.route('/stories/<story_id>/progress', methods=['GET'])
@jwt_required()
def get_story_progress(story_id):
    """
    获取故事进度信息（轻量级接口）
    """
    agent_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        # 验证权限
        agent_story = db.query(AgentStory).filter(
            AgentStory.agent_id == agent_id,
            AgentStory.story_id == story_id
        ).first()
        
        if not agent_story:
            return jsonify({'error': '无权访问'}), 403
        
        progress = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id,
            AgentProgress.story_id == story_id
        ).first()
        
        return jsonify({
            'data': {
                'story_id': str(story_id),
                'summary': progress.summary if progress else '',
                'next_action': progress.next_action if progress else '',
                'auto_continue': agent_story.auto_continue,
                'last_updated': progress.last_updated.isoformat() if progress and progress.last_updated else None,
                'server_time': datetime.utcnow().isoformat()
            }
        }), 200
        
    finally:
        db.close()


@agent_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_agent_stats():
    """
    获取 Agent 统计数据
    """
    agent_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent 不存在'}), 404
        
        agent_stories = db.query(AgentStory).filter(AgentStory.agent_id == agent_id).all()
        
        total_segments = 0
        for as_record in agent_stories:
            progress = db.query(AgentProgress).filter(
                AgentProgress.agent_id == agent_id,
                AgentProgress.story_id == as_record.story_id
            ).first()
            if progress:
                total_segments += progress.segments_count or 0
        
        return jsonify({
            'data': {
                'agent_id': str(agent.id),
                'name': agent.name,
                'stories_count': len(agent_stories),
                'total_segments': total_segments,
                'status': agent.status,
                'created_at': agent.created_at.isoformat() if agent.created_at else None,
                'last_active': agent.updated_at.isoformat() if agent.updated_at else None
            }
        }), 200
        
    finally:
        db.close()


# =====================================================
# Agent 操作接口
# =====================================================

@agent_bp.route('/register', methods=['POST'])
@jwt_required()
def register_agent():
    """
    注册 Agent
    
    请求体:
    {
        "name": "my-agent",
        "api_key": "plain-text-api-key",
        "story_ids": ["uuid-1", "uuid-2"]
    }
    """
    agent_id = get_jwt_identity()
    user_type = get_jwt().get('user_type')
    
    if user_type != 'admin':
        return jsonify({"error": "需要管理员权限"}), 403
    
    data = request.get_json()
    db = next(get_db())
    
    try:
        name = data.get('name')
        api_key = data.get('api_key')
        story_ids = data.get('story_ids', [])
        
        # 验证必填
        if not name or not api_key:
            return jsonify({'error': '缺少必填字段'}), 400
        
        # 加密 API Key
        api_key_hash = hash_api_key(api_key)
        
        # 创建 Agent
        agent = Agent(
            id=agent_id,  # 使用 JWT identity 作为 ID
            name=name,
            owner_id=agent_id,
            api_key_hash=api_key_hash,
            status='idle'
        )
        db.add(agent)
        
        # 分配故事
        for story_id in story_ids:
            agent_story = AgentStory(
                agent_id=agent_id,
                story_id=story_id,
                auto_continue=True
            )
            db.add(agent_story)
        
        db.commit()
        
        return jsonify({
            "message": "Agent 注册成功",
            "agent_id": str(agent.id),
            "name": name
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
        
    finally:
        db.close()


@agent_bp.route('/me', methods=['GET'])
@jwt_required()
def get_agent_info():
    """获取当前 Agent 信息"""
    agent_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            return jsonify({"error": "Agent 不存在"}), 404
        
        agent_stories = db.query(AgentStory).filter(AgentStory.agent_id == agent_id).all()
        
        return jsonify({
            "id": str(agent.id),
            "name": agent.name,
            "status": agent.status,
            "stories_count": len(agent_stories)
        }), 200
        
    finally:
        db.close()


@agent_bp.route('/stories/<story_id>/continue', methods=['POST'])
@jwt_required()
def continue_story(story_id):
    """
    Agent 续写故事
    
    流程：
    1. 验证权限（必须是分配给此 Agent 的故事）
    2. 获取分支最新片段
    3. 调用 LLM 生成续写
    4. 提交新片段
    5. 记录日志
    6. 更新进度摘要
    """
    agent_id = get_jwt_identity()
    db: Session = get_db()
    
    try:
        # 验证权限
        agent_story = db.query(AgentStory).filter(
            AgentStory.agent_id == agent_id,
            AgentStory.story_id == story_id
        ).first()
        
        if not agent_story:
            return jsonify({'error': '无权访问此故事'}), 403
        
        # 获取 Bot 信息
        bot = db.query(Agent).filter(Agent.id == agent_id).first()
        if not bot:
            return jsonify({'error': 'Bot 不存在'}), 404
        
        # 获取故事分支
        from src.models.branch import Branch
        branches = db.query(Branch).filter(
            Branch.story_id == story_id,
            Branch.status == 'active'
        ).order_by(Branch.created_at.desc()).all()
        
        if not branches:
            return jsonify({'error': '故事暂无分支'}), 404
        
        # 使用主分支（parent_branch 为空）
        main_branch = next((b for b in branches if b.parent_branch is None), branches[0])
        
        # 获取最新片段
        latest_segment = db.query(Segment).filter(
            Segment.branch_id == main_branch.id
        ).order_by(Segment.sequence_order.desc()).first()
        
        if not latest_segment:
            return jsonify({'error': '分支暂无片段'}), 404
        
        # 获取前文上下文（最近5个片段）
        context_segments = db.query(Segment).filter(
            Segment.branch_id == main_branch.id
        ).order_by(Segment.sequence_order.desc()).limit(5).all()
        context_segments.reverse()
        
        context = "\n\n".join([
            f"【片段 {s.sequence_order}】{s.content}" 
            for s in context_segments
        ])
        
        # 调用 LLM 生成续写
        prompt = f"""你是一个专业作家，为协作故事平台续写。

## 前文上下文
{context}

## 最新片段
【片段 {latest_segment.sequence_order}】{latest_segment.content}

## 要求
- 延续故事风格和节奏
- 字数 200-400 字
- 直接输出内容，不要前缀说明
- 不要重复前文内容
"""
        
        try:
            content = call_llm(prompt, bot.model)
        except Exception as llm_error:
            logger.error(f"LLM 调用失败: {llm_error}")
            return jsonify({'error': f'LLM 调用失败: {str(llm_error)}'}), 500
        
        # 提交新片段
        from src.services.segment_service import create_segment, log_segment_creation
        
        new_segment = create_segment(
            db=db,
            branch_id=main_branch.id,
            bot_id=agent_id,
            content=content,
            is_starter=False
        )
        
        # 记录日志
        try:
            log_segment_creation(
                db=db,
                segment_id=new_segment.id,
                story_id=story_id,
                branch_id=main_branch.id,
                author_id=agent_id,
                author_type='bot',
                author_name=bot.name,
                content_length=len(content),
                is_continuation='continuation',
                parent_segment_id=latest_segment.id
            )
        except Exception as log_error:
            logger.warning(f"记录日志失败: {log_error}")
        
        # 更新进度摘要
        summary_prompt = f"""根据以下故事片段，生成一句话进展摘要：

{context}

新片段：{content}

请用一句话总结故事的最新进展。"""
        
        try:
            summary = call_llm(summary_prompt, bot.model)[:200]
        except:
            summary = f"继续推进剧情发展"
        
        next_action_prompt = f"""根据以下故事内容，预测接下来可能的发展方向：

{context}

新片段：{content}

请用一句话说明接下来的剧情方向。"""
        
        try:
            next_action = call_llm(next_action_prompt, bot.model)[:200]
        except:
            next_action = "继续续写，推动剧情发展"
        
        # 更新或创建进度记录
        progress = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id,
            AgentProgress.story_id == story_id
        ).first()
        
        now = datetime.utcnow()
        
        if not progress:
            progress = AgentProgress(
                agent_id=agent_id,
                story_id=story_id,
                summary=summary,
                next_action=next_action,
                last_action='continue',
                last_updated=now,
                segments_count=latest_segment.sequence_order + 1
            )
            db.add(progress)
        else:
            progress.summary = summary
            progress.next_action = next_action
            progress.last_action = 'continue'
            progress.last_updated = now
            progress.segments_count = latest_segment.sequence_order + 1
        
        db.commit()
        
        return jsonify({
            "message": "续写完成",
            "story_id": story_id,
            "branch_id": str(main_branch.id),
            "segment_id": str(new_segment.id),
            "content_length": len(content),
            "summary": summary,
            "next_action": next_action
        }), 200
        
    except Exception as e:
        db.rollback()
        logger.error(f"续写失败: {e}", exc_info=True)
        return jsonify({'error': f'续写失败: {str(e)}'}), 500
    finally:
        db.close()


@agent_bp.route('/stories/<story_id>/summarize', methods=['POST'])
@jwt_required()
def update_story_summary(story_id):
    """更新故事进展摘要（调用 LLM）"""
    agent_id = get_jwt_identity()
    db: Session = get_db()
    
    try:
        # 验证权限
        agent_story = db.query(AgentStory).filter(
            AgentStory.agent_id == agent_id,
            AgentStory.story_id == story_id
        ).first()
        
        if not agent_story:
            return jsonify({'error': '无权访问此故事'}), 403
        
        # 获取 Bot 信息
        bot = db.query(Agent).filter(Agent.id == agent_id).first()
        
        # 获取分支
        from src.models.branch import Branch
        branches = db.query(Branch).filter(
            Branch.story_id == story_id,
            Branch.status == 'active'
        ).all()
        
        if not branches:
            return jsonify({'error': '故事暂无分支'}), 404
        
        main_branch = next((b for b in branches if b.parent_branch is None), branches[0])
        
        # 获取所有片段
        segments = db.query(Segment).filter(
            Segment.branch_id == main_branch.id
        ).order_by(Segment.sequence_order.asc()).limit(50).all()
        
        if not segments:
            return jsonify({'error': '分支暂无片段'}), 404
        
        # 生成摘要
        content = "\n\n".join([f"【片段 {s.sequence_order}】{s.content}" for s in segments])
        summary_prompt = f"""请阅读以下故事内容，然后生成：
1. 一句话剧情摘要
2. 接下来可能的发展方向

## 故事内容
{content[:8000]}

请用中文回复，格式如下：
摘要：xxx
下一步：xxx
"""
        
        bot_model = bot.model if bot else "qwen2.5:7b"
        
        try:
            result = call_llm(summary_prompt, bot_model)
            lines = result.strip().split('\n')
            summary = ""
            next_action = "继续续写，推动剧情发展"
            
            for line in lines:
                if '摘要' in line and '：' in line:
                    summary = line.split('：')[1].split(':')[-1].strip()
                elif '下一步' in line and '：' in line:
                    next_action = line.split('：')[1].split(':')[-1].strip()
            
            if not summary:
                summary = result[:200]
        except Exception as llm_error:
            logger.warning(f"LLM 生成摘要失败: {llm_error}")
            summary = f"故事已有 {len(segments)} 个片段"
            next_action = "继续续写，推动剧情发展"
        
        # 更新进度
        now = datetime.utcnow()
        progress = db.query(AgentProgress).filter(
            AgentProgress.agent_id == agent_id,
            AgentProgress.story_id == story_id
        ).first()
        
        if not progress:
            progress = AgentProgress(
                agent_id=agent_id,
                story_id=story_id,
                summary=summary,
                next_action=next_action,
                last_action='summarize',
                last_updated=now,
                segments_count=len(segments)
            )
            db.add(progress)
        else:
            progress.summary = summary
            progress.next_action = next_action
            progress.last_action = 'summarize'
            progress.last_updated = now
            progress.segments_count = len(segments)
        
        db.commit()
        
        return jsonify({
            "message": "摘要已更新",
            "summary": summary,
            "next_action": next_action,
            "segments_count": len(segments)
        }), 200
        
    except Exception as e:
        db.rollback()
        logger.error(f"生成摘要失败: {e}", exc_info=True)
        return jsonify({'error': f'生成摘要失败: {str(e)}'}), 500
    finally:
        db.close()


@agent_bp.route('/stories/<story_id>/auto-continue', methods=['PUT'])
@jwt_required()
def update_auto_continue(story_id):
    """更新故事的自动续写设置"""
    agent_id = get_jwt_identity()
    data = request.get_json()
    enabled = data.get('enabled', True)
    
    db = next(get_db())
    
    try:
        # 验证权限
        agent_story = db.query(AgentStory).filter(
            AgentStory.agent_id == agent_id,
            AgentStory.story_id == story_id
        ).first()
        
        if not agent_story:
            return jsonify({'error': '无权访问此故事'}), 403
        
        agent_story.auto_continue = enabled
        agent_story.updated_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            "message": "设置已更新",
            "auto_continue": enabled
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
        
    finally:
        db.close()


@agent_bp.route('/monitor', methods=['POST'])
@agent_bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_bot_profile():
    """更新 Bot 个人信息（名称、模型等）"""
    agent_id = get_jwt_identity()
    data = request.get_json()
    db: Session = get_db()
    
    try:
        bot = db.query(Agent).filter(Agent.id == agent_id).first()
        if not bot:
            return jsonify({'error': 'Bot 不存在'}), 404
        
        # 更新名称
        if 'name' in data and data['name']:
            bot.name = data['name']
        
        # 更新模型
        if 'model' in data and data['model']:
            bot.model = data['model']
        
        db.commit()
        
        return jsonify({
            'message': '更新成功',
            'data': {
                'id': str(bot.id),
                'name': bot.name,
                'model': bot.model,
                'status': bot.status
            }
        }), 200
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新失败: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@agent_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_bot_profile():
    """获取 Bot 个人信息"""
    agent_id = get_jwt_identity()
    db: Session = get_db()
    
    try:
        bot = db.query(Agent).filter(Agent.id == agent_id).first()
        if not bot:
            return jsonify({'error': 'Bot 不存在'}), 404
        
        return jsonify({
            'data': {
                'id': str(bot.id),
                'name': bot.name,
                'model': bot.model,
                'status': bot.status,
                'reputation': bot.reputation,
                'created_at': bot.created_at.isoformat() if bot.created_at else None
            }
        }), 200
        
    finally:
        db.close()


@jwt_required()
def monitor_stories():
    """Agent 监控分配的故事"""
    agent_id = get_jwt_identity()
    
    return jsonify({
        "message": "监控完成",
        "checked_stories": 0,
        "continued_stories": 0
    }), 200


# =====================================================
# 预加载接口
# =====================================================

@agent_bp.route('/preload/<story_id>', methods=['GET'])
@jwt_required()
def preload_story(story_id):
    """预加载故事完整数据"""
    agent_id = get_jwt_identity()
    
    # TODO: 从数据库获取真实完整数据
    
    return jsonify({
        'data': {
            'story_id': str(story_id),
            'preloaded_at': datetime.utcnow().isoformat()
        }
    }), 200
