"""Webhook管理测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.webhook_service import (
    validate_webhook_url, update_webhook_url, get_webhook_status
)
from src.services.bot_service import register_bot
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
        import src.api.v1.webhooks as webhooks_module
        webhooks_module.get_db = mock_get_db
        
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
        name="WebhookTestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    return bot, api_key


def test_validate_webhook_url_valid():
    """测试Webhook URL验证（有效）"""
    valid_urls = [
        "https://example.com/webhook",
        "http://localhost:3000/webhook",
        "https://api.example.com/v1/webhook"
    ]
    
    for url in valid_urls:
        is_valid, error = validate_webhook_url(url)
        assert is_valid is True, f"URL {url} should be valid"
        assert error is None


def test_validate_webhook_url_invalid():
    """测试Webhook URL验证（无效）"""
    # 测试空URL
    is_valid, error = validate_webhook_url("")
    assert is_valid is False
    assert "不能为空" in error
    
    # 测试无效格式（没有协议）
    is_valid, error = validate_webhook_url("not-a-url")
    assert is_valid is False
    # urlparse可能解析为相对路径，所以可能返回"必须是HTTP或HTTPS协议"或"必须包含有效的主机名"
    assert "HTTP或HTTPS" in error or "必须包含有效的主机名" in error or "无效的URL格式" in error
    
    # 测试非HTTP/HTTPS协议
    is_valid, error = validate_webhook_url("ftp://example.com/webhook")
    assert is_valid is False
    assert "HTTP或HTTPS" in error
    
    # 测试空主机名
    is_valid, error = validate_webhook_url("https://")
    assert is_valid is False
    assert "必须包含有效的主机名" in error


def test_update_webhook_url(test_db, test_bot):
    """测试更新Webhook URL"""
    bot, _ = test_bot
    
    # 初始webhook_url为None
    assert bot.webhook_url is None
    
    # 更新Webhook URL
    updated_bot = update_webhook_url(
        test_db, bot.id, "https://example.com/webhook"
    )
    
    assert updated_bot.webhook_url == "https://example.com/webhook"


def test_update_webhook_url_invalid(test_db, test_bot):
    """测试更新Webhook URL（无效URL）"""
    bot, _ = test_bot
    
    with pytest.raises(ValueError, match="无效的URL格式|必须是HTTP或HTTPS"):
        update_webhook_url(test_db, bot.id, "not-a-url")


def test_get_webhook_status(test_db, test_bot):
    """测试获取Webhook状态"""
    bot, _ = test_bot
    
    # 初始状态
    status = get_webhook_status(test_db, bot.id)
    assert status['is_configured'] is False
    assert status['webhook_url'] is None
    
    # 设置Webhook URL后
    update_webhook_url(test_db, bot.id, "https://example.com/webhook")
    status = get_webhook_status(test_db, bot.id)
    assert status['is_configured'] is True
    assert status['webhook_url'] == "https://example.com/webhook"


def test_update_webhook_api(client, test_db, test_bot):
    """测试更新Webhook API"""
    bot, api_key = test_bot
    
    response = client.put(
        f'/api/v1/bots/{bot.id}/webhook',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'webhook_url': 'https://example.com/webhook'
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['webhook_url'] == 'https://example.com/webhook'


def test_update_webhook_api_invalid_url(client, test_db, test_bot):
    """测试更新Webhook API（无效URL）"""
    bot, api_key = test_bot
    
    response = client.put(
        f'/api/v1/bots/{bot.id}/webhook',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'webhook_url': 'not-a-url'
        }
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'


def test_get_webhook_status_api(client, test_db, test_bot):
    """测试获取Webhook状态API"""
    bot, api_key = test_bot
    
    # 先设置Webhook URL
    client.put(
        f'/api/v1/bots/{bot.id}/webhook',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'webhook_url': 'https://example.com/webhook'}
    )
    
    # 获取状态
    response = client.get(
        f'/api/v1/bots/{bot.id}/webhook/status',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['is_configured'] is True
    assert data['data']['webhook_url'] == 'https://example.com/webhook'
