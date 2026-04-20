# Summarization

## Goal
Generate daily/weekly/monthly digest summaries from memory history.

## Endpoint
- POST /summarize

## Behavior
- Derives date range from query
- Aggregates total count, duration estimate, dominant memory type
- Extracts top themes from memory text

## Output
- summary text
- count
- period start/end date

## Files
- backend/app/api/summarization.py
- backend/app/services/summarization_service.py
