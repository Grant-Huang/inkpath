"""故事管理测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.story_service import create_story, get_story_by_id, get_stories, update_story_style_rules
from src.services.bot_service import register_bot
from src.services.user_service import register_user
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
        import src.api.v1.stories as stories_module
        stories_module.get_db = mock_get_db
        
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
        name="StoryTestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    return bot, api_key


@pytest.fixture
def test_user(test_db):
    """创建测试用户"""
    user = register_user(
        db=test_db,
        email="storytest@example.com",
        name="Story Test User",
        password="password123"
    )
    return user


def test_create_story_success(test_db, test_bot):
    """测试创建故事成功"""
    bot, _ = test_bot
    
    story = create_story(
        db=test_db,
        title="测试故事",
        background="这是一个测试故事的背景",
        owner_id=bot.id,
        owner_type='bot',
        style_rules="使用第三人称叙述",
        language="zh"
    )
    
    assert story is not None
    assert story.title == "测试故事"
    assert story.background == "这是一个测试故事的背景"
    assert story.owner_id == bot.id
    assert story.owner_type == 'bot'
    assert story.language == 'zh'
    assert story.status == 'active'


def test_create_story_invalid_owner_type(test_db, test_bot):
    """测试创建故事无效owner_type"""
    bot, _ = test_bot
    
    with pytest.raises(ValueError, match="owner_type"):
        create_story(
            db=test_db,
            title="测试故事",
            background="背景",
            owner_id=bot.id,
            owner_type='invalid_type',
            language="zh"
        )


def test_get_story_by_id(test_db, test_bot):
    """测试根据ID获取故事"""
    bot, _ = test_bot
    
    story = create_story(
        db=test_db,
        title="测试故事",
        background="背景",
        owner_id=bot.id,
        owner_type='bot',
        language="zh"
    )
    
    found_story = get_story_by_id(test_db, story.id)
    
    assert found_story is not None
    assert found_story.id == story.id
    assert found_story.title == story.title


def test_get_stories_list(test_db, test_bot):
    """测试获取故事列表"""
    bot, _ = test_bot
    
    # 创建多个故事
    for i in range(3):
        create_story(
            db=test_db,
            title=f"故事{i+1}",
            background=f"背景{i+1}",
            owner_id=bot.id,
            owner_type='bot',
            language="zh"
        )
    
    stories = get_stories(test_db, limit=10)
    
    assert len(stories) == 3


def test_update_story_style_rules(test_db, test_bot):
    """测试更新故事规范"""
    bot, _ = test_bot
    
    story = create_story(
        db=test_db,
        title="测试故事",
        background="背景",
        owner_id=bot.id,
        owner_type='bot',
        style_rules="旧规范",
        language="zh"
    )
    
    updated_story = update_story_style_rules(test_db, story.id, "新规范")
    
    assert updated_story is not None
    assert updated_story.style_rules == "新规范"


def test_create_story_api_with_bot(client, test_db, test_bot):
    """测试Bot创建故事API"""
    bot, api_key = test_bot
    
    response = client.post('/api/v1/stories', 
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': 'API测试故事',
            'background': '这是通过API创建的故事',
            'style_rules': '使用第一人称',
            'language': 'zh'
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['title'] == 'API测试故事'
    assert data['data']['owner_type'] == 'bot'


def test_create_story_api_without_auth(client):
    """测试创建故事API（无认证）"""
    response = client.post('/api/v1/stories', json={
        'title': '测试故事',
        'background': '背景'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'UNAUTHORIZED'


def test_create_story_api_missing_fields(client, test_db, test_bot):
    """测试创建故事API缺少字段"""
    bot, api_key = test_bot
    
    response = client.post('/api/v1/stories',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '测试故事'
            # 缺少background
        }
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'VALIDATION_ERROR'


def test_get_story_list_api(client, test_db, test_bot):
    """测试获取故事列表API"""
    bot, api_key = test_bot
    
    # 先创建故事
    client.post('/api/v1/stories',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '列表测试故事',
            'background': '背景'
        }
    )
    
    # 获取列表
    response = client.get('/api/v1/stories')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'stories' in data['data']
    assert len(data['data']['stories']) > 0


def test_get_story_detail_api(client, test_db, test_bot):
    """测试获取故事详情API"""
    bot, api_key = test_bot
    
    # 先创建故事
    create_response = client.post('/api/v1/stories',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '详情测试故事',
            'background': '这是详情测试故事的背景内容',
            'style_rules': '测试规范'
        }
    )
    
    assert create_response.status_code == 201
    story_id = create_response.get_json()['data']['id']
    
    # 获取详情
    response = client.get(f'/api/v1/stories/{story_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['id'] == story_id
    assert data['data']['title'] == '详情测试故事'
    assert data['data']['background'] == '这是详情测试故事的背景内容'
    assert 'branches_count' in data['data']


def test_get_story_detail_not_found(client):
    """测试获取不存在的故事"""
    fake_id = str(uuid.uuid4())
    response = client.get(f'/api/v1/stories/{fake_id}')
    
    assert response.status_code == 404
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'NOT_FOUND'


def test_update_story_style_rules_api(client, test_db, test_bot):
    """测试更新故事规范API"""
    bot, api_key = test_bot
    
    # 先创建故事
    create_response = client.post('/api/v1/stories',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '更新测试故事',
            'background': '背景',
            'style_rules': '旧规范'
        }
    )
    
    assert create_response.status_code == 201
    story_id = create_response.get_json()['data']['id']
    
    # 更新规范
    response = client.patch(f'/api/v1/stories/{story_id}/style-rules',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'style_rules': '新规范'
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['style_rules'] == '新规范'
