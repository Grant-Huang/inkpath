"""续写管理测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.segment_service import (
    create_segment, get_segments_by_branch, count_words, validate_segment_length, check_turn_order
)
from src.services.story_service import create_story
from src.services.branch_service import create_branch, join_branch
from src.services.bot_service import register_bot
from src.models.segment import Segment
import uuid


@pytest.fixture
def client(test_db):
    """创建测试客户端"""
    app = create_app(TestConfig)
    app.config['TEST_DB'] = test_db
    
    # 替换get_db函数
    from src.database import get_db as original_get_db
    def mock_get_db():
        yield test_db
    
    # 在应用上下文中替换get_db
    with app.app_context():
        import src.api.v1.segments as segments_module
        segments_module.get_db = mock_get_db
        
        with app.test_client() as client:
            yield client


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_test_db()
    session = get_test_session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        drop_test_db(engine)


@pytest.fixture
def test_bot(test_db):
    """创建测试Bot"""
    bot, api_key = register_bot(
        db=test_db,
        name="SegmentTestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    return bot, api_key


@pytest.fixture
def test_story(test_db, test_bot):
    """创建测试故事"""
    bot, _ = test_bot
    story = create_story(
        db=test_db,
        title="续写测试故事",
        background="背景",
        owner_id=bot.id,
        owner_type='bot',
        language="zh",
        min_length=150,
        max_length=500
    )
    return story


@pytest.fixture
def test_branch(test_db, test_story, test_bot):
    """创建测试分支"""
    bot, _ = test_bot
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="续写测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    return branch


def test_count_words_chinese():
    """测试中文字数统计"""
    text = "这是一个测试文本，包含中文字符。"
    count = count_words(text, 'zh')
    assert count == 14  # 14个中文字符


def test_count_words_english():
    """测试英文单词数统计"""
    text = "This is a test text with English words."
    count = count_words(text, 'en')
    assert count == 8  # 8个单词


def test_validate_segment_length_valid(test_story):
    """测试续写段长度验证（有效）"""
    content = "这是一个有效的续写内容。" * 20  # 约200字
    is_valid, error = validate_segment_length(content, test_story)
    assert is_valid is True
    assert error is None


def test_validate_segment_length_too_short(test_story):
    """测试续写段长度验证（太短）"""
    content = "太短"  # 只有2字
    is_valid, error = validate_segment_length(content, test_story)
    assert is_valid is False
    assert "太短" in error


def test_validate_segment_length_too_long(test_story):
    """测试续写段长度验证（太长）"""
    content = "这是一个很长的续写内容。" * 100  # 约1000字
    is_valid, error = validate_segment_length(content, test_story)
    assert is_valid is False
    assert "太长" in error


def test_create_segment_success(test_db, test_branch, test_bot):
    """测试创建续写段成功"""
    bot, _ = test_bot
    
    content = "这是第一段续写内容。" * 25  # 约200字
    
    segment = create_segment(
        db=test_db,
        branch_id=test_branch.id,
        bot_id=bot.id,
        content=content
    )
    
    assert segment is not None
    assert segment.content == content
    assert segment.sequence_order == 1
    assert segment.bot_id == bot.id


def test_create_segment_sequence_order(test_db, test_branch, test_bot):
    """测试sequence_order自动递增"""
    bot, _ = test_bot
    
    content1 = "第一段续写内容。" * 25  # 约175字
    segment1 = create_segment(
        db=test_db,
        branch_id=test_branch.id,
        bot_id=bot.id,
        content=content1
    )
    
    assert segment1.sequence_order == 1
    
    # 创建第二个Bot并加入
    bot2, _ = register_bot(
        db=test_db,
        name="SegmentTestBot2",
        model="gpt-4",
        language="zh"
    )
    join_branch(test_db, test_branch.id, bot2.id)
    
    content2 = "第二段续写内容。" * 25  # 约175字
    segment2 = create_segment(
        db=test_db,
        branch_id=test_branch.id,
        bot_id=bot2.id,
        content=content2
    )
    
    assert segment2.sequence_order == 2


def test_create_segment_wrong_turn(test_db, test_branch, test_bot):
    """测试轮次检查（不是你的轮次）"""
    bot1, _ = test_bot
    
    # Bot1写第一段
    content1 = "第一段续写内容。" * 25  # 约175字
    create_segment(
        db=test_db,
        branch_id=test_branch.id,
        bot_id=bot1.id,
        content=content1
    )
    
    # 创建Bot2并加入
    bot2, _ = register_bot(
        db=test_db,
        name="SegmentTestBot2",
        model="gpt-4",
        language="zh"
    )
    join_branch(test_db, test_branch.id, bot2.id)
    
    # Bot1尝试写第二段（应该是Bot2的轮次）
    content2 = "第二段续写内容。" * 25  # 约175字
    with pytest.raises(ValueError, match="不是你的轮次"):
        create_segment(
            db=test_db,
            branch_id=test_branch.id,
            bot_id=bot1.id,
            content=content2
        )


def test_get_segments_by_branch(test_db, test_branch, test_bot):
    """测试获取分支的续写段列表"""
    bot, _ = test_bot
    
    # 创建多个续写段
    for i in range(3):
        content = f"第{i+1}段续写内容。" * 25  # 约175字
        create_segment(
            db=test_db,
            branch_id=test_branch.id,
            bot_id=bot.id,
            content=content
        )
    
    segments, total = get_segments_by_branch(test_db, test_branch.id, limit=10)
    
    assert len(segments) == 3
    assert total == 3
    # 验证按顺序返回
    assert segments[0].sequence_order == 1
    assert segments[1].sequence_order == 2
    assert segments[2].sequence_order == 3


def test_create_segment_api(client, test_db, test_branch, test_bot):
    """测试提交续写API"""
    bot, api_key = test_bot
    
    content = "这是通过API提交的续写内容。" * 25  # 约200字
    
    response = client.post(
        f'/api/v1/branches/{test_branch.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'content': content
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'segment' in data['data']
    assert data['data']['segment']['content'] == content
    assert data['data']['segment']['sequence_order'] == 1


def test_create_segment_api_wrong_turn(client, test_db, test_branch, test_bot):
    """测试提交续写API（不是你的轮次）"""
    bot1, api_key1 = test_bot
    
    # 先创建Bot2并加入（在Bot1写第一段之前）
    bot2_response = client.post('/api/v1/auth/bot/register', json={
        'name': 'SegmentTestBot2',
        'model': 'gpt-4',
        'language': 'zh'
    })
    bot2_api_key = bot2_response.get_json()['data']['api_key']
    
    client.post(
        f'/api/v1/branches/{test_branch.id}/join',
        headers={'Authorization': f'Bearer {bot2_api_key}'}
    )
    
    # Bot1写第一段
    content1 = "第一段续写内容。" * 25  # 约175字
    client.post(
        f'/api/v1/branches/{test_branch.id}/segments',
        headers={'Authorization': f'Bearer {api_key1}'},
        json={'content': content1}
    )
    
    # Bot1尝试写第二段（应该是Bot2的轮次）
    content2 = "第二段续写内容。" * 25  # 约175字
    response = client.post(
        f'/api/v1/branches/{test_branch.id}/segments',
        headers={'Authorization': f'Bearer {api_key1}'},
        json={'content': content2}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert '不是你的轮次' in data['error']['message']


def test_create_segment_api_too_short(client, test_db, test_branch, test_bot):
    """测试提交续写API（内容太短）"""
    bot, api_key = test_bot
    
    response = client.post(
        f'/api/v1/branches/{test_branch.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'content': '太短'  # 只有2字
        }
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert '太短' in data['error']['message']


def test_list_segments_api(client, test_db, test_branch, test_bot):
    """测试获取续写列表API"""
    bot, api_key = test_bot
    
    # 创建几个续写段
    for i in range(2):
        content = f"第{i+1}段续写内容。" * 25  # 约175字
        client.post(
            f'/api/v1/branches/{test_branch.id}/segments',
            headers={'Authorization': f'Bearer {api_key}'},
            json={'content': content}
        )
    
    # 获取列表
    response = client.get(f'/api/v1/branches/{test_branch.id}/segments')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'segments' in data['data']
    assert len(data['data']['segments']) == 2
    # 验证按顺序返回
    assert data['data']['segments'][0]['sequence_order'] == 1
    assert data['data']['segments'][1]['sequence_order'] == 2
