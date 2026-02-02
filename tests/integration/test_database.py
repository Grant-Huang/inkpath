"""数据库连接测试"""
import pytest
from sqlalchemy import text
from src.config import Config
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    engine = create_test_db()
    session = get_test_session(engine)
    try:
        yield session
    finally:
        session.close()
        # 关闭引擎连接
        engine.dispose()
        drop_test_db(engine)


def test_database_connection(test_db):
    """测试数据库连接"""
    result = test_db.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_database_url_configured():
    """测试数据库URL已配置"""
    assert Config.DATABASE_URL is not None
    # 支持postgresql和sqlite
    assert Config.DATABASE_URL.startswith(('postgresql://', 'sqlite://'))


def test_create_tables(test_db):
    """测试创建所有表"""
    from sqlalchemy import inspect
    inspector = inspect(test_db.bind)
    tables = inspector.get_table_names()
    
    # 检查关键表是否存在
    expected_tables = [
        'users', 'bots', 'stories', 'branches', 'segments',
        'pinned_posts', 'bot_branch_membership', 'human_branch_membership',
        'votes', 'comments', 'bot_reputation_log'
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table {table} should exist"
