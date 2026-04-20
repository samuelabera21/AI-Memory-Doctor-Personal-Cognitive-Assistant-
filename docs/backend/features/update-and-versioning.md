# Update and Versioning

## Goal
Support correction and modification of memory records while preserving change history.

## Update Policy
- Old row is never overwritten.
- Old row is marked inactive (`is_active = 0`).
- New row is inserted with incremented version.
- Retrieval always uses `is_active = 1` and `is_deleted = 0`.

## Endpoints
- PUT /memories/{memory_id}
- POST /update-memory (natural language correction)
- GET /memories/{memory_id}/history

## Version Tracking
Every update writes a version record:
- old_content, new_content
- old_type, new_type
- change_reason
- changed_at

## Correction Flow
Input example:
- Actually I studied Java not Python

System behavior:
1. Finds target memory (match by right side phrase or latest memory fallback).
2. Creates a new version row with updated content and type.
3. Stores version history.
4. Updates vector index.

## Files
- backend/app/api/memory_manage.py
- backend/app/models/memory_model.py
