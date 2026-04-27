# Evaluation Metrics

## Goal
Provide measurable quality indicators for the memory assistant.

## Endpoints
- GET /evaluation/metrics
- POST /evaluation/metrics
- POST /evaluation/export-report
- POST /evaluation/run-context-scenario
- GET /evaluation/context-scenario-history

## Metrics
- classification_accuracy
- retrieval_accuracy
- response_correctness
- context_followup_accuracy
- context_application_rate

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

## Multi-Turn Context Scenario
- POST /evaluation/run-context-scenario executes a real behavior-driven follow-up flow:
	- seeds temporary memories
	- runs initial query + follow-up query
	- scores context-followup correctness and context application
	- cleans temporary seeded data
- Scenario runs are appended to a persistent history log for trend monitoring.
- GET /evaluation/context-scenario-history returns recent run records and average context-followup correctness.

## Notes
- Classification accuracy is computed on seeded supervised samples.
- Retrieval and response metrics can be provided as sampled evaluation cases.
- Follow-up context accuracy measures whether multi-turn continuity remains correct.
- Context application rate shows how often context gating allowed context to be applied.

## Files
- backend/app/api/evaluation.py
- backend/app/services/evaluation_service.py
- backend/app/services/ml_classifier_service.py
