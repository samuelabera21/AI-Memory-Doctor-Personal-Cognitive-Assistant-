from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

from app.db.database import SessionLocal
from app.models.memory_model import Memory, MemoryVersion
from app.services.dependency import get_current_user, is_admin_user
from app.services.embedding_service import get_embedding
from app.services.vector_store import delete_memory_vector, upsert_memory_vector
from app.services.nlp_service import classify_type

router = APIRouter()

class UpdateMemoryInput(BaseModel):
    content: str
    reason: str | None = "manual_edit"


@router.put("/memories/{memory_id}")
def update_memory(memory_id: int, data: UpdateMemoryInput, user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user.id,
            Memory.is_active == 1,
            Memory.is_deleted == 0,
        ).first()

        if not memory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

        old_content = memory.content
        old_type = memory.type
        new_content = data.content.strip()
        new_type = classify_type(new_content)

        memory.is_active = 0
        memory.updated_at = datetime.utcnow()

        new_memory = Memory(
            user_id=memory.user_id,
            date=memory.date,
            time=memory.time,
            type=new_type,
            content=new_content,
            duration=memory.duration,
            tags=memory.tags,
            source_text=new_content,
            parent_memory_id=memory.parent_memory_id or memory.id,
            version=(memory.version or 1) + 1,
            is_active=1,
            is_deleted=0,
        )
        db.add(new_memory)
        db.flush()

        version = MemoryVersion(
            memory_id=new_memory.id,
            user_id=user.id,
            old_content=old_content,
            new_content=new_content,
            old_type=old_type,
            new_type=new_type,
            change_reason=data.reason or "manual_edit",
        )
        db.add(version)
        db.commit()
        db.refresh(new_memory)

        delete_memory_vector(memory.id)

        upsert_memory_vector(
            memory_id=new_memory.id,
            user_id=user.id,
            vector=get_embedding(new_content),
            text=new_content,
        )

        return {
            "status": "updated",
            "memory_id": new_memory.id,
            "previous_memory_id": memory.id,
            "content": new_memory.content,
            "type": new_memory.type,
            "version": new_memory.version,
        }
    finally:
        db.close()

class DeleteMemoryInput(BaseModel):
    reason: str | None = "user_delete"
    hard_delete: bool = False


class LegacyUpdateInput(BaseModel):
    id: int
    content: str
    reason: str | None = "manual_edit"


class LegacyDeleteInput(BaseModel):
    id: int
    reason: str | None = "user_delete"


@router.delete("/memories/{memory_id}")
def delete_memory(memory_id: int, data: DeleteMemoryInput | None = None, user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user.id,
            Memory.is_deleted == 0,
        ).first()

        if not memory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

        if data and data.hard_delete:
            if not is_admin_user(user):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hard delete is admin only")
            db.delete(memory)
            db.commit()
            delete_memory_vector(memory.id)
            return {
                "status": "hard_deleted",
                "memory_id": memory.id,
                "reason": data.reason,
            }

        memory.is_active = 0
        memory.is_deleted = 1
        memory.deleted_at = datetime.utcnow()
        memory.updated_at = datetime.utcnow()
        db.commit()
        delete_memory_vector(memory.id)

        return {
            "status": "soft_deleted",
            "memory_id": memory.id,
            "reason": (data.reason if data else "user_delete"),
        }
    finally:
        db.close()

class CorrectionInput(BaseModel):
    text: str


@router.post("/update-memory")
def correction_update(data: CorrectionInput, user=Depends(get_current_user)):
    text = data.text.strip()
    lowered = text.lower()

    if " not " not in lowered and "actually" not in lowered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No correction pattern detected")

    left, right = text, ""
    if " not " in lowered:
        split_idx = lowered.index(" not ")
        left = text[:split_idx].replace("Actually", "").replace("actually", "").strip(" ,")
        right = text[split_idx + 5 :].strip(" .,")

    db = SessionLocal()
    try:
        user_memories = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.is_active == 1,
            Memory.is_deleted == 0,
        ).all()

        if not user_memories:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No memory found to update")

        target = None
        if right:
            for m in user_memories:
                if right.lower() in (m.content or "").lower():
                    target = m
                    break
        if target is None:
            target = sorted(user_memories, key=lambda m: (m.date, m.time), reverse=True)[0]

        old_content = target.content
        old_type = target.type

        target.is_active = 0
        target.updated_at = datetime.utcnow()

        updated_memory = Memory(
            user_id=target.user_id,
            date=target.date,
            time=target.time,
            type=classify_type(left),
            content=left,
            duration=target.duration,
            tags=target.tags,
            source_text=left,
            parent_memory_id=target.parent_memory_id or target.id,
            version=(target.version or 1) + 1,
            is_active=1,
            is_deleted=0,
        )
        db.add(updated_memory)
        db.flush()

        db.add(
            MemoryVersion(
                memory_id=updated_memory.id,
                user_id=user.id,
                old_content=old_content,
                new_content=updated_memory.content,
                old_type=old_type,
                new_type=updated_memory.type,
                change_reason="natural_language_correction",
            )
        )
        db.commit()

        delete_memory_vector(target.id)

        upsert_memory_vector(
            memory_id=updated_memory.id,
            user_id=user.id,
            vector=get_embedding(updated_memory.content),
            text=updated_memory.content,
        )

        return {
            "message": "Memory updated",
            "memory_id": updated_memory.id,
            "previous_memory_id": target.id,
            "updated": updated_memory.content,
            "version": updated_memory.version,
        }
    finally:
        db.close()

@router.get("/memories")
def get_all_memories(user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        memories = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.is_active == 1,
            Memory.is_deleted == 0,
        ).order_by(Memory.date.desc(), Memory.time.desc()).all()

        return [
            {
                "id": m.id,
                "content": m.content,
                "type": m.type,
                "date": m.date,
                "time": m.time,
                "duration": m.duration,
                "tags": m.tags.split(",") if m.tags else [],
                "version": m.version,
            }
            for m in memories
        ]
    finally:
        db.close()


@router.get("/memories/{memory_id}/history")
def memory_history(memory_id: int, user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        versions = db.query(MemoryVersion).filter(
            MemoryVersion.memory_id == memory_id,
            MemoryVersion.user_id == user.id,
        ).order_by(MemoryVersion.changed_at.desc()).all()

        return [
            {
                "id": v.id,
                "old_content": v.old_content,
                "new_content": v.new_content,
                "old_type": v.old_type,
                "new_type": v.new_type,
                "change_reason": v.change_reason,
                "changed_at": v.changed_at.isoformat() if v.changed_at else None,
            }
            for v in versions
        ]
    finally:
        db.close()


@router.put("/update-memory")
def legacy_update_memory(data: LegacyUpdateInput, user=Depends(get_current_user)):
    return update_memory(
        memory_id=data.id,
        data=UpdateMemoryInput(content=data.content, reason=data.reason),
        user=user,
    )


@router.delete("/delete-memory")
def legacy_delete_memory(data: LegacyDeleteInput, user=Depends(get_current_user)):
    return delete_memory(
        memory_id=data.id,
        data=DeleteMemoryInput(reason=data.reason),
        user=user,
    )