"""
修改 agents 表允许 owner_id 为 NULL
"""
import sys
sys.path.insert(0, '/Users/admin/Desktop/work/inkpath')

from src.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        # 修改 owner_id 允许 NULL
        print("修改 agents.owner_id 允许 NULL...")
        try:
            conn.execute(text("ALTER TABLE agents ALTER COLUMN owner_id DROP NOT NULL"))
            conn.commit()
            print("完成")
        except Exception as e:
            print(f"可能已存在: {e}")

if __name__ == "__main__":
    run_migration()
