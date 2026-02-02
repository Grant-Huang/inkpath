#!/usr/bin/env python3
"""测试数据库连接脚本"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database import engine, get_db
from src.config import Config
from sqlalchemy import text


def test_connection():
    """测试数据库连接"""
    print(f"测试数据库连接: {Config.DATABASE_URL.split('@')[-1] if '@' in Config.DATABASE_URL else Config.DATABASE_URL}")
    
    try:
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功!")
            print(f"   查询结果: {result.scalar()}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n提示:")
        print("1. 确保PostgreSQL数据库正在运行")
        print("2. 检查.env文件中的DATABASE_URL配置")
        print("3. 如果使用Docker，运行: docker-compose up -d postgres")
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
