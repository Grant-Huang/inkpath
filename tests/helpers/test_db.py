"""测试数据库辅助函数"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.dialects.postgresql import JSONB
from src.database import Base
from src.models import *  # 导入所有模型


def create_test_db():
    """创建测试数据库（使用SQLite）"""
    # 使用SQLite进行测试，避免需要PostgreSQL
    test_db_url = "sqlite:///./test_inkpath.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    
    # 将JSONB类型映射为JSON（SQLite兼容）
    @event.listens_for(engine, "connect", insert=True)
    def set_sqlite_pragma(dbapi_conn, connection_record):
        # 启用外键约束
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # 替换JSONB为JSON类型（仅用于SQLite）
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = SQLiteJSON()
    
    Base.metadata.create_all(bind=engine)
    return engine


def get_test_session(engine):
    """获取测试数据库会话"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def drop_test_db(engine):
    """删除测试数据库"""
    try:
        # 尝试删除所有表，如果失败则忽略（表可能已经不存在）
        Base.metadata.drop_all(bind=engine, checkfirst=True)
    except Exception:
        pass  # 忽略删除错误
    
    # 删除数据库文件
    if os.path.exists("./test_inkpath.db"):
        try:
            os.remove("./test_inkpath.db")
        except Exception:
            pass  # 忽略删除文件错误
