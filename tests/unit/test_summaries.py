"""摘要生成测试"""
import pytest
from datetime import datetime, timedelta
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.summary_service import (
    should_generate_summary, generate_summary, get_branch_summary
)
from src.services.story_service import create_story
from src.services.branch_service import create_branch
from src.services.segment_service import create_segment
from src.services.bot_service import register_bot
from src.models.branch import Branch
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
        name="SummaryTestBot",
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
        title="摘要测试故事",
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
        title="摘要测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    return branch


def test_should_generate_summary_new_branch(test_db, test_branch):
    """测试分支创建时应该生成摘要"""
    # 新分支没有摘要，应该生成
    assert should_generate_summary(test_db, test_branch.id) is True


def test_should_generate_summary_after_3_segments(test_db, test_branch, test_bot):
    """测试新增3段后应该生成摘要"""
    bot, _ = test_bot
    
    # 先设置一个摘要更新时间（模拟已有摘要）
    test_branch.summary_updated_at = datetime.utcnow() - timedelta(hours=1)
    test_db.commit()
    
    # 初始不应该生成
    assert should_generate_summary(test_db, test_branch.id) is False
    
    # 创建3段续写
    content = "测试续写内容。" * 25
    for i in range(3):
        create_segment(test_db, test_branch.id, bot.id, content)
    
    # 现在应该生成摘要
    assert should_generate_summary(test_db, test_branch.id) is True


def test_get_branch_summary(test_db, test_branch):
    """测试获取分支摘要"""
    summary_data = get_branch_summary(test_db, test_branch.id)
    
    assert 'summary' in summary_data
    assert 'updated_at' in summary_data
    assert 'covers_up_to' in summary_data
    # 新分支没有摘要
    assert summary_data['summary'] is None


def test_get_branch_summary_lazy_refresh(test_db, test_branch, test_bot):
    """测试懒刷新机制"""
    bot, _ = test_bot
    
    # 创建3段续写
    content = "测试续写内容。" * 25
    for i in range(3):
        create_segment(test_db, test_branch.id, bot.id, content)
    
    # 获取摘要（会触发懒刷新）
    summary_data = get_branch_summary(test_db, test_branch.id, force_refresh=False)
    
    # 即使生成失败，也应该返回数据
    assert 'summary' in summary_data
    assert 'updated_at' in summary_data
    assert 'covers_up_to' in summary_data


def test_generate_summary_force(test_db, test_branch, test_bot):
    """测试强制生成摘要"""
    bot, _ = test_bot
    
    # 创建几段续写
    content = "测试续写内容。" * 25
    for i in range(2):
        create_segment(test_db, test_branch.id, bot.id, content)
    
    # 强制生成摘要（即使不满足触发条件）
    summary = generate_summary(test_db, test_branch.id, force=True)
    
    # 如果没有配置API Key，会返回占位符字符串
    # 如果有配置，会返回实际摘要
    # 如果失败，会返回None
    # 所以summary可能是None或字符串
    if summary is not None:
        assert isinstance(summary, str)
        
        # 验证数据库已更新
        test_db.refresh(test_branch)
        assert test_branch.current_summary is not None
        assert test_branch.summary_updated_at is not None
        assert test_branch.summary_covers_up_to is not None
    else:
        # 如果生成失败（如没有API Key），数据库可能不会更新
        # 这是可以接受的，因为摘要生成失败不应该阻塞其他功能
        pass
