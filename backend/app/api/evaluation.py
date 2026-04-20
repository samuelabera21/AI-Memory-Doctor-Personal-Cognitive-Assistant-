from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.dependency import get_current_user
from app.services.evaluation_service import compute_system_metrics, run_endpoint_test_report

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationSample(BaseModel):
    retrieval_precision: float
    response_correctness: float


class EvaluationInput(BaseModel):
    samples: list[EvaluationSample] = []


class EvaluationCase(BaseModel):
    query: str
    expected_ids: list[int] = []
    expected_answer: str = ""


class ReportExportInput(BaseModel):
    report_name: str = "thesis_evaluation"
    cases: list[EvaluationCase] = []


@router.get("/metrics")
def get_metrics(user=Depends(get_current_user)):
    _ = user
    return compute_system_metrics()


@router.post("/metrics")
def evaluate_from_samples(payload: EvaluationInput, user=Depends(get_current_user)):
    _ = user
    return compute_system_metrics([sample.model_dump() for sample in payload.samples])


@router.post("/export-report")
def export_report(payload: ReportExportInput, user=Depends(get_current_user)):
    case_payload = [case.model_dump() for case in payload.cases] if payload.cases else None
    return run_endpoint_test_report(
        user=user,
        cases=case_payload,
        report_name=payload.report_name,
    )
