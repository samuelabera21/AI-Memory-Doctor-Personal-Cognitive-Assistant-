# Agent Orchestration

## Goal
Provide one conversational endpoint that routes user text to the correct memory capability.

## Endpoint
- POST /agent

## Intent Routing
- store -> add memory
- search -> search memory
- summarize -> summarization
- insight -> insight analysis
- update -> natural language correction

## Files
- backend/app/api/agent.py
- backend/app/services/intent_service.py
