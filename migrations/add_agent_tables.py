"""数据库迁移脚本 - 添加 Agent 相关表

运行方式:
    cd /Users/admin/Desktop/work/inkpath
    python migrations/add_agent_tables.py

注意事项:
    - 必须在 Render PostgreSQL 控制台运行
    - 建议先备份数据库
"""

import sys
sys.path.insert(0, '/Users/admin/Desktop/work/inkpath')

from src.database import engine, Base
from src.models.agent import Agent, AgentStory, AgentProgress


def run_migration():
    """执行迁移"""
    print("=" * 60)
    print("Agent 表迁移")
    print("=" * 60)
    
    # 创建表
    print("\n[1/3] 创建 Agent 表...")
    Agent.__table__.create(bind=engine, checkfirst=True)
    print("   ✅ Agent 表就绪")
    
    print("\n[2/3] 创建 AgentStory 表...")
    AgentStory.__table__.create(bind=engine, checkfirst=True)
    print("   ✅ AgentStory 表就绪")
    
    print("\n[3/3] 创建 AgentProgress 表...")
    AgentProgress.__table__.create(bind=engine, checkfirst=True)
    print("   ✅ AgentProgress 表就绪")
    
    print("\n" + "=" * 60)
    print("✅ 迁移完成!")
    print("=" * 60)
    
    # 列出所有表
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n当前数据库表: {', '.join(tables)}")


if __name__ == '__main__':
    run_migration()
