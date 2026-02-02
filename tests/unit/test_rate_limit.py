"""速率限制测试"""
import pytest
import time
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.story_service import create_story
from src.services.branch_service import create_branch
from src.services.bot_service import register_bot
from src.services.user_service import register_user
from src.services.segment_service import create_segment
from src.services.comment_service import create_comment
from src.services.vote_service import create_or_update_vote
from redis import Redis
from src.config import Config


@pytest.fixture
def client(test_db):
    """创建测试客户端"""
    app = create_app(TestConfig)
    app.config['TESTING'] = True
    app.config['TEST_DB'] = test_db
    
    # 替换get_db函数
    from src.database import get_db as original_get_db
    def mock_get_db():
        yield test_db
    
    # 在应用上下文中替换get_db
    with app.app_context():
        import src.api.v1.segments as segments_module
        import src.api.v1.branches as branches_module
        import src.api.v1.comments as comments_module
        import src.api.v1.votes as votes_module
        segments_module.get_db = mock_get_db
        branches_module.get_db = mock_get_db
        comments_module.get_db = mock_get_db
        votes_module.get_db = mock_get_db
        
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
def redis_client():
    """创建Redis客户端（用于清理速率限制）"""
    client = Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
        decode_responses=True
    )
    yield client
    # 清理测试数据
    keys = client.keys('LIMITER:*')
    if keys:
        client.delete(*keys)


@pytest.fixture
def test_bot(test_db):
    """创建测试Bot"""
    bot, api_key = register_bot(
        db=test_db,
        name="RateLimitTestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    return bot, api_key


@pytest.fixture
def test_user(test_db):
    """创建测试用户"""
    user = register_user(
        db=test_db,
        email="ratelimit@example.com",
        name="速率限制测试用户",
        password="password123"
    )
    return user, "password123"


@pytest.fixture
def test_story(test_db, test_bot):
    """创建测试故事"""
    bot, _ = test_bot
    story = create_story(
        db=test_db,
        title="速率限制测试故事",
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
        title="速率限制测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    return branch


def test_segment_rate_limit(client, test_db, test_branch, test_bot, redis_client):
    """测试续写速率限制（每分支每小时2次）"""
    bot, api_key = test_bot
    
    # 清理速率限制
    redis_client.flushdb()
    
    # 第一次续写 - 应该成功
    content1 = "这是第一次续写内容。" * 20  # 确保长度足够
    response1 = client.post(
        f'/api/v1/branches/{test_branch.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content1}
    )
    assert response1.status_code == 201
    
    # 第二次续写 - 应该成功
    content2 = "这是第二次续写内容。" * 20
    response2 = client.post(
        f'/api/v1/branches/{test_branch.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content2}
    )
    assert response2.status_code == 201
    
    # 第三次续写 - 应该被限制（429）
    content3 = "这是第三次续写内容。" * 20
    response3 = client.post(
        f'/api/v1/branches/{test_branch.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content3}
    )
    assert response3.status_code == 429
    # Flask-Limiter可能返回纯文本或JSON，检查响应内容
    if response3.is_json:
        data = response3.get_json()
        assert 'error' in data or 'RATE_LIMIT_EXCEEDED' in str(data)
    else:
        # 可能是纯文本响应
        assert '429' in str(response3.status_code) or 'rate limit' in response3.get_data(as_text=True).lower()


def test_branch_create_rate_limit(client, test_db, test_story, test_bot, redis_client):
    """测试创建分支速率限制（每小时1次）"""
    bot, api_key = test_bot
    
    # 清理速率限制
    redis_client.flushdb()
    
    # 第一次创建分支 - 应该成功
    response1 = client.post(
        f'/api/v1/stories/{test_story.id}/branches',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '第一个分支',
            'description': '描述1'
        }
    )
    assert response1.status_code == 201
    
    # 第二次创建分支 - 应该被限制（429）
    response2 = client.post(
        f'/api/v1/stories/{test_story.id}/branches',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '第二个分支',
            'description': '描述2'
        }
    )
    assert response2.status_code == 429
    # Flask-Limiter可能返回纯文本或JSON
    if response2.is_json:
        data = response2.get_json()
        assert 'error' in data or 'RATE_LIMIT_EXCEEDED' in str(data)


def test_comment_rate_limit(client, test_db, test_branch, test_bot, redis_client):
    """测试评论速率限制（每小时10次）"""
    bot, api_key = test_bot
    
    # 清理速率限制
    redis_client.flushdb()
    
    # 创建10条评论 - 应该都成功
    for i in range(10):
        response = client.post(
            f'/api/v1/branches/{test_branch.id}/comments',
            headers={'Authorization': f'Bearer {api_key}'},
            json={'content': f'评论 {i+1}'}
        )
        assert response.status_code == 201, f"第{i+1}条评论应该成功"
    
    # 第11条评论 - 应该被限制（429）
    response11 = client.post(
        f'/api/v1/branches/{test_branch.id}/comments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': '第11条评论'}
    )
    assert response11.status_code == 429
    # Flask-Limiter可能返回纯文本或JSON
    if response11.is_json:
        data = response11.get_json()
        assert 'error' in data or 'RATE_LIMIT_EXCEEDED' in str(data)


def test_join_branch_rate_limit(client, test_db, test_story, test_bot, redis_client):
    """测试加入分支速率限制（每小时5次）"""
    bot, api_key = test_bot
    
    # 清理速率限制
    redis_client.flushdb()
    
    # 创建多个分支
    branches = []
    for i in range(6):
        branch = create_branch(
            db=test_db,
            story_id=test_story.id,
            title=f'分支 {i+1}',
            description='描述',
            creator_bot_id=bot.id
        )
        branches.append(branch)
    
    # 加入前5个分支 - 应该都成功
    for i in range(5):
        response = client.post(
            f'/api/v1/branches/{branches[i].id}/join',
            headers={'Authorization': f'Bearer {api_key}'}
        )
        assert response.status_code == 200, f"加入第{i+1}个分支应该成功"
    
    # 加入第6个分支 - 应该被限制（429）
    response6 = client.post(
        f'/api/v1/branches/{branches[5].id}/join',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    assert response6.status_code == 429
    # Flask-Limiter可能返回纯文本或JSON
    if response6.is_json:
        data = response6.get_json()
        assert 'error' in data or 'RATE_LIMIT_EXCEEDED' in str(data)


def test_vote_rate_limit(client, test_db, test_branch, test_user, redis_client):
    """测试投票速率限制（每小时20次）"""
    user, password = test_user
    
    # 先登录获取JWT
    login_response = client.post('/api/v1/auth/login', json={
        'email': 'ratelimit@example.com',
        'password': 'password123'
    })
    jwt_token = login_response.get_json()['data']['token']
    
    # 清理速率限制
    redis_client.flushdb()
    
    # 创建20个续写段用于投票
    bot, api_key = test_bot
    segments = []
    for i in range(20):
        content = f"续写段 {i+1}。" * 20
        segment = create_segment(
            db=test_db,
            branch_id=test_branch.id,
            bot_id=bot.id,
            content=content
        )
        segments.append(segment)
    
    # 对前20个段投票 - 应该都成功
    for i in range(20):
        response = client.post(
            '/api/v1/votes',
            headers={'Authorization': f'Bearer {jwt_token}'},
            json={
                'target_type': 'segment',
                'target_id': str(segments[i].id),
                'vote': 1
            }
        )
        assert response.status_code == 201, f"第{i+1}次投票应该成功"
    
    # 第21次投票 - 应该被限制（429）
    response21 = client.post(
        '/api/v1/votes',
        headers={'Authorization': f'Bearer {jwt_token}'},
        json={
            'target_type': 'segment',
            'target_id': str(segments[0].id),
            'vote': 1
        }
    )
    assert response21.status_code == 429
    # Flask-Limiter可能返回纯文本或JSON
    if response21.is_json:
        data = response21.get_json()
        assert 'error' in data or 'RATE_LIMIT_EXCEEDED' in str(data)


def test_segment_rate_limit_per_branch(client, test_db, test_story, test_bot, redis_client):
    """测试续写速率限制是按分支独立的（每个分支每小时2次）"""
    bot, api_key = test_bot
    
    # 清理速率限制
    redis_client.flushdb()
    
    # 创建两个分支
    branch1 = create_branch(
        db=test_db,
        story_id=test_story.id,
        title='分支1',
        description='描述',
        creator_bot_id=bot.id
    )
    branch2 = create_branch(
        db=test_db,
        story_id=test_story.id,
        title='分支2',
        description='描述',
        creator_bot_id=bot.id
    )
    
    # 在分支1中续写2次
    content1 = "分支1续写1。" * 20
    response1 = client.post(
        f'/api/v1/branches/{branch1.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content1}
    )
    assert response1.status_code == 201
    
    content2 = "分支1续写2。" * 20
    response2 = client.post(
        f'/api/v1/branches/{branch1.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content2}
    )
    assert response2.status_code == 201
    
    # 分支1的第3次续写应该被限制
    content3 = "分支1续写3。" * 20
    response3 = client.post(
        f'/api/v1/branches/{branch1.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content3}
    )
    assert response3.status_code == 429
    
    # 但分支2的续写应该不受影响（可以续写2次）
    content4 = "分支2续写1。" * 20
    response4 = client.post(
        f'/api/v1/branches/{branch2.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content4}
    )
    assert response4.status_code == 201
    
    content5 = "分支2续写2。" * 20
    response5 = client.post(
        f'/api/v1/branches/{branch2.id}/segments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': content5}
    )
    assert response5.status_code == 201
