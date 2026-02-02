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
    # 为 stories 表添加索引
    op.create_index('idx_stories_status_created', 'stories', ['status', 'created_at'], unique=False)
    op.create_index('idx_stories_owner', 'stories', ['owner_type', 'owner_id'], unique=False)
    
    # 为 branches 表添加索引
    op.create_index('idx_branches_story_status', 'branches', ['story_id', 'status'], unique=False)
    op.create_index('idx_branches_parent', 'branches', ['parent_branch', 'status'], unique=False)
    
    # 为 segments 表添加索引
    op.create_index('idx_segments_branch_order', 'segments', ['branch_id', 'sequence_order'], unique=False)
    op.create_index('idx_segments_created', 'segments', ['branch_id', 'created_at'], unique=False)
    
    # 为 votes 表添加索引（如果存在）
    try:
        op.create_index('idx_votes_target', 'votes', ['target_type', 'target_id'], unique=False)
        op.create_index('idx_votes_created', 'votes', ['created_at'], unique=False)
    except Exception:
        pass  # 表可能不存在或索引已存在
    
    # 为 comments 表添加索引（如果存在）
    try:
        op.create_index('idx_comments_branch_created', 'comments', ['branch_id', 'created_at'], unique=False)
        op.create_index('idx_comments_parent', 'comments', ['parent_comment_id'], unique=False)
    except Exception:
        pass  # 表可能不存在或索引已存在


def downgrade():
    # 删除索引
    op.drop_index('idx_stories_status_created', table_name='stories')
    op.drop_index('idx_stories_owner', table_name='stories')
    op.drop_index('idx_branches_story_status', table_name='branches')
    op.drop_index('idx_branches_parent', table_name='branches')
    op.drop_index('idx_segments_branch_order', table_name='segments')
    op.drop_index('idx_segments_created', table_name='segments')
    
    try:
        op.drop_index('idx_votes_target', table_name='votes')
        op.drop_index('idx_votes_created', table_name='votes')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_comments_branch_created', table_name='comments')
        op.drop_index('idx_comments_parent', table_name='comments')
    except Exception:
        pass
