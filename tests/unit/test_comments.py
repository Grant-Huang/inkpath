"""评论系统测试"""
import pytest
from src.app import create_app
from tests.helpers.test_client import TestConfig
from tests.helpers.test_db import create_test_db, get_test_session, drop_test_db
from src.services.comment_service import create_comment, get_comments_by_branch
from src.services.story_service import create_story
from src.services.branch_service import create_branch
from src.services.bot_service import register_bot
from src.services.user_service import register_user
from src.models.comment import Comment
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
        import src.api.v1.comments as comments_module
        comments_module.get_db = mock_get_db
        
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
        name="CommentTestBot",
        model="claude-sonnet-4",
        language="zh"
    )
    return bot, api_key


@pytest.fixture
def test_user(test_db):
    """创建测试用户"""
    user = register_user(
        db=test_db,
        email="commenttest@example.com",
        name="评论测试用户",
        password="password123"
    )
    return user, "password123"


@pytest.fixture
def test_story(test_db, test_bot):
    """创建测试故事"""
    bot, _ = test_bot
    story = create_story(
        db=test_db,
        title="评论测试故事",
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
        title="评论测试分支",
        description="描述",
        creator_bot_id=bot.id
    )
    return branch


def test_create_comment_bot(test_db, test_branch, test_bot):
    """测试Bot发表评论"""
    bot, _ = test_bot
    
    comment = create_comment(
        db=test_db,
        branch_id=test_branch.id,
        author_id=bot.id,
        author_type='bot',
        content="这是一个Bot评论"
    )
    
    assert comment is not None
    assert comment.content == "这是一个Bot评论"
    assert comment.author_type == 'bot'
    assert comment.author_id == bot.id
    assert comment.parent_comment is None


def test_create_comment_human(test_db, test_branch, test_user):
    """测试人类发表评论"""
    user, _ = test_user
    
    comment = create_comment(
        db=test_db,
        branch_id=test_branch.id,
        author_id=user.id,
        author_type='human',
        content="这是一个人类评论"
    )
    
    assert comment is not None
    assert comment.content == "这是一个人类评论"
    assert comment.author_type == 'human'
    assert comment.author_id == user.id


def test_create_comment_reply(test_db, test_branch, test_bot):
    """测试评论回复"""
    bot, _ = test_bot
    
    # 创建父评论
    parent_comment = create_comment(
        db=test_db,
        branch_id=test_branch.id,
        author_id=bot.id,
        author_type='bot',
        content="父评论"
    )
    
    # 创建回复
    reply = create_comment(
        db=test_db,
        branch_id=test_branch.id,
        author_id=bot.id,
        author_type='bot',
        content="回复评论",
        parent_comment_id=parent_comment.id
    )
    
    assert reply is not None
    assert reply.parent_comment == parent_comment.id


def test_create_comment_empty_content(test_db, test_branch, test_bot):
    """测试空内容评论（应该失败）"""
    bot, _ = test_bot
    
    with pytest.raises(ValueError, match="不能为空"):
        create_comment(
            db=test_db,
            branch_id=test_branch.id,
            author_id=bot.id,
            author_type='bot',
            content=""
        )


def test_create_comment_too_long(test_db, test_branch, test_bot):
    """测试评论内容太长（应该失败）"""
    bot, _ = test_bot
    
    long_content = "a" * 1001
    
    with pytest.raises(ValueError, match="不能超过1000字符"):
        create_comment(
            db=test_db,
            branch_id=test_branch.id,
            author_id=bot.id,
            author_type='bot',
            content=long_content
        )


def test_get_comments_tree(test_db, test_branch, test_bot):
    """测试获取评论树"""
    bot, _ = test_bot
    
    # 创建父评论
    parent = create_comment(
        db=test_db,
        branch_id=test_branch.id,
        author_id=bot.id,
        author_type='bot',
        content="父评论"
    )
    
    # 创建两个回复
    reply1 = create_comment(
        db=test_db,
        branch_id=test_branch.id,
        author_id=bot.id,
        author_type='bot',
        content="回复1",
        parent_comment_id=parent.id
    )
    
    reply2 = create_comment(
        db=test_db,
        branch_id=test_branch.id,
        author_id=bot.id,
        author_type='bot',
        content="回复2",
        parent_comment_id=parent.id
    )
    
    # 获取评论树
    comments_tree = get_comments_by_branch(test_db, test_branch.id)
    
    assert len(comments_tree) == 1  # 只有一个根评论
    assert len(comments_tree[0]['children']) == 2  # 有两个回复
    assert comments_tree[0]['id'] == str(parent.id)
    assert comments_tree[0]['children'][0]['id'] == str(reply1.id)
    assert comments_tree[0]['children'][1]['id'] == str(reply2.id)


def test_create_comment_api_bot(client, test_db, test_branch, test_bot):
    """测试Bot发表评论API"""
    bot, api_key = test_bot
    
    response = client.post(
        f'/api/v1/branches/{test_branch.id}/comments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'content': '这是通过API发表的Bot评论'
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['comment']['content'] == '这是通过API发表的Bot评论'
    assert data['data']['comment']['author_type'] == 'bot'


def test_create_comment_api_human(client, test_db, test_branch, test_user):
    """测试人类发表评论API"""
    user, password = test_user
    
    # 先登录获取JWT
    login_response = client.post('/api/v1/auth/login', json={
        'email': 'commenttest@example.com',
        'password': 'password123'
    })
    jwt_token = login_response.get_json()['data']['token']
    
    # 发表评论
    response = client.post(
        f'/api/v1/branches/{test_branch.id}/comments',
        headers={'Authorization': f'Bearer {jwt_token}'},
        json={
            'content': '这是通过API发表的人类评论'
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['comment']['content'] == '这是通过API发表的人类评论'
    assert data['data']['comment']['author_type'] == 'human'


def test_create_comment_api_reply(client, test_db, test_branch, test_bot):
    """测试回复评论API"""
    bot, api_key = test_bot
    
    # 创建父评论
    parent_response = client.post(
        f'/api/v1/branches/{test_branch.id}/comments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': '父评论'}
    )
    parent_id = parent_response.get_json()['data']['comment']['id']
    
    # 回复评论
    reply_response = client.post(
        f'/api/v1/branches/{test_branch.id}/comments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'content': '回复评论',
            'parent_comment_id': parent_id
        }
    )
    
    assert reply_response.status_code == 201
    data = reply_response.get_json()
    assert data['status'] == 'success'
    assert data['data']['comment']['parent_comment_id'] == parent_id


def test_get_comments_api(client, test_db, test_branch, test_bot):
    """测试获取评论树API"""
    bot, api_key = test_bot
    
    # 创建几个评论
    client.post(
        f'/api/v1/branches/{test_branch.id}/comments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': '评论1'}
    )
    
    client.post(
        f'/api/v1/branches/{test_branch.id}/comments',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'content': '评论2'}
    )
    
    # 获取评论树
    response = client.get(f'/api/v1/branches/{test_branch.id}/comments')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'comments' in data['data']
    assert len(data['data']['comments']) == 2  # 两个根评论
