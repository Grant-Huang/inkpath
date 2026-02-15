# Agent API Routes for InkPath
# 提供信息抓取接口供 Agent 客户端使用

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
import uuid
import bcrypt

from src.database import get_db
from src.models.agent import Agent, AgentStory, AgentProgress

agent_bp = Blueprint('agent', __name__)


# =====================================================
# 工具函数
# =====================================================

def hash_api_key(api_key: str) -> str:
    """加密 API Key"""
    return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_api_key(api_key: str, hashed: str) -> bool:
    """验证 API Key"""
    return bcrypt.checkpw(api_key.encode('utf-8'), hashed.encode('utf-8'))


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
    """
    agent_id = get_jwt_identity()
    db = next(get_db())
    
    try:
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 20, type=int), 100)
        status_filter = request.args.get('status', 'all')
        
        # 获取 Agent 分配的故事
        agent_stories = db.query(AgentStory).filter(AgentStory.agent_id == agent_id).all()
        
        stories = []
        for as_record in agent_stories:
            # 获取进度
            progress = db.query(AgentProgress).filter(
                AgentProgress.agent_id == agent_id,
                AgentProgress.story_id == as_record.story_id
            ).first()
            
            auto_continue = as_record.auto_continue
            
            if status_filter == 'running' and not auto_continue:
                continue
            if status_filter == 'idle' and auto_continue:
                continue
            
            stories.append({
                'id': str(as_record.story_id),
                'auto_continue': auto_continue,
                'summary': progress.summary if progress else None,
                'next_action': progress.next_action if progress else None,
                'segments_count': progress.segments_count if progress else 0,
                'last_updated': progress.last_updated.isoformat() if progress and progress.last_updated else None,
                'last_action': progress.last_action if progress else None
            })
        
        # 分页
        start = (page - 1) * limit
        end = start + limit
        paginated_stories = stories[start:end]
        
        return jsonify({
            'data': {
                'stories': paginated_stories,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': len(stories),
                    'total_pages': (len(stories) + limit - 1) // limit
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
    """Agent 手动续写故事"""
    agent_id = get_jwt_identity()
    
    # TODO: 实现续写逻辑
    # 1. 获取故事最新片段
    # 2. 调用 LLM 生成续写
    # 3. 提交新片段
    # 4. 更新进度摘要
    
    return jsonify({
        "message": "续写完成",
        "story_id": story_id,
        "agent_id": agent_id
    }), 200


@agent_bp.route('/stories/<story_id>/summarize', methods=['POST'])
@jwt_required()
def update_story_summary(story_id):
    """更新故事进展摘要"""
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
        
        # TODO: 获取故事片段，生成摘要
        
        summary = f"已更新"
        next_action = "继续续写，推动剧情发展"
        
        # 更新或创建进度记录
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
                last_action='summarize'
            )
            db.add(progress)
        else:
            progress.summary = summary
            progress.next_action = next_action
            progress.last_action = 'summarize'
            progress.last_updated = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            "message": "摘要已更新",
            "summary": summary,
            "next_action": next_action
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
        
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
