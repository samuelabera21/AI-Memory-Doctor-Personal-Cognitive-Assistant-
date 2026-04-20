from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

DATABASE_URL = settings.database_url

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite requires this for multi-threaded FastAPI access patterns.
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()   


def _sqlite_has_column(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return any(row[1] == column_name for row in rows)


def _apply_sqlite_compat_migrations() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as conn:
        if _sqlite_has_column(conn, "users", "created_at") is False:
            conn.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))

        memory_columns = {
            "source_text": "TEXT",
            "parent_memory_id": "INTEGER",
            "version": "INTEGER DEFAULT 1",
            "is_active": "INTEGER DEFAULT 1",
            "is_deleted": "INTEGER DEFAULT 0",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
            "deleted_at": "DATETIME",
        }
        for column_name, column_type in memory_columns.items():
            if _sqlite_has_column(conn, "memories", column_name) is False:
                conn.execute(text(f"ALTER TABLE memories ADD COLUMN {column_name} {column_type}"))

        conn.execute(text("UPDATE memories SET version = COALESCE(version, 1)"))
        conn.execute(text("UPDATE memories SET is_active = COALESCE(is_active, 1)"))
        conn.execute(text("UPDATE memories SET is_deleted = COALESCE(is_deleted, 0)"))


def init_database() -> None:
    # Import models here so metadata has all tables before create_all.
    from app.models import memory_model, user_model  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_compat_migrations()