# Evaluation Metrics

## Goal
Provide measurable quality indicators for the memory assistant.

## Endpoints
- GET /evaluation/metrics
- POST /evaluation/metrics
- POST /evaluation/export-report

## Metrics
- classification_accuracy
- retrieval_accuracy
- response_correctness

## Single-Command Thesis Export

Use one endpoint call to run evaluation test cases and export both JSON and CSV reports.

Request:
- POST /evaluation/export-report
- Body supports optional custom cases and report_name.

Response:
- metrics summary
- json_report path
- csv_report path

Export location:
- backend/reports

## Notes
- Classification accuracy is computed on seeded supervised samples.
- Retrieval and response metrics can be provided as sampled evaluation cases.

## Files
- backend/app/api/evaluation.py
- backend/app/services/evaluation_service.py
- backend/app/services/ml_classifier_service.py
