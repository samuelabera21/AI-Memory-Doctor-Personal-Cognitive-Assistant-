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

## Files
- backend/app/services/temporal_service.py
- backend/app/services/context_service.py
- backend/app/api/search.py
- backend/app/api/summarization.py
