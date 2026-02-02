"""用户认证测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.user_service import register_user, authenticate_user, hash_password, verify_password


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


def test_hash_and_verify_password():
    """测试密码加密和验证"""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password  # 加密后应该不同
    assert verify_password(password, hashed) is True  # 验证应该通过
    assert verify_password("wrong_password", hashed) is False  # 错误密码应该失败


def test_register_user_success(test_db):
    """测试用户注册成功"""
    user = register_user(
        db=test_db,
        email="test@example.com",
        name="Test User",
        password="password123"
    )
    
    assert user is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.password_hash is not None
    assert user.password_hash != "password123"  # 密码应该被加密
    assert verify_password("password123", user.password_hash) is True


def test_register_user_duplicate_email(test_db):
    """测试重复邮箱验证"""
    register_user(
        db=test_db,
        email="duplicate@example.com",
        name="First User",
        password="password123"
    )
    
    # 尝试注册相同邮箱应该失败
    with pytest.raises(ValueError, match="已被注册"):
        register_user(
            db=test_db,
            email="duplicate@example.com",
            name="Second User",
            password="password456"
        )


def test_authenticate_user_success(test_db):
    """测试用户认证成功"""
    user = register_user(
        db=test_db,
        email="auth@example.com",
        name="Auth User",
        password="password123"
    )
    
    authenticated_user = authenticate_user(test_db, "auth@example.com", "password123")
    
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    assert authenticated_user.email == user.email


def test_authenticate_user_wrong_password(test_db):
    """测试错误密码认证失败"""
    register_user(
        db=test_db,
        email="test@example.com",
        name="Test User",
        password="correct_password"
    )
    
    authenticated_user = authenticate_user(test_db, "test@example.com", "wrong_password")
    
    assert authenticated_user is None


def test_authenticate_user_nonexistent(test_db):
    """测试不存在用户认证失败"""
    authenticated_user = authenticate_user(test_db, "nonexistent@example.com", "password")
    
    assert authenticated_user is None


def test_register_user_api(client, test_db):
    """测试用户注册API"""
    response = client.post('/api/v1/auth/user/register', json={
        'email': 'newuser@example.com',
        'name': 'New User',
        'password': 'password123'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'user_id' in data['data']
    assert data['data']['email'] == 'newuser@example.com'
    assert data['data']['name'] == 'New User'


def test_register_user_api_missing_fields(client):
    """测试用户注册API缺少字段"""
    response = client.post('/api/v1/auth/user/register', json={
        'email': 'test@example.com'
        # 缺少name和password
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'VALIDATION_ERROR'


def test_register_user_api_duplicate_email(client, test_db):
    """测试用户注册API重复邮箱"""
    # 第一次注册
    client.post('/api/v1/auth/user/register', json={
        'email': 'duplicate@example.com',
        'name': 'First User',
        'password': 'password123'
    })
    
    # 第二次注册相同邮箱
    response = client.post('/api/v1/auth/user/register', json={
        'email': 'duplicate@example.com',
        'name': 'Second User',
        'password': 'password456'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert '已被注册' in data['error']['message']


def test_register_user_api_short_password(client):
    """测试用户注册API密码太短"""
    response = client.post('/api/v1/auth/user/register', json={
        'email': 'test@example.com',
        'name': 'Test User',
        'password': '12345'  # 少于6位
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert '密码长度至少6位' in data['error']['message']


def test_login_user_api_success(client, test_db):
    """测试用户登录API成功"""
    # 先注册用户
    register_response = client.post('/api/v1/auth/user/register', json={
        'email': 'login@example.com',
        'name': 'Login User',
        'password': 'password123'
    })
    
    assert register_response.status_code == 201
    
    # 登录
    response = client.post('/api/v1/auth/login', json={
        'email': 'login@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'token' in data['data']
    assert 'user' in data['data']
    assert data['data']['user']['email'] == 'login@example.com'


def test_login_user_api_wrong_password(client, test_db):
    """测试用户登录API错误密码"""
    # 先注册用户
    client.post('/api/v1/auth/user/register', json={
        'email': 'test@example.com',
        'name': 'Test User',
        'password': 'correct_password'
    })
    
    # 使用错误密码登录
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrong_password'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'UNAUTHORIZED'


def test_login_user_api_nonexistent(client):
    """测试用户登录API不存在用户"""
    response = client.post('/api/v1/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'UNAUTHORIZED'
