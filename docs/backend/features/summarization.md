# Summarization

## Goal
Generate daily/weekly/monthly digest summaries from memory history.

## Endpoint
- POST /summarize

## Behavior
- Derives date range from query
- Aggregates total count, duration estimate, dominant memory type
- Extracts top themes from memory text
- Prioritizes important memories when generating fallback summaries
- Passes importance metadata into the LLM payload so generated summaries can emphasize high-value items

## Output
- summary text
- count
- period start/end date
- human-readable emphasis on priority memories and highlights

## Files
- backend/app/api/summarization.py
- backend/app/services/summarization_service.py
