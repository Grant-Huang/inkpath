"""数据库连接和会话管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config import Config

# 确保使用psycopg驱动（psycopg3）
database_url = Config.DATABASE_URL
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
elif database_url.startswith('postgresql+psycopg2://'):
    database_url = database_url.replace('postgresql+psycopg2://', 'postgresql+psycopg://', 1)

# 创建数据库引擎
engine = create_engine(
    database_url,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    echo=Config.FLASK_DEBUG  # 开发环境打印SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建线程安全的会话
db_session = scoped_session(SessionLocal)

# 创建基础模型类
Base = declarative_base()


def init_db():
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话（用于依赖注入）"""
    db = db_session()
    try:
        yield db
    finally:
        db.close()
