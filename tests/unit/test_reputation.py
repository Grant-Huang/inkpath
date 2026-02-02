"""Bot声誉系统测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.reputation_service import (
    update_reputation, get_reputation_history, get_reputation_summary
)
from src.services.bot_service import register_bot
import uuid


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
        name="ReputationTestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    return bot, api_key


def test_update_reputation_add_points(test_db, test_bot):
    """测试声誉加分"""
    bot, _ = test_bot
    
    # 初始声誉为0
    assert bot.reputation == 0
    
    # 成功提交续写，+5
    updated_bot = update_reputation(
        test_db, bot.id, 5, "成功提交续写", 'segment', uuid.uuid4()
    )
    
    assert updated_bot.reputation == 5
    assert updated_bot.status == 'active'


def test_update_reputation_subtract_points(test_db, test_bot):
    """测试声誉扣分"""
    bot, _ = test_bot
    
    # 先加一些分
    update_reputation(test_db, bot.id, 10, "测试加分")
    
    # 续写段获得人类负票，-8
    updated_bot = update_reputation(
        test_db, bot.id, -8, "续写段获得人类负票", 'vote', uuid.uuid4()
    )
    
    assert updated_bot.reputation == 2  # 10 - 8 = 2
    assert updated_bot.status == 'active'


def test_update_reputation_suspend(test_db, test_bot):
    """测试声誉降到0以下（暂停）"""
    bot, _ = test_bot
    
    # 初始声誉为0
    assert bot.reputation == 0
    assert bot.status == 'active'
    
    # 扣分导致声誉降到0以下
    updated_bot = update_reputation(
        test_db, bot.id, -5, "超时未续写"
    )
    
    assert updated_bot.reputation == -5
    assert updated_bot.status == 'suspended'  # 自动暂停


def test_get_reputation_history(test_db, test_bot):
    """测试获取声誉历史"""
    bot, _ = test_bot
    
    # 添加几条声誉记录
    update_reputation(test_db, bot.id, 5, "成功提交续写", 'segment', uuid.uuid4())
    update_reputation(test_db, bot.id, 10, "续写段获得人类正票", 'vote', uuid.uuid4())
    update_reputation(test_db, bot.id, -8, "续写段获得人类负票", 'vote', uuid.uuid4())
    
    # 获取历史
    history = get_reputation_history(test_db, bot.id, limit=10)
    
    assert len(history) == 3
    # 验证按时间倒序
    assert history[0].change == -8
    assert history[1].change == 10
    assert history[2].change == 5


def test_get_reputation_summary(test_db, test_bot):
    """测试获取声誉汇总"""
    bot, _ = test_bot
    
    # 添加几条声誉记录
    update_reputation(test_db, bot.id, 5, "成功提交续写")
    update_reputation(test_db, bot.id, 10, "续写段获得人类正票")
    
    summary = get_reputation_summary(test_db, bot.id)
    
    assert summary['current_reputation'] == 15
    assert summary['status'] == 'active'
    assert summary['total_changes'] == 2
