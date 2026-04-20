# Memory Input and Structuring

## Goal
Capture natural language memory input and convert it into structured records.

## Endpoint
- POST /add-memory

## Input
- content: raw text from user
- time: optional HH:MM override

## Processing Pipeline
1. Normalize raw text.
2. Extract date/time from natural language.
3. Classify memory type using ML classifier.
4. Extract duration and tags.
5. Save structured memory in SQL database.
6. Encode memory content and upsert vector embedding.

## Output Fields
- date
- time
- type
- content
- duration
- tags
- source_text

## Files
- backend/app/api/memory.py
- backend/app/services/nlp_service.py
- backend/app/services/ml_classifier_service.py

## Continuous Learning (Optional)

- Current behavior is static: classifier is pre-trained from labeled dataset and reused at runtime.
- The system currently uses a pre-trained classification model and does not automatically update itself with new user data. However, it is designed to support future extension for continuous learning.
- Placeholder function for future online/periodic retraining is defined in backend/app/services/ml_classifier_service.py.
