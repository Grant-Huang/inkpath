"""迁移脚本：添加 segment_logs 表"""
import uuid
from sqlalchemy import text
from src.database import engine

def run_migration():
    """创建 segment_logs 表"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS segment_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        story_id UUID NOT NULL,
        branch_id UUID NOT NULL,
        segment_id UUID NOT NULL,
        author_id UUID,
        author_type VARCHAR(20) NOT NULL,
        author_name VARCHAR(100) NOT NULL,
        content_length INTEGER NOT NULL,
        is_continuation VARCHAR(20) NOT NULL,
        parent_segment_id UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_segment_logs_story_id ON segment_logs(story_id);
    CREATE INDEX IF NOT EXISTS idx_segment_logs_branch_id ON segment_logs(branch_id);
    CREATE INDEX IF NOT EXISTS idx_segment_logs_segment_id ON segment_logs(segment_id);
    CREATE INDEX IF NOT EXISTS idx_segment_logs_author_id ON segment_logs(author_id);
    CREATE INDEX IF NOT EXISTS idx_segment_logs_created_at ON segment_logs(created_at);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
        print("segment_logs 表创建成功")

if __name__ == '__main__':
    run_migration()
