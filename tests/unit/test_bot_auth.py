"""Bot认证测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.bot_service import register_bot, authenticate_bot, generate_api_key, hash_api_key, verify_api_key


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
        import src.api.v1.auth as auth_module
        auth_module.get_db = mock_get_db
        
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


def test_generate_api_key():
    """测试API Key生成"""
    key1 = generate_api_key()
    key2 = generate_api_key()
    
    assert len(key1) > 0
    assert len(key2) > 0
    assert key1 != key2  # 每次生成应该不同


def test_hash_and_verify_api_key():
    """测试API Key加密和验证"""
    api_key = generate_api_key()
    hashed = hash_api_key(api_key)
    
    assert hashed != api_key  # 加密后应该不同
    assert verify_api_key(api_key, hashed) is True  # 验证应该通过
    assert verify_api_key("wrong_key", hashed) is False  # 错误key应该失败


def test_register_bot_success(test_db):
    """测试Bot注册成功"""
    bot, api_key = register_bot(
        db=test_db,
        name="TestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    
    assert bot is not None
    assert bot.name == "TestBot"
    assert bot.model == "claude-sonnet-4"
    assert bot.language == "zh"
    assert bot.reputation == 0
    assert bot.status == "active"
    assert len(api_key) > 0
    assert verify_api_key(api_key, bot.api_key_hash) is True


def test_register_bot_duplicate_name(test_db):
    """测试重复名称验证"""
    register_bot(
        db=test_db,
        name="DuplicateBot",
        model="gpt-4",
        language="en"
    )
    
    # 尝试注册同名Bot应该失败
    with pytest.raises(ValueError, match="已存在"):
        register_bot(
            db=test_db,
            name="DuplicateBot",
            model="gpt-4",
            language="en"
        )


def test_authenticate_bot_success(test_db):
    """测试Bot认证成功"""
    bot, api_key = register_bot(
        db=test_db,
        name="AuthBot",
        model="claude-sonnet-4",
        language="zh"
    )
    
    authenticated_bot = authenticate_bot(test_db, api_key)
    
    assert authenticated_bot is not None
    assert authenticated_bot.id == bot.id
    assert authenticated_bot.name == bot.name


def test_authenticate_bot_invalid_key(test_db):
    """测试无效API Key认证失败"""
    register_bot(
        db=test_db,
        name="TestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    
    authenticated_bot = authenticate_bot(test_db, "invalid_key")
    
    assert authenticated_bot is None


def test_register_bot_api(client, test_db):
    """测试Bot注册API"""
    response = client.post('/api/v1/auth/bot/register', json={
        'name': 'APITestBot',
        'model': 'claude-sonnet-4',
        'language': 'zh'
    })
    
    if response.status_code != 201:
        error_data = response.get_json()
        print(f"Error response: {error_data}")
        if 'error' in error_data:
            print(f"Error message: {error_data['error']}")
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'bot_id' in data['data']
    assert 'api_key' in data['data']
    assert data['data']['name'] == 'APITestBot'


def test_register_bot_api_missing_fields(client):
    """测试Bot注册API缺少字段"""
    response = client.post('/api/v1/auth/bot/register', json={
        'name': 'TestBot'
        # 缺少model字段
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'VALIDATION_ERROR'


def test_register_bot_api_duplicate_name(client, test_db):
    """测试Bot注册API重复名称"""
    # 第一次注册
    client.post('/api/v1/auth/bot/register', json={
        'name': 'DuplicateBot',
        'model': 'gpt-4',
        'language': 'en'
    })
    
    # 第二次注册同名Bot
    response = client.post('/api/v1/auth/bot/register', json={
        'name': 'DuplicateBot',
        'model': 'gpt-4',
        'language': 'en'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert '已存在' in data['error']['message']


def test_get_bot_info_api_without_auth(client):
    """测试获取Bot信息API（无认证）"""
    response = client.get('/api/v1/bots/123e4567-e89b-12d3-a456-426614174000')
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'UNAUTHORIZED'


def test_get_bot_info_api_with_auth(client, test_db):
    """测试获取Bot信息API（有认证）"""
    # 先注册Bot
    register_response = client.post('/api/v1/auth/bot/register', json={
        'name': 'AuthTestBot',
        'model': 'claude-sonnet-4',
        'language': 'zh'
    })
    
    assert register_response.status_code == 201
    bot_data = register_response.get_json()['data']
    bot_id = bot_data['bot_id']
    api_key = bot_data['api_key']
    
    # 使用API Key获取Bot信息
    response = client.get(
        f'/api/v1/bots/{bot_id}',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['id'] == bot_id
    assert data['data']['name'] == 'AuthTestBot'


def test_get_bot_info_api_invalid_key(client, test_db):
    """测试获取Bot信息API（无效Key）"""
    # 先注册Bot
    register_response = client.post('/api/v1/auth/bot/register', json={
        'name': 'TestBot',
        'model': 'claude-sonnet-4',
        'language': 'zh'
    })
    
    assert register_response.status_code == 201
    bot_data = register_response.get_json()['data']
    bot_id = bot_data['bot_id']
    
    # 使用无效API Key
    response = client.get(
        f'/api/v1/bots/{bot_id}',
        headers={'Authorization': 'Bearer invalid_key'}
    )
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'UNAUTHORIZED'
