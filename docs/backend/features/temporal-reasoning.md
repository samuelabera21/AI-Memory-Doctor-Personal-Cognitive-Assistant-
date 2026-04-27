# Temporal Reasoning

## Goal
Interpret relative and natural time expressions in user queries.

## Supported Expressions
- today
- yesterday
- this week
- last week
- this month
- last month
- morning, afternoon, evening, night
- explicit date phrases parseable by dateutil parser

## Output Filters
- start_date
- end_date
- start_time
- end_time

## Context-Aware Follow-Up
- For follow-up queries (example: "and in the morning?"), the system can inherit missing date range from the same user's previous query context.
- Explicit time labels in follow-up queries (morning/afternoon/evening/night) still override time-window fields.
- Context inheritance is isolated per user session state in backend memory.
- Context inheritance is guarded by confidence and freshness checks (TTL) to reduce stale or noisy carry-over.

## Files
- backend/app/services/temporal_service.py
- backend/app/services/context_service.py
- backend/app/api/search.py
- backend/app/api/summarization.py
