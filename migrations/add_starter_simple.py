#!/usr/bin/env python3
"""
简单的数据库迁移脚本 - 添加 starter 字段

使用方法：
    python migrations/add_starter_simple.py

或者直接运行 SQL：
    psql "YOUR_DATABASE_URL" -c "ALTER TABLE stories ADD COLUMN starter TEXT NULL;"
"""

import os
import sys

def main():
    print("="*60)
    print("迁移：添加 starter 字段")
    print("="*60)
    
    # 方法 1: 如果有 DATABASE_URL 环境变量
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        print("📝 使用 DATABASE_URL 连接数据库...")
        
        # 检查字段是否存在
        import subprocess
        check_result = subprocess.run(
            ['psql', database_url, '-t', '-c', 
             "SELECT column_name FROM information_schema.columns WHERE table_name='stories' AND column_name='starter';"],
            capture_output=True,
            text=True
        )
        
        if 'starter' in check_result.stdout:
            print("✅ starter 字段已存在，跳过迁移")
            return
        
        # 添加字段
        print("📝 添加 starter 字段...")
        result = subprocess.run(
            ['psql', database_url, '-c', 
             "ALTER TABLE stories ADD COLUMN starter TEXT NULL;"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ starter 字段添加成功!")
        else:
            print(f"❌ 错误: {result.stderr}")
    else:
        print("⚠️  未找到 DATABASE_URL 环境变量")
        print("")
        print("请在 Render 后台 Shell 执行以下命令：")
        print("")
        print("方法 1 - 使用 psql (如果有)：")
        print('  psql "$DATABASE_URL" -c "ALTER TABLE stories ADD COLUMN starter TEXT NULL;"')
        print("")
        print("方法 2 - 如果没有 psql，在 Python shell 中运行：")
        print("""
  from sqlalchemy import create_engine, text
  engine = create_engine(os.environ['DATABASE_URL'])
  with engine.connect() as conn:
      conn.execute(text('ALTER TABLE stories ADD COLUMN starter TEXT NULL'))
      conn.commit()
        """)
        
        # 尝试使用 SQLAlchemy
        try:
            from src.database import engine
            from sqlalchemy import text
            
            with engine.connect() as conn:
                # 检查
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='stories' AND column_name='starter'"
                ))
                exists = result.fetchone() is not None
                
                if exists:
                    print("✅ starter 字段已存在")
                else:
                    print("📝 添加 starter 字段...")
                    conn.execute(text('ALTER TABLE stories ADD COLUMN starter TEXT NULL'))
                    conn.commit()
                    print("✅ 成功!")
        except Exception as e:
            print(f"❌ 自动迁移失败: {e}")

if __name__ == "__main__":
    main()
