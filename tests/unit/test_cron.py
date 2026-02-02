"""定时任务测试"""
import pytest
from datetime import datetime, timedelta
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.story_service import create_story
from src.services.branch_service import create_branch
from src.services.bot_service import register_bot
from src.services.segment_service import create_segment
from src.services.cron_service import check_bot_timeouts, update_bot_activity
from src.models.bot import Bot
import uuid


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
        import src.api.v1.cron as cron_module
        cron_module.get_db = mock_get_db
        
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
        name="CronTestBot",
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
        title="定时任务测试故事",
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
        title="定时任务测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    return branch


def test_update_bot_activity(test_db, test_bot):
    """测试更新Bot活动时间"""
    bot, _ = test_bot
    original_updated_at = bot.updated_at
    
    # 更新活动时间
    update_bot_activity(test_db, bot.id)
    test_db.refresh(bot)
    
    assert bot.updated_at > original_updated_at


def test_check_bot_timeouts_no_timeout(test_db, test_bot):
    """测试正常Bot不扣分"""
    bot, _ = test_bot
    original_reputation = bot.reputation or 0
    
    # 更新Bot活动时间（确保不超时）
    update_bot_activity(test_db, bot.id)
    
    # 检查超时
    results = check_bot_timeouts(test_db)
    
    assert results['timeout_bots_count'] == 0
    assert len(results['processed_bots']) == 0
    
    # 验证Bot声誉未变
    test_db.refresh(bot)
    assert bot.reputation == original_reputation


def test_check_bot_timeouts_with_timeout(test_db, test_bot):
    """测试超时Bot扣分"""
    bot, _ = test_bot
    original_reputation = bot.reputation or 0
    
    # 手动设置updated_at为2小时前（模拟超时）
    from datetime import datetime, timedelta
    bot.updated_at = datetime.utcnow() - timedelta(hours=2)
    test_db.commit()
    test_db.refresh(bot)
    
    # 检查超时
    results = check_bot_timeouts(test_db)
    
    assert results['timeout_bots_count'] == 1
    assert len(results['processed_bots']) == 1
    assert results['processed_bots'][0]['bot_id'] == str(bot.id)
    assert results['processed_bots'][0]['old_reputation'] == original_reputation
    assert results['processed_bots'][0]['new_reputation'] == original_reputation - 5
    
    # 验证Bot声誉已扣分
    test_db.refresh(bot)
    assert bot.reputation == original_reputation - 5


def test_check_bot_timeouts_suspend_on_negative(test_db, test_bot):
    """测试声誉分降到0以下（暂停Bot）"""
    bot, _ = test_bot
    
    # 设置Bot声誉为3（扣5分后会变成-2）
    bot.reputation = 3
    test_db.commit()
    
    # 手动设置updated_at为2小时前（模拟超时）
    bot.updated_at = datetime.utcnow() - timedelta(hours=2)
    test_db.commit()
    test_db.refresh(bot)
    
    # 检查超时
    results = check_bot_timeouts(test_db)
    
    assert results['timeout_bots_count'] == 1
    assert results['processed_bots'][0]['new_reputation'] == -2
    assert results['processed_bots'][0]['was_suspended'] == True
    
    # 验证Bot已被暂停
    test_db.refresh(bot)
    assert bot.reputation == -2
    assert bot.status == 'suspended'


def test_check_bot_timeouts_api(client, test_db, test_bot):
    """测试Bot超时检查API"""
    bot, _ = test_bot
    
    # 手动设置updated_at为2小时前（模拟超时）
    bot.updated_at = datetime.utcnow() - timedelta(hours=2)
    test_db.commit()
    
    # 调用API（需要CRON_SECRET）
    import os
    cron_secret = os.getenv('CRON_SECRET', 'dev-cron-secret-change-in-production')
    
    response = client.post(
        '/api/v1/cron/check-bot-timeouts',
        headers={'Authorization': f'Bearer {cron_secret}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'data' in data
    assert data['data']['timeout_bots_count'] == 1


def test_check_bot_timeouts_api_unauthorized(client):
    """测试Bot超时检查API（未授权）"""
    response = client.post(
        '/api/v1/cron/check-bot-timeouts',
        headers={'Authorization': 'Bearer wrong-secret'}
    )
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['error']['code'] == 'UNAUTHORIZED'
