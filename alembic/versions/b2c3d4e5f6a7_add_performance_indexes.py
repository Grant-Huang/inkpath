"""添加性能优化索引

Revision ID: b2c3d4e5f6a7
Revises: a9ac0bfac694
Create Date: 2024-02-01 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a9ac0bfac694'
branch_labels = None
depends_on = None


def upgrade():
    """添加性能优化索引（跳过已存在的）"""
    # 为 stories 表添加索引
    _create_index_if_not_exists('idx_stories_status_created', 'stories', ['status', 'created_at'])
    _create_index_if_not_exists('idx_stories_owner', 'stories', ['owner_type', 'owner_id'])
    
    # 为 branches 表添加索引
    _create_index_if_not_exists('idx_branches_story_status', 'branches', ['story_id', 'status'])
    _create_index_if_not_exists('idx_branches_parent', 'branches', ['parent_branch', 'status'])
    
    # 为 segments 表添加索引
    _create_index_if_not_exists('idx_segments_branch_order', 'segments', ['branch_id', 'sequence_order'])
    _create_index_if_not_exists('idx_segments_created', 'segments', ['branch_id', 'created_at'])
    
    # 为 votes 表添加索引
    _create_index_if_not_exists('idx_votes_target', 'votes', ['target_type', 'target_id'])
    _create_index_if_not_exists('idx_votes_created', 'votes', ['created_at'])
    
    # 为 comments 表添加索引
    _create_index_if_not_exists('idx_comments_branch_created', 'comments', ['branch_id', 'created_at'])
    _create_index_if_not_exists('idx_comments_parent', 'comments', ['parent_comment_id'])


def downgrade():
    # 删除索引（不检查是否存在）
    op.drop_index('idx_stories_status_created', table_name='stories', if_exists=True)
    op.drop_index('idx_stories_owner', table_name='stories', if_exists=True)
    op.drop_index('idx_branches_story_status', table_name='branches', if_exists=True)
    op.drop_index('idx_branches_parent', table_name='branches', if_exists=True)
    op.drop_index('idx_segments_branch_order', table_name='segments', if_exists=True)
    op.drop_index('idx_segments_created', table_name='segments', if_exists=True)
    op.drop_index('idx_votes_target', table_name='votes', if_exists=True)
    op.drop_index('idx_votes_created', table_name='votes', if_exists=True)
    op.drop_index('idx_comments_branch_created', table_name='comments', if_exists=True)
    op.drop_index('idx_comments_parent', table_name='comments', if_exists=True)


def _create_index_if_not_exists(index_name, table_name, columns, unique=False):
    """创建索引，如果已存在则跳过"""
    from sqlalchemy import inspect
    from sqlalchemy.engine import Connection
    
    # 获取数据库连接
    connection = op.get_bind()
    inspector = inspect(connection)
    existing_indexes = inspector.get_indexes(table_name)
    existing_index_names = [idx['name'] for idx in existing_indexes]
    
    if index_name not in existing_index_names:
        op.create_index(index_name, table_name, columns, unique=unique)
