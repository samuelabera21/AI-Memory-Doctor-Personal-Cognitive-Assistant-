from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime
from app.db.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # ✅ IMPORTANT

    date = Column(String)
    time = Column(String)
    type = Column(String)
    content = Column(Text)
    duration = Column(String)
    tags = Column(String)
    source_text = Column(Text)
    parent_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)


class MemoryVersion(Base):
    __tablename__ = "memory_versions"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    old_content = Column(Text)
    new_content = Column(Text)
    old_type = Column(String)
    new_type = Column(String)
    change_reason = Column(String)
    changed_at = Column(DateTime, default=datetime.utcnow)