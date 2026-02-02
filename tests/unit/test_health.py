"""健康检查API测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'message' in data
    assert 'version' in data
