"""连续性校验测试"""
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from werkzeug.exceptions import UnprocessableEntity
from src.services.coherence_service import (
    get_previous_segments,
    format_segments_for_coherence,
    check_coherence
)
from src.services.segment_service import create_segment
from src.models.segment import Segment
from src.models.branch import Branch
from src.models.story import Story
from src.models.bot import Bot
from src.config import Config
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_test_db()
    session = get_test_session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        drop_test_db(engine)


@pytest.fixture
def mock_branch(db_session):
    """创建测试分支"""
    story = Story(
        id=uuid.uuid4(),
        title="测试故事",
        background="测试背景",
        language="zh",
        min_length=50,
        max_length=500,
        owner_type="human",  # 必需字段
        status="active"
    )
    db_session.add(story)
    db_session.commit()
    
    branch = Branch(
        id=uuid.uuid4(),
        story_id=story.id,
        title="测试分支",
        status="active"
    )
    db_session.add(branch)
    db_session.commit()
    
    return branch


@pytest.fixture
def mock_bot(db_session):
    """创建测试Bot"""
    bot = Bot(
        id=uuid.uuid4(),
        name="测试Bot",
        model="claude-haiku",  # 必需字段
        api_key_hash="test_hash"
    )
    db_session.add(bot)
    db_session.commit()
    
    return bot


def test_get_previous_segments(db_session, mock_branch):
    """测试获取前N段续写"""
    # 创建5段续写
    segments = []
    for i in range(5):
        segment = Segment(
            id=uuid.uuid4(),
            branch_id=mock_branch.id,
            content=f"第{i+1}段内容",
            sequence_order=i+1
        )
        db_session.add(segment)
        segments.append(segment)
    db_session.commit()
    
    # 获取前3段
    previous = get_previous_segments(db_session, mock_branch.id, limit=3)
    assert len(previous) == 3
    assert previous[0].sequence_order == 3
    assert previous[1].sequence_order == 4
    assert previous[2].sequence_order == 5
    
    # 获取前10段（实际只有5段）
    previous = get_previous_segments(db_session, mock_branch.id, limit=10)
    assert len(previous) == 5


def test_format_segments_for_coherence(db_session, mock_branch):
    """测试格式化续写段"""
    segments = []
    for i in range(3):
        segment = Segment(
            id=uuid.uuid4(),
            branch_id=mock_branch.id,
            content=f"第{i+1}段内容",
            sequence_order=i+1
        )
        db_session.add(segment)
        segments.append(segment)
    db_session.commit()
    
    formatted = format_segments_for_coherence(segments)
    assert "第1段：" in formatted
    assert "第2段：" in formatted
    assert "第3段：" in formatted
    assert "第1段内容" in formatted


def test_format_segments_empty():
    """测试格式化空续写段列表"""
    formatted = format_segments_for_coherence([])
    assert "暂无前面的续写内容" in formatted


@patch('src.services.coherence_service.Config.ENABLE_COHERENCE_CHECK', False)
def test_check_coherence_disabled(db_session, mock_branch):
    """测试连续性校验未启用时直接通过"""
    passed, score, error = check_coherence(db_session, mock_branch.id, "新内容")
    assert passed is True
    assert score == 0.0
    assert error is None


@patch('src.services.coherence_service.Config.ENABLE_COHERENCE_CHECK', True)
@patch('src.services.coherence_service.Config.ANTHROPIC_API_KEY', '')
def test_check_coherence_no_api_key(db_session, mock_branch):
    """测试未配置API Key时跳过校验"""
    passed, score, error = check_coherence(db_session, mock_branch.id, "新内容")
    assert passed is True
    assert score == 0.0
    assert error is None


@patch('src.services.coherence_service.Config.ENABLE_COHERENCE_CHECK', True)
@patch('src.services.coherence_service.Config.ANTHROPIC_API_KEY', 'test-key')
@patch('src.services.coherence_service.Config.COHERENCE_THRESHOLD', 4)
@patch('src.services.coherence_service.anthropic.Anthropic')
def test_check_coherence_high_score(mock_anthropic, db_session, mock_branch):
    """测试高分通过"""
    # Mock LLM响应
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="8")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
    
    passed, score, error = check_coherence(db_session, mock_branch.id, "新内容")
    assert passed is True
    assert score == 8.0
    assert error is None


@patch('src.services.coherence_service.Config.ENABLE_COHERENCE_CHECK', True)
@patch('src.services.coherence_service.Config.ANTHROPIC_API_KEY', 'test-key')
@patch('src.services.coherence_service.Config.COHERENCE_THRESHOLD', 4)
@patch('src.services.coherence_service.anthropic.Anthropic')
def test_check_coherence_low_score(mock_anthropic, db_session, mock_branch):
    """测试低分拒绝"""
    # Mock LLM响应
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="3")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
    
    passed, score, error = check_coherence(db_session, mock_branch.id, "新内容")
    assert passed is False
    assert score == 3.0
    assert "连续性校验未通过" in error
    assert "评分：3.0" in error


@patch('src.services.coherence_service.Config.ENABLE_COHERENCE_CHECK', True)
@patch('src.services.coherence_service.Config.ANTHROPIC_API_KEY', 'test-key')
@patch('src.services.coherence_service.anthropic.Anthropic')
def test_check_coherence_llm_failure(mock_anthropic, db_session, mock_branch):
    """测试LLM API失败时不阻塞续写"""
    # Mock LLM抛出异常
    mock_anthropic.side_effect = Exception("API调用失败")
    
    passed, score, error = check_coherence(db_session, mock_branch.id, "新内容")
    assert passed is True  # 失败时不阻塞
    assert score == 0.0
    assert error is None


@patch('src.services.coherence_service.Config.ENABLE_COHERENCE_CHECK', True)
@patch('src.services.coherence_service.Config.ANTHROPIC_API_KEY', 'test-key')
@patch('src.services.coherence_service.Config.COHERENCE_THRESHOLD', 4)
@patch('src.services.coherence_service.anthropic.Anthropic')
def test_create_segment_with_coherence_check(mock_anthropic, db_session, mock_branch, mock_bot):
    """测试续写提交时连续性校验"""
    from src.models.bot_branch_membership import BotBranchMembership
    
    # Bot加入分支
    membership = BotBranchMembership(
        branch_id=mock_branch.id,
        bot_id=mock_bot.id,
        joined_at_order=1
    )
    db_session.add(membership)
    db_session.commit()
    
    # Mock LLM响应（高分通过）
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="8")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client
    
    # 创建续写段（应该通过）
    segment = create_segment(
        db_session,
        mock_branch.id,
        mock_bot.id,
        "这是一段新的续写内容，长度足够满足要求。"
    )
    
    assert segment is not None
    assert segment.coherence_score == 8.0
    
    # Mock LLM响应（低分拒绝）
    mock_response.content = [MagicMock(text="2")]
    
    # 应该抛出UnprocessableEntity异常
    with pytest.raises(UnprocessableEntity) as exc_info:
        create_segment(
            db_session,
            mock_branch.id,
            mock_bot.id,
            "这是一段不连贯的内容。"
        )
    
    assert "连续性校验未通过" in str(exc_info.value)
