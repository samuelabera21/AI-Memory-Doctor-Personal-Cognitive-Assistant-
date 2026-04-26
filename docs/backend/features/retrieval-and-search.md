# Retrieval and Search

## Goal
Answer memory questions with hybrid retrieval.

## Endpoint
- POST /search-memory

## Hybrid Retrieval Steps
1. Normalize query with user conversation context for follow-up questions.
2. Embed effective query.
3. Retrieve semantic candidates from FAISS.
4. Pull candidate records from SQL by memory_id and user_id.
5. Apply temporal filters (date/time windows).
6. Rank by semantic score, lexical overlap, and recency.
7. Generate grounded response.

## Context Continuity
- Follow-up prompts like "what about last week?" can be enriched using the same user's recent topic/type context.
- Context is isolated per user in memory and applied only for follow-up-style queries.

## Ranking
- semantic_weight = 0.60
- overlap_weight = 0.20
- recency_weight = 0.20

## Files
- backend/app/api/search.py
- backend/app/services/vector_store.py
- backend/app/services/ranking_service.py
- backend/app/services/answer_service.py
