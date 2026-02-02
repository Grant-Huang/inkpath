"""投票系统测试"""
import pytest
from datetime import datetime, timedelta
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.vote_service import (
    calculate_bot_weight, is_new_bot, is_same_branch, calculate_vote_weight,
    check_vote_spam, check_self_vote, create_or_update_vote, calculate_score,
    get_vote_summary
)
from src.services.story_service import create_story
from src.services.branch_service import create_branch, join_branch
from src.services.segment_service import create_segment
from src.services.bot_service import register_bot
from src.models.vote import Vote
from src.models.bot import Bot
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
        name="VoteTestBot",
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
        title="投票测试故事",
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
        title="投票测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    return branch


def test_calculate_bot_weight():
    """测试Bot权重计算"""
    assert calculate_bot_weight(0) == 0.3  # 新Bot
    assert calculate_bot_weight(50) == 0.3  # 新Bot
    assert calculate_bot_weight(51) == 0.5  # 活跃Bot
    assert calculate_bot_weight(200) == 0.5  # 活跃Bot
    assert calculate_bot_weight(201) == 0.8  # 资深Bot
    assert calculate_bot_weight(500) == 0.8  # 资深Bot（上限）


def test_is_new_bot(test_db, test_bot):
    """测试新Bot检查"""
    bot, _ = test_bot
    
    # 刚注册的Bot应该是新Bot
    assert is_new_bot(test_db, bot.id) is True
    
    # 修改创建时间为25小时前
    bot.created_at = datetime.utcnow() - timedelta(hours=25)
    test_db.commit()
    
    # 应该不是新Bot
    assert is_new_bot(test_db, bot.id) is False


def test_is_same_branch(test_db, test_branch, test_bot):
    """测试同分支检查"""
    bot, _ = test_bot
    
    # Bot在分支中，应该是同分支
    assert is_same_branch(test_db, bot.id, 'branch', test_branch.id) is True
    
    # 创建另一个Bot和分支
    bot2, _ = register_bot(test_db, "VoteTestBot2", "gpt-4", "zh")
    story2 = create_story(test_db, "Story2", "Background", bot2.id, 'bot', language="zh", min_length=150, max_length=500)
    branch2 = create_branch(test_db, story2.id, "Branch2", "Desc", bot2.id)
    
    # Bot1不在分支2中
    assert is_same_branch(test_db, bot.id, 'branch', branch2.id) is False


def test_calculate_vote_weight_human(test_db, test_branch):
    """测试人类投票权重（固定1.0）"""
    # 创建用户（这里简化，实际应该从User模型获取）
    user_id = uuid.uuid4()
    
    weight = calculate_vote_weight(
        test_db, user_id, 'human', 'branch', test_branch.id
    )
    assert weight == 1.0


def test_calculate_vote_weight_bot(test_db, test_branch, test_bot):
    """测试Bot投票权重"""
    bot, _ = test_bot
    
    # 新Bot权重为0
    weight = calculate_vote_weight(
        test_db, bot.id, 'bot', 'branch', test_branch.id
    )
    assert weight == 0.0  # 新Bot 24小时内权重为0
    
    # 修改Bot创建时间为25小时前，声誉为100
    bot.created_at = datetime.utcnow() - timedelta(hours=25)
    bot.reputation = 100
    test_db.commit()
    
    # 同分支Bot投票，权重打0.5折
    weight = calculate_vote_weight(
        test_db, bot.id, 'bot', 'branch', test_branch.id
    )
    assert weight == 0.25  # 0.5 * 0.5 = 0.25


def test_check_self_vote(test_db, test_branch, test_bot):
    """测试自票检查"""
    bot, _ = test_bot
    
    # 创建续写段
    content = "测试续写内容。" * 25
    segment = create_segment(
        test_db, test_branch.id, bot.id, content
    )
    
    # Bot给自己的续写段投票，应该检测为自票
    is_self, error_msg = check_self_vote(
        test_db, bot.id, 'bot', 'segment', segment.id
    )
    assert is_self is True
    assert "不能给自己的续写段投票" in error_msg
    
    # Bot给其他续写段投票，不是自票
    bot2, _ = register_bot(test_db, "VoteTestBot2", "gpt-4", "zh")
    join_branch(test_db, test_branch.id, bot2.id)
    content2 = "第二段续写内容。" * 25
    segment2 = create_segment(
        test_db, test_branch.id, bot2.id, content2
    )
    
    is_self, _ = check_self_vote(
        test_db, bot.id, 'bot', 'segment', segment2.id
    )
    assert is_self is False


def test_check_vote_spam(test_db, test_branch, test_bot):
    """测试刷票检查"""
    bot, _ = test_bot
    
    # 修改Bot创建时间为25小时前
    bot.created_at = datetime.utcnow() - timedelta(hours=25)
    bot.reputation = 100
    test_db.commit()
    
    # 创建多个不同的目标（分支或续写段）来避免唯一约束冲突
    # 创建21个不同的分支来投票
    story = test_branch.story_id
    for i in range(21):
        branch = create_branch(
            test_db, story, f"Branch{i}", f"Desc{i}", bot.id
        )
        vote = Vote(
            voter_id=bot.id,
            voter_type='bot',
            target_type='branch',
            target_id=branch.id,
            vote=1,
            effective_weight=0.5,
            created_at=datetime.utcnow() - timedelta(minutes=30)
        )
        test_db.add(vote)
    test_db.commit()
    
    # 应该检测为刷票
    is_spam, error_msg = check_vote_spam(test_db, bot.id)
    assert is_spam is True
    assert "超过20次" in error_msg


def test_create_vote_human(test_db, test_branch):
    """测试人类投票"""
    # 创建用户（简化，实际应该从User模型获取）
    user_id = uuid.uuid4()
    
    vote, score = create_or_update_vote(
        test_db, user_id, 'human', 'branch', test_branch.id, 1
    )
    
    assert vote is not None
    assert vote.vote == 1
    assert vote.effective_weight == 1.0
    assert score == 1.0


def test_create_vote_bot(test_db, test_branch, test_bot):
    """测试Bot投票"""
    bot, _ = test_bot
    
    # 修改Bot创建时间为25小时前，声誉为100
    bot.created_at = datetime.utcnow() - timedelta(hours=25)
    bot.reputation = 100
    test_db.commit()
    
    vote, score = create_or_update_vote(
        test_db, bot.id, 'bot', 'branch', test_branch.id, 1
    )
    
    assert vote is not None
    assert vote.vote == 1
    # 同分支Bot投票，权重打0.5折：0.5 * 0.5 = 0.25
    assert vote.effective_weight == 0.25
    assert score == 0.25


def test_update_vote(test_db, test_branch):
    """测试更新投票"""
    user_id = uuid.uuid4()
    
    # 创建投票
    vote1, score1 = create_or_update_vote(
        test_db, user_id, 'human', 'branch', test_branch.id, 1
    )
    assert score1 == 1.0
    
    # 更新为负票
    vote2, score2 = create_or_update_vote(
        test_db, user_id, 'human', 'branch', test_branch.id, -1
    )
    
    assert vote1.id == vote2.id  # 同一个投票
    assert vote2.vote == -1
    assert score2 == -1.0


def test_calculate_score(test_db, test_branch):
    """测试得分计算"""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    
    # 两个人类正票
    create_or_update_vote(test_db, user1_id, 'human', 'branch', test_branch.id, 1)
    create_or_update_vote(test_db, user2_id, 'human', 'branch', test_branch.id, 1)
    
    score = calculate_score(test_db, 'branch', test_branch.id)
    assert score == 2.0


def test_get_vote_summary(test_db, test_branch):
    """测试投票汇总"""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    
    # 两个人类正票，一个负票
    create_or_update_vote(test_db, user1_id, 'human', 'branch', test_branch.id, 1)
    create_or_update_vote(test_db, user2_id, 'human', 'branch', test_branch.id, 1)
    
    # 创建用户3并投负票
    user3_id = uuid.uuid4()
    create_or_update_vote(test_db, user3_id, 'human', 'branch', test_branch.id, -1)
    
    summary = get_vote_summary(test_db, 'branch', test_branch.id)
    
    assert summary['total_score'] == 1.0  # 2 - 1 = 1
    assert summary['upvotes'] == 2
    assert summary['downvotes'] == 1
    assert summary['human_votes'] == 3
    assert summary['bot_votes'] == 0
