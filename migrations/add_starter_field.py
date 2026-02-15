"""
数据库迁移：添加 starter 字段

用途：将开篇内容存储在 stories 表中

使用方法：
    python migrations/add_starter_field.py

注意事项：
    1. 确保已备份数据库
    2. 在生产环境运行前先在测试环境验证
    3. 需要 PostgreSQL ALTER TABLE 权限
"""

import os
import sys
import yaml

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.database import engine

def migrate():
    """执行迁移"""
    print("="*60)
    print("迁移：添加 starter 字段")
    print("="*60)
    
    # 检查字段是否已存在
    check_sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='stories' AND column_name='starter'
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(check_sql))
        exists = result.fetchone() is not None
        
        if exists:
            print("✅ starter 字段已存在，跳过迁移")
            return
        
        # 添加字段
        print("📝 添加 starter 字段...")
        alter_sql = """
        ALTER TABLE stories 
        ADD COLUMN starter TEXT NULL;
        """
        
        conn.execute(text(alter_sql))
        conn.commit()
        
        print("✅ starter 字段添加成功")
        
        # 验证
        result = conn.execute(text(check_sql))
        exists = result.fetchone() is not None
        
        if exists:
            print("✅ 验证成功")
        else:
            print("❌ 验证失败")

if __name__ == "__main__":
    migrate()
