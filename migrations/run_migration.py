#!/usr/bin/env python3
"""
在 Render 后台运行的迁移脚本

使用方法：
    python migrations/run_migration.py
"""

import os
import sys

def main():
    print("="*60)
    print("迁移：添加 starter 字段")
    print("="*60)
    
    # 尝试使用 SQLAlchemy
    try:
        from src.database import engine
        from sqlalchemy import text
        
        print("📝 使用 SQLAlchemy 连接数据库...")
        
        with engine.connect() as conn:
            # 检查字段是否存在
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='stories' AND column_name='starter'"
            ))
            exists = result.fetchone() is not None
            
            if exists:
                print("✅ starter 字段已存在，跳过迁移")
                return 0
            
            # 添加字段
            print("📝 添加 starter 字段...")
            conn.execute(text('ALTER TABLE stories ADD COLUMN starter TEXT NULL'))
            conn.commit()
            print("✅ starter 字段添加成功!")
            
            return 0
            
    except Exception as e:
        print(f"❌ SQLAlchemy 迁移失败: {e}")
        print("")
        print("请在 Render 后台执行以下命令：")
        print("")
        print("1. 获取 DATABASE_URL:")
        print("   echo $DATABASE_URL")
        print("")
        print("2. 直接使用 psql:")
        print('   psql "$DATABASE_URL" -c "ALTER TABLE stories ADD COLUMN starter TEXT NULL;"')
        print("")
        print("3. 或者重启服务后再次尝试")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
