# Memory Storage

## Goal
Persist memories with both exact and semantic retrieval support.

## Structured Storage
- SQLAlchemy model: memories table
- Includes user_id, date, time, type, content, duration, tags, timestamps
- Lifecycle fields:
	- is_active: 1 for current valid version, 0 for inactive history rows
	- is_deleted: 1 for deleted rows (soft delete), 0 otherwise
	- version: incremented on updates
	- parent_memory_id: links versions across updates

## Semantic Storage
- FAISS ID map index stores normalized embeddings keyed by memory_id
- Metadata map tracks ownership and content

## Startup Sync
- On app startup, vectors are rebuilt only from active and non-deleted SQL records.

## Files
- backend/app/models/memory_model.py
- backend/app/services/vector_store.py
- backend/app/services/vector_sync_service.py
- backend/app/main.py
