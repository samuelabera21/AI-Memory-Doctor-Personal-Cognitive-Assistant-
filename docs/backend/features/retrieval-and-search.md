# Retrieval and Search

## Goal
Answer memory questions with hybrid retrieval.

## Endpoint
- POST /search-memory

## Hybrid Retrieval Steps
1. Embed query.
2. Retrieve semantic candidates from FAISS.
3. Pull candidate records from SQL by memory_id and user_id.
4. Apply temporal filters (date/time windows).
5. Rank by semantic score, lexical overlap, and recency.
6. Generate grounded response.

## Ranking
- semantic_weight = 0.60
- overlap_weight = 0.20
- recency_weight = 0.20

## Files
- backend/app/api/search.py
- backend/app/services/vector_store.py
- backend/app/services/ranking_service.py
- backend/app/services/answer_service.py
