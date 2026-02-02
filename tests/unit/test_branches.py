"""分支管理测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.branch_service import (
    create_branch, get_branch_by_id, get_branches_by_story,
    get_branch_tree, join_branch, leave_branch, get_next_bot_in_queue
)
from src.services.story_service import create_story
from src.services.bot_service import register_bot
from src.models.segment import Segment
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
        import src.api.v1.branches as branches_module
        branches_module.get_db = mock_get_db
        
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
        name="BranchTestBot",
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
        title="分支测试故事",
        background="背景",
        owner_id=bot.id,
        owner_type='bot',
        language="zh"
    )
    return story


def test_create_branch_success(test_db, test_story, test_bot):
    """测试创建分支成功"""
    bot, _ = test_bot
    
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="测试分支",
        description="这是测试分支",
        creator_bot_id=bot.id
    )
    
    assert branch is not None
    assert branch.title == "测试分支"
    assert branch.story_id == test_story.id
    assert branch.creator_bot_id == bot.id


def test_create_branch_auto_join(test_db, test_story, test_bot):
    """测试创建分支时Bot自动加入"""
    bot, _ = test_bot
    
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="自动加入测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    
    # 检查Bot是否自动加入
    from src.models.bot_branch_membership import BotBranchMembership
    membership = test_db.query(BotBranchMembership).filter(
        BotBranchMembership.bot_id == bot.id,
        BotBranchMembership.branch_id == branch.id
    ).first()
    
    assert membership is not None
    assert membership.join_order == 1


def test_get_branch_by_id(test_db, test_story, test_bot):
    """测试根据ID获取分支"""
    bot, _ = test_bot
    
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="查询测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    
    found_branch = get_branch_by_id(test_db, branch.id)
    
    assert found_branch is not None
    assert found_branch.id == branch.id
    assert found_branch.title == branch.title


def test_get_branches_by_story(test_db, test_story, test_bot):
    """测试获取故事的所有分支"""
    bot, _ = test_bot
    
    # 创建多个分支
    for i in range(3):
        create_branch(
            db=test_db,
            story_id=test_story.id,
            title=f"分支{i+1}",
            description=f"描述{i+1}",
            creator_bot_id=bot.id
        )
    
    branches, total = get_branches_by_story(test_db, test_story.id, limit=10)
    
    # 应该包含主干线分支（创建故事时自动创建）+ 3个新分支 = 4个
    assert total >= 3
    assert len(branches) >= 3


def test_get_branch_tree(test_db, test_story, test_bot):
    """测试获取分支树"""
    bot, _ = test_bot
    
    # 创建父分支
    parent_branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="父分支",
        description="父分支描述",
        creator_bot_id=bot.id
    )
    
    # 创建子分支
    child_branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="子分支",
        description="子分支描述",
        creator_bot_id=bot.id,
        parent_branch_id=parent_branch.id
    )
    
    tree = get_branch_tree(test_db, test_story.id)
    
    assert len(tree) > 0
    # 检查树结构（简化检查）
    assert isinstance(tree, list)


def test_join_branch(test_db, test_story, test_bot):
    """测试Bot加入分支"""
    bot, _ = test_bot
    
    # 创建分支
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="加入测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    
    # 创建另一个Bot
    bot2, _ = register_bot(
        db=test_db,
        name="BranchTestBot2",
        model="gpt-4",
        language="zh"
    )
    
    # Bot2加入分支
    membership = join_branch(test_db, branch.id, bot2.id)
    
    assert membership is not None
    assert membership.bot_id == bot2.id
    assert membership.branch_id == branch.id
    assert membership.join_order == 2  # Bot1是1，Bot2是2


def test_join_branch_duplicate(test_db, test_story, test_bot):
    """测试重复加入分支（更新）"""
    bot, _ = test_bot
    
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="重复加入测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    
    # 第一次加入（已经通过创建分支自动加入）
    from src.models.bot_branch_membership import BotBranchMembership
    membership1 = test_db.query(BotBranchMembership).filter(
        BotBranchMembership.bot_id == bot.id,
        BotBranchMembership.branch_id == branch.id
    ).first()
    
    assert membership1 is not None  # 确保已自动加入
    
    # 再次加入（应该返回现有记录）
    membership2 = join_branch(test_db, branch.id, bot.id)
    
    assert membership2 is not None
    # BotBranchMembership是复合主键，没有单独的id字段
    assert membership2.bot_id == membership1.bot_id
    assert membership2.branch_id == membership1.branch_id


def test_leave_branch(test_db, test_story, test_bot):
    """测试Bot离开分支"""
    bot, _ = test_bot
    
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="离开测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    
    # 离开分支
    success = leave_branch(test_db, branch.id, bot.id)
    
    assert success is True
    
    # 验证已离开
    from src.models.bot_branch_membership import BotBranchMembership
    membership = test_db.query(BotBranchMembership).filter(
        BotBranchMembership.bot_id == bot.id,
        BotBranchMembership.branch_id == branch.id
    ).first()
    
    assert membership is None


def test_get_next_bot_in_queue_empty(test_db, test_story, test_bot):
    """测试空队列获取下一个Bot"""
    bot, _ = test_bot
    
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="队列测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    
    # 没有续写段，应该返回第一个Bot
    next_bot = get_next_bot_in_queue(test_db, branch.id)
    
    assert next_bot is not None
    assert next_bot.id == bot.id


def test_get_next_bot_in_queue_rotation(test_db, test_story, test_bot):
    """测试轮次队列轮转"""
    bot1, _ = test_bot
    
    branch = create_branch(
        db=test_db,
        story_id=test_story.id,
        title="轮转测试分支",
        description="描述",
        creator_bot_id=bot1.id
    )
    
    # 创建第二个Bot并加入
    bot2, _ = register_bot(
        db=test_db,
        name="BranchTestBot2",
        model="gpt-4",
        language="zh"
    )
    join_branch(test_db, branch.id, bot2.id)
    
    # 创建第一个续写段（Bot1写的）
    segment1 = Segment(
        branch_id=branch.id,
        bot_id=bot1.id,
        content="第一段内容",
        sequence_order=1
    )
    test_db.add(segment1)
    test_db.commit()
    
    # 获取下一个Bot（应该是Bot2）
    next_bot = get_next_bot_in_queue(test_db, branch.id)
    
    assert next_bot is not None
    assert next_bot.id == bot2.id


def test_create_branch_api(client, test_db, test_story, test_bot):
    """测试创建分支API"""
    bot, api_key = test_bot
    
    response = client.post(
        f'/api/v1/stories/{test_story.id}/branches',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': 'API测试分支',
            'description': '这是通过API创建的分支'
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['title'] == 'API测试分支'
    assert data['data']['creator_bot_id'] == str(bot.id)


def test_get_branch_detail_api(client, test_db, test_story, test_bot):
    """测试获取分支详情API"""
    bot, api_key = test_bot
    
    # 先创建分支
    create_response = client.post(
        f'/api/v1/stories/{test_story.id}/branches',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '详情测试分支',
            'description': '描述'
        }
    )
    
    assert create_response.status_code == 201
    branch_id = create_response.get_json()['data']['id']
    
    # 获取详情
    response = client.get(f'/api/v1/branches/{branch_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['id'] == branch_id
    assert 'segments_count' in data['data']
    assert 'active_bots_count' in data['data']


def test_list_branches_api(client, test_db, test_story, test_bot):
    """测试获取故事的所有分支API"""
    bot, api_key = test_bot
    
    # 创建几个分支
    for i in range(2):
        client.post(
            f'/api/v1/stories/{test_story.id}/branches',
            headers={'Authorization': f'Bearer {api_key}'},
            json={
                'title': f'列表测试分支{i+1}',
                'description': '描述'
            }
        )
    
    # 获取列表
    response = client.get(f'/api/v1/stories/{test_story.id}/branches')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'branches' in data['data']
    assert len(data['data']['branches']) >= 2  # 至少包含创建的2个分支


def test_join_branch_api(client, test_db, test_story, test_bot):
    """测试Bot加入分支API"""
    bot, api_key = test_bot
    
    # 创建分支
    create_response = client.post(
        f'/api/v1/stories/{test_story.id}/branches',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '加入测试分支',
            'description': '描述'
        }
    )
    
    assert create_response.status_code == 201
    branch_id = create_response.get_json()['data']['id']
    
    # 创建第二个Bot
    bot2_response = client.post('/api/v1/auth/bot/register', json={
        'name': 'JoinTestBot2',
        'model': 'gpt-4',
        'language': 'zh'
    })
    bot2_api_key = bot2_response.get_json()['data']['api_key']
    
    # Bot2加入分支
    join_response = client.post(
        f'/api/v1/branches/{branch_id}/join',
        headers={'Authorization': f'Bearer {bot2_api_key}'}
    )
    
    assert join_response.status_code == 200
    data = join_response.get_json()
    assert data['status'] == 'success'
    assert data['data']['join_order'] == 2  # Bot1是1，Bot2是2


def test_leave_branch_api(client, test_db, test_story, test_bot):
    """测试Bot离开分支API"""
    bot, api_key = test_bot
    
    # 创建分支（Bot自动加入）
    create_response = client.post(
        f'/api/v1/stories/{test_story.id}/branches',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '离开测试分支',
            'description': '描述'
        }
    )
    
    assert create_response.status_code == 201
    branch_id = create_response.get_json()['data']['id']
    
    # 离开分支
    leave_response = client.post(
        f'/api/v1/branches/{branch_id}/leave',
        headers={'Authorization': f'Bearer {api_key}'}
    )
    
    assert leave_response.status_code == 200
    data = leave_response.get_json()
    assert data['status'] == 'success'


def test_get_next_bot_api(client, test_db, test_story, test_bot):
    """测试获取下一个Bot API"""
    bot, api_key = test_bot
    
    # 创建分支
    create_response = client.post(
        f'/api/v1/stories/{test_story.id}/branches',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'title': '队列测试分支',
            'description': '描述'
        }
    )
    
    assert create_response.status_code == 201
    branch_id = create_response.get_json()['data']['id']
    
    # 获取下一个Bot
    response = client.get(f'/api/v1/branches/{branch_id}/next-bot')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'bot' in data['data']
    assert data['data']['bot']['id'] == str(bot.id)  # 应该是第一个Bot
