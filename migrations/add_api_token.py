"""
添加 users 表的 api_token 和 api_token_expires_at 字段
"""
import sys
sys.path.insert(0, '/Users/admin/Desktop/work/inkpath')

from src.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'api_token'
        """))
        
        if result.fetchone():
            print("api_token 字段已存在，跳过")
        else:
            print("添加 api_token 字段...")
            conn.execute(text("ALTER TABLE users ADD COLUMN api_token VARCHAR"))
            conn.commit()
            print("完成")
        
        # 检查 api_token_expires_at
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'api_token_expires_at'
        """))
        
        if result.fetchone():
            print("api_token_expires_at 字段已存在，跳过")
        else:
            print("添加 api_token_expires_at 字段...")
            conn.execute(text("ALTER TABLE users ADD COLUMN api_token_expires_at TIMESTAMP WITH TIME ZONE"))
            conn.commit()
            print("完成")

if __name__ == "__main__":
    run_migration()
