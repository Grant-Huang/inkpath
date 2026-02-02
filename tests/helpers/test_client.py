"""测试客户端辅助函数"""
import os
from src.app import create_app
from src.config import Config


class TestConfig(Config):
    """测试配置"""
    TESTING = True
    DATABASE_URL = os.getenv('TEST_DATABASE_URL', 'sqlite:///./test_inkpath.db')


def create_test_app():
    """创建测试应用"""
    app = create_app(TestConfig)
    
    # 初始化测试数据库
    from tests.helpers.test_db import create_test_db
    create_test_db()
    
    return app
