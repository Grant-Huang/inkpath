"""
Agent API - 故事包生成和对话

提供 Agent 与用户对话生成故事包的 API
"""

import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional

from src.api.v1.auth import get_current_bot
from src.services.story_service import StoryService

agent_bp = Blueprint('agent', url_prefix='/api/v1/agent')


@agent_bp.route('/generate', methods=['POST'])
def generate():
    """
    生成故事包或继续对话
    
    请求体:
    {
        "message": "用户消息",
        "history": [{"role": "user|assistant", "content": "..."}],
        "currentPackage": {
            "files": [{"name": "文件名", "content": "内容"}],
            "status": "incomplete|complete"
        }
    }
    
    响应:
    {
        "status": "success",
        "response": "AI 回复文本",
        "metadata": {...},
        "storyPackage": {
            "files": [...],
            "status": "incomplete|complete",
            "missingFields": [...]
        }
    }
    """
    try:
        data = request.get_json()
        
        user_message = data.get('message', '').strip()
        history = data.get('history', [])
        current_package = data.get('currentPackage', None)
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'error': {'message': '消息不能为空'}
            }), 400
        
        # 解析用户意图
        intent = _parse_intent(user_message)
        
        # 生成响应
        response = _generate_response(
            message=user_message,
            intent=intent,
            history=history,
            current_package=current_package
        )
        
        # 更新故事包状态
        story_package = _update_package(
            current_package,
            response.get('storyPackage', {}),
            intent
        )
        
        return jsonify({
            'status': 'success',
            'response': response['text'],
            'metadata': response.get('metadata', {}),
            'storyPackage': story_package,
            'missingFields': story_package.get('missingFields', [])
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': {'message': str(e)}
        }), 500


@agent_bp.route('/submit', methods=['POST'])
def submit():
    """
    提交故事包到 InkPath
    
    请求体:
    {
        "files": [{"name": "文件名", "content": "内容"}],
        "storyData": {
            "title": "故事标题",
            "background": "故事背景",
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        files = data.get('files', [])
        
        if not files:
            return jsonify({
                'status': 'error',
                'error': {'message': '没有故事包文件'}
            }), 400
        
        # 从文件提取故事信息
        story_data = _extract_story_data(files)
        
        # 创建故事
        story_service = StoryService()
        story = story_service.create_story(
            title=story_data['title'],
            background=story_data['background'],
            style_rules=story_data.get('style_rules', ''),
            story_pack={
                'evidence_pack': _get_file_content(files, '10_evidence_pack.md'),
                'stance_pack': _get_file_content(files, '20_stance_pack.md'),
                'cast': _get_file_content(files, '30_cast.md'),
                'plot_outline': _get_file_content(files, '40_plot_outline.md'),
                'constraints': _get_file_content(files, '50_constraints.md'),
                'sources': _get_file_content(files, '60_sources.md'),
            }
        )
        
        return jsonify({
            'status': 'success',
            'storyId': story['id'],
            'title': story['title'],
            'url': f'https://inkpath.cc/stories/{story["id"]}'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': {'message': str(e)}
        }), 500


@agent_bp.route('/stories', methods=['GET'])
def list_stories():
    """获取 Agent 创建的故事列表"""
    try:
        bot_id = request.args.get('bot_id')
        
        story_service = StoryService()
        stories = story_service.get_stories(
            creator_bot_id=bot_id,
            limit=100
        )
        
        return jsonify({
            'status': 'success',
            'data': stories
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': {'message': str(e)}
        }), 500


@agent_bp.route('/branches', methods=['GET'])
def list_branches():
    """获取 Agent 创建的分支列表"""
    try:
        bot_id = request.args.get('bot_id')
        
        story_service = StoryService()
        branches = story_service.get_branches(
            creator_bot_id=bot_id,
            limit=100
        )
        
        return jsonify({
            'status': 'success',
            'data': branches
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': {'message': str(e)}
        }), 500


@agent_bp.route('/participations', methods=['GET'])
def list_participations():
    """获取 Agent 参与的续写列表"""
    try:
        bot_id = request.args.get('bot_id')
        
        story_service = StoryService()
        participations = story_service.get_bot_participations(
            bot_id=bot_id,
            limit=100
        )
        
        return jsonify({
            'status': 'success',
            'data': participations
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': {'message': str(e)}
        }), 500


@agent_bp.route('/files', methods=['POST'])
def preview_files():
    """预览故事包文件"""
    try:
        data = request.get_json()
        files = data.get('files', [])
        filename = data.get('filename')
        
        content = _get_file_content(files, filename)
        
        if not content:
            return jsonify({
                'status': 'error',
                'error': {'message': '文件不存在'}
            }), 404
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'content': content
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': {'message': str(e)}
        }), 500


# ============ 辅助函数 ============

def _parse_intent(message: str) -> Dict[str, Any]:
    """解析用户意图"""
    message_lower = message.lower()
    
    # 检查是否是创建故事
    if any(kw in message_lower for kw in ['创建', '写一个', '生成', '创作']):
        return {
            'type': 'create',
            'era': _extract_era(message),
            'genre': _extract_genre(message),
            'style': _extract_style(message),
        }
    
    # 检查是否是修改
    if any(kw in message_lower for kw in ['修改', '调整', '改变', '更新']):
        return {
            'type': 'modify',
            'target': _extract_modify_target(message),
        }
    
    # 检查是否是完善信息
    if any(kw in message_lower for kw in ['完善', '补充', '添加', '更多']):
        return {
            'type': 'complete',
            'fields': _extract_fields(message),
        }
    
    return {
        'type': 'general',
    }


def _generate_response(
    message: str,
    intent: Dict[str, Any],
    history: list,
    current_package: Optional[Dict]
) -> Dict[str, Any]:
    """生成 AI 响应"""
    
    if intent['type'] == 'create':
        return _handle_create(message, intent)
    elif intent['type'] == 'modify':
        return _handle_modify(message, intent, current_package)
    elif intent['type'] == 'complete':
        return _handle_complete(message, intent, current_package)
    else:
        return _handle_general(message, history)


def _handle_create(message: str, intent: Dict[str, Any]) -> Dict[str, Any]:
    """处理创建故事请求"""
    
    # 检查信息是否完整
    missing_fields = []
    if not intent.get('era'):
        missing_fields.append('故事发生的时代背景（如：三国、明朝、现代等）')
    if not intent.get('genre'):
        missing_fields.append('故事类型（如：历史悬疑、科幻、言情等）')
    
    if missing_fields:
        return {
            'text': f'好的，我想帮你创建这个故事！\n\n不过为了更好地创作，我还需要了解一些信息：\n\n' + 
                    '\n'.join([f'• {f}' for f in missing_fields]) +
                    '\n\n请告诉我这些细节，我会据此生成完整的故事包。',
            'storyPackage': {
                'files': [],
                'status': 'incomplete',
                'missingFields': missing_fields
            }
        }
    
    # 信息完整，生成故事包（这里应该调用 LLM）
    # 暂时返回示例响应
    files = _generate_story_package(message, intent)
    
    return {
        'text': f'太棒了！我已经根据你的要求生成了完整的故事包。\n\n故事包包含：\n' +
                '• 00_meta.md - 元数据\n' +
                '• 10_evidence_pack.md - 证据层\n' +
                '• 20_stance_pack.md - 立场层\n' +
                '• 30_cast.md - 角色层\n' +
                '• 40_plot_outline.md - 剧情大纲\n' +
                '• 50_constraints.md - 约束条件\n' +
                '• 60_sources.md - 资料来源\n\n' +
                '你可以在右侧预览所有文件。预览满意后，点击"提交到 InkPath"按钮正式创建故事。',
        'metadata': {
            'intent': 'create',
            'era': intent.get('era'),
            'genre': intent.get('genre'),
        },
        'storyPackage': {
            'files': files,
            'status': 'complete',
        }
    }


def _handle_modify(
    message: str,
    intent: Dict[str, Any],
    current_package: Optional[Dict]
) -> Dict[str, Any]:
    """处理修改故事包请求"""
    # 修改逻辑
    return {
        'text': f'好的，我会帮你修改故事包。\n\n请告诉我具体想要修改什么内容？',
        'storyPackage': current_package or {'files': [], 'status': 'incomplete'}
    }


def _handle_complete(
    message: str,
    intent: Dict[str, Any],
    current_package: Optional[Dict]
) -> Dict[str, Any]:
    """处理完善信息请求"""
    return {
        'text': f'好的，请补充以下信息：\n\n' +
                '\n'.join([f'• {f}' for f in intent.get('fields', [])]),
        'storyPackage': current_package or {'files': [], 'status': 'incomplete'}
    }


def _handle_general(message: str, history: list) -> Dict[str, Any]:
    """处理一般对话"""
    return {
        'text': '我理解了。请告诉我更多关于这个故事的信息，比如：\n\n' +
                '• 你想创作什么类型的故事？\n' +
                '• 故事发生在什么时代？\n' +
                '• 有什么特别想要的情节或角色吗？',
        'storyPackage': {'files': [], 'status': 'incomplete'}
    }


def _extract_era(message: str) -> Optional[str]:
    """提取时代背景"""
    eras = ['三国', '唐朝', '宋朝', '明朝', '清朝', '民国', '现代', '未来', '科幻', '奇幻']
    for era in eras:
        if era in message:
            return era
    return None


def _extract_genre(message: str) -> list:
    """提取故事类型"""
    genres = []
    genre_keywords = {
        '悬疑': ['悬疑', '推理', '破案'],
        '科幻': ['科幻', '太空', '外星人'],
        '历史': ['历史', '古代', '王朝'],
        '言情': ['言情', '爱情', '感情'],
        '战争': ['战争', '军事', '战斗'],
        '谍战': ['谍战', '特务', '间谍'],
    }
    
    for genre, keywords in genre_keywords.items():
        for kw in keywords:
            if kw in message:
                genres.append(genre)
                break
    
    return genres


def _extract_style(message: str) -> Optional[str]:
    """提取风格参考"""
    styles = ['马伯庸', '金庸', '古龙', '指环王', '哈利波特']
    for style in styles:
        if style in message:
            return style
    return None


def _extract_fields(message: str) -> list:
    """提取需要完善的字段"""
    return []  # TODO: 实现字段提取


def _extract_modify_target(message: str) -> str:
    """提取修改目标"""
    return message  # TODO: 实现修改目标提取


def _update_package(
    current_package: Optional[Dict],
    new_data: Dict,
    intent: Dict[str, Any]
) -> Dict[str, Any]:
    """更新故事包状态"""
    if not current_package:
        return new_data
    
    # 合并文件列表
    current_files = current_package.get('files', [])
    new_files = new_data.get('files', [])
    
    # 如果有新文件，添加到列表
    if new_files:
        existing_names = {f['name'] for f in current_files}
        for f in new_files:
            if f['name'] not in existing_names:
                current_files.append(f)
    
    # 更新状态
    current_package['files'] = current_files
    
    if intent['type'] == 'create':
        if current_package['files']:
            current_package['status'] = 'complete'
    elif intent['type'] == 'complete':
        current_package['status'] = 'complete'
    
    return current_package


def _generate_story_package(message: str, intent: Dict[str, Any]) -> list:
    """生成故事包文件（这里应该调用 LLM）"""
    # 示例文件内容
    files = [
        {
            'name': '00_meta.md',
            'content': f"""---
pack_id: "{intent.get('era', 'x')}-{datetime.now().strftime('%Y%m%d')}-0001"
title: "新故事"
subtitle: ""
logline: "{message[:100]}..."
era: "{intent.get('era', '未知')}"
time_window: ["待定"]
geo_scope: ["待定"]
genre: {json.dumps(intent.get('genre', ['故事']))}
tone: ["叙事"]
rating: "PG-13"
canon_policy: "respect_major_events"
---
# 核心冲突
{message}

# 读者预期
读者将与主角一同经历这个故事。

# 创作原则
- 风格参考: {intent.get('style', '无')}
"""
        },
        {
            'name': '10_evidence_pack.md',
            'content': '''# 证据包（Evidence Layer）

## E-001｜
- 载体：
- 时间指向：
- 内容摘述：
- 明显缺口：
- 可靠度：
- 可争论点：
'''
        },
        {
            'name': '20_stance_pack.md',
            'content': '''# 立场包（Stance Layer）

## S-01｜

- 解释权来源：
- 核心利益：
- 核心恐惧：
- 典型口号：
- 对证据的默认解读：
- 代价结构：
'''
        },
        {
            'name': '30_cast.md',
            'content': '''# 角色包（Individual Layer）

## C-01｜

- 身份/阶层：
- 可接触信息：
- 无法接触信息：
- 立场绑定：
- 个人目标：
- 认知盲区：
- 触发点：
- 禁区：
'''
        },
        {
            'name': '40_plot_outline.md',
            'content': '''# 剧情大纲（Plot Outline）

## 信息流设计

### 序章：证据入场
- 核心冲突：
- 信息释放量：
- 立场压力：

### 第一幕：立场施压
...

### 第二幕：真相逼近
...

### 第三幕：抉择时刻
...
'''
        },
        {
            'name': '50_constraints.md',
            'content': '''# 约束与边界（Constraints）

## 硬约束
- 历史大事件不可改写：
- 时间边界：
- 地理边界：

## 软约束
- 视角限制：
- 历史细节：

## 内容边界
- 分级：PG-13
'''
        },
        {
            'name': '60_sources.md',
            'content': '''# 资料来源（Sources）

## 史料（公版/原始）

## 现代研究

## 证据卡对应关系
'''
        },
    ]
    
    return files


def _extract_story_data(files: list) -> Dict[str, Any]:
    """从文件列表提取故事数据"""
    title = '新故事'
    background = ''
    style_rules = ''
    
    for f in files:
        if f['name'] == '00_meta.md':
            content = f['content']
            # 简单解析 YAML front matter
            import re
            title_match = re.search(r'title:\s*"([^"]+)"', content)
            if title_match:
                title = title_match.group(1)
            
            logline_match = re.search(r'logline:\s*"([^"]+)"', content)
            if logline_match:
                background = logline_match.group(1)
            
            era_match = re.search(r'era:\s*"([^"]+)"', content)
            if era_match:
                background = f"{era_match.group(1)}: {background}"
        
        elif f['name'] == '00_meta.md':
            # 提取 style_rules
            pass
    
    return {
        'title': title,
        'background': background,
        'style_rules': style_rules,
    }


def _get_file_content(files: list, filename: str) -> str:
    """从文件列表获取指定文件内容"""
    for f in files:
        if f['name'] == filename:
            return f['content']
    return ''
