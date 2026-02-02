"""活跃度得分测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.story_service import create_story
from src.services.branch_service import create_branch, join_branch
from src.services.bot_service import register_bot
from src.services.segment_service import create_segment
from src.services.vote_service import create_or_update_vote
from src.services.activity_service import (
    calculate_activity_score,
    get_activity_score_cached,
    update_activity_score_cache,
    update_all_branch_activity_scores
)
from src.models.user import User
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
        name="ActivityTestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    return bot, api_key


@pytest.fixture
def test_user(test_db):
    """创建测试用户"""
    from src.services.user_service import register_user
    user = register_user(
        db=test_db,
        email="activity@example.com",
        name="活跃度测试用户",
        password="password123"
    )
    return user, "password123"


@pytest.fixture
def test_story(test_db, test_bot):
    """创建测试故事"""
    bot, _ = test_bot
    story = create_story(
        db=test_db,
        title="活跃度测试故事",
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
        title="活跃度测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    return branch


def test_calculate_activity_score_basic(test_db, test_branch):
    """测试基本活跃度得分计算"""
    score = calculate_activity_score(test_db, test_branch.id)
    
    # 新分支：0投票得分 * 0.5 + 0续写 * 0.3 + 1Bot * 0.2 = 0.2
    assert score == 0.2


def test_calculate_activity_score_with_segments(test_db, test_branch, test_bot):
    """测试有续写的活跃度得分"""
    bot, _ = test_bot
    
    # 创建3个续写段（需要至少150字）
    for i in range(3):
        content = f"续写段 {i+1}。这是测试内容，用于验证活跃度得分计算。" * 20
        create_segment(
            db=test_db,
            branch_id=test_branch.id,
            bot_id=bot.id,
            content=content
        )
    
    score = calculate_activity_score(test_db, test_branch.id)
    
    # 0投票得分 * 0.5 + 3续写 * 0.3 + 1Bot * 0.2 = 0.9 + 0.2 = 1.1
    assert score == 1.1


def test_calculate_activity_score_with_votes(test_db, test_branch, test_bot, test_user):
    """测试有投票的活跃度得分"""
    bot, _ = test_bot
    user, _ = test_user
    
    # 创建续写段（需要至少150字）
    content = "续写段内容。这是测试内容，用于验证活跃度得分计算。" * 20
    segment = create_segment(
        db=test_db,
        branch_id=test_branch.id,
        bot_id=bot.id,
        content=content
    )
    
    # 人类用户投票（+1分，权重1.0）
    create_or_update_vote(
        db=test_db,
        voter_id=user.id,
        voter_type='human',
        target_type='segment',
        target_id=segment.id,
        vote=1
    )
    
    score = calculate_activity_score(test_db, test_branch.id)
    
    # 1投票得分（1.0 * 1 = 1.0） * 0.5 + 1续写 * 0.3 + 1Bot * 0.2 = 0.5 + 0.3 + 0.2 = 1.0
    assert abs(score - 1.0) < 0.01  # 允许浮点数误差


def test_calculate_activity_score_with_multiple_bots(test_db, test_branch, test_bot):
    """测试多个Bot的活跃度得分"""
    bot1, _ = test_bot
    
    # 创建第二个Bot
    bot2, _ = register_bot(
        db=test_db,
        name="ActivityTestBot2",
        model="claude-sonnet-4",
        language="zh"
    )
    
    # Bot2加入分支
    join_branch(test_db, test_branch.id, bot2.id)
    
    score = calculate_activity_score(test_db, test_branch.id)
    
    # 0投票得分 * 0.5 + 0续写 * 0.3 + 2Bot * 0.2 = 0.4
    assert score == 0.4


def test_get_activity_score_cached(test_db, test_branch):
    """测试获取活跃度得分（带缓存）"""
    score1 = get_activity_score_cached(test_db, test_branch.id)
    score2 = get_activity_score_cached(test_db, test_branch.id)
    
    # 两次应该返回相同的结果
    assert score1 == score2
    assert score1 == 0.2


def test_update_activity_score_cache(test_db, test_branch, test_bot):
    """测试更新活跃度得分缓存"""
    bot, _ = test_bot
    
    # 创建续写段（需要至少150字）
    content = "续写段内容。这是测试内容，用于验证活跃度得分计算。" * 20
    create_segment(
        db=test_db,
        branch_id=test_branch.id,
        bot_id=bot.id,
        content=content
    )
    
    # 更新缓存
    update_activity_score_cache(test_db, test_branch.id)
    
    # 获取缓存的值
    cached_score = get_activity_score_cached(test_db, test_branch.id)
    
    # 应该反映新的续写段
    assert abs(cached_score - 0.5) < 0.01  # 0 * 0.5 + 1 * 0.3 + 1 * 0.2 = 0.5


def test_update_all_branch_activity_scores(test_db, test_story, test_bot):
    """测试更新所有分支的活跃度得分"""
    bot, _ = test_bot
    
    # 创建多个分支
    branches = []
    for i in range(3):
        branch = create_branch(
            db=test_db,
            story_id=test_story.id,
            title=f"分支 {i+1}",
            description="描述",
            creator_bot_id=bot.id
        )
        branches.append(branch)
    
    # 更新所有分支的活跃度得分
    results = update_all_branch_activity_scores(test_db)
    
    # 应该包括主分支和创建的3个分支，至少3个
    assert results['updated_count'] >= 3  # 至少3个（可能包括主分支）
    assert len(results['errors']) == 0
