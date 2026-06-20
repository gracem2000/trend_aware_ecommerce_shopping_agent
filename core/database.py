"""SQLAlchemy 引擎 + SessionLocal + init_db。

SQLite 单文件；check_same_thread=False 以支持 Streamlit 多会话 + 后台调度线程并发读。
写操作由 repository 层用模块级 _write_lock 串行化。
"""
import threading
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.config import DATABASE_PATH
from core.models import Base

# 确保数据库文件父目录存在（首次运行 / 全新部署）
_db_path = Path(DATABASE_PATH)
if _db_path.parent and not _db_path.parent.exists():
    _db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
    future=True,
)


# 启用 WAL：读不阻塞写、写不阻塞读，避免 UI 轮询与后台流水线互相 "database is locked"
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _record):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("PRAGMA busy_timeout=5000")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# 写操作串行化锁。用 RLock 是因为 agent 持锁写库时可能再调用 log/status（也需持锁）。
_write_lock = threading.RLock()


def get_session():
    """返回一个新的 Session，调用方负责关闭（建议用 with 语句）。"""
    return SessionLocal()


def _migrate():
    """轻量迁移：给老库补 Scene 的吸收字段。幂等（PRAGMA 检查后 ALTER）。"""
    from sqlalchemy import text

    new_cols = [
        ("scene_type", "TEXT"), ("trigger_event", "TEXT"), ("temporal_scope", "TEXT"),
        ("geo_scope", "TEXT"), ("user_intent", "TEXT"), ("source", "TEXT"),
    ]
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='scenes'")
        ).fetchone()
        if not exists:
            return  # 全新库：create_all 会按最新模型建表，无需迁移
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(scenes)"))}
        for col, typ in new_cols:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE scenes ADD COLUMN {col} {typ}"))
        conn.commit()


def init_db():
    """建表 + 迁移 + 种子数据。幂等，可安全重复调用。"""
    Base.metadata.create_all(engine)
    _migrate()
    # 延迟导入避免循环依赖
    from core.seed import seed_if_empty

    with SessionLocal() as db:
        seed_if_empty(db)


def reset_db():
    """危险：删除所有表后重建（仅开发/调试用）。"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    from core.seed import seed_if_empty

    with SessionLocal() as db:
        seed_if_empty(db)
