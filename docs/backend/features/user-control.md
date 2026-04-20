# User Control System

## Goal
Allow users to safely view, edit, and delete their own memory records.

## Endpoints
- GET /memories
- PUT /memories/{memory_id}
- DELETE /memories/{memory_id}
- Legacy compatibility:
  - PUT /update-memory
  - DELETE /delete-memory

## Security
- All operations are authenticated via bearer token.
- Queries are scoped by user_id.
- Soft delete:
  - is_active = 0
  - is_deleted = 1
  - row remains in database
- Hard delete:
  - admin only
  - row is permanently removed
- Retrieval/search always filters: is_active = 1 and is_deleted = 0

## Files
- backend/app/api/memory_manage.py
- backend/app/services/dependency.py
