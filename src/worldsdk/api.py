"""Optional FastAPI surface for command/query access to the framework SDK."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from worldruntime import WorldRuntimeError

from .client import WorldSDK


class CreateEntityRequest(BaseModel):
    stable_id: str
    entity_type: str
    state: str | None = None
    attributes: dict = Field(default_factory=dict)


class AttachEvidenceRequest(BaseModel):
    evidence_id: str
    subject_stable_id: str
    source_ref: str
    excerpt: str
    source_system: str = "system_of_record"
    metadata: dict = Field(default_factory=dict)


class TransitionRequest(BaseModel):
    stable_id: str
    to_state: str
    reason: str
    evidence_id: str | None = None


class EvaluateRequest(BaseModel):
    run_id: str
    test_set_version: str
    alignment_strategy: str
    extracted_rows: list[dict]
    truth_rows: list[dict]


class CompareRunsRequest(BaseModel):
    run_a_id: str
    run_b_id: str


def create_app(db_url: str = "sqlite:///./world_framework.db") -> FastAPI:
    """Create API app for SDK operations."""

    app = FastAPI(title="World Framework SDK", version="0.1.0")
    sdk = WorldSDK(db_url=db_url)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "worldview_profile": sdk.worldview.name}

    @app.post("/entities")
    def create_entity(req: CreateEntityRequest):
        try:
            return sdk.create_entity(**req.model_dump()).model_dump()
        except WorldRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/evidence")
    def attach_evidence(req: AttachEvidenceRequest):
        try:
            return sdk.attach_evidence(**req.model_dump()).model_dump()
        except WorldRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/transitions")
    def transition(req: TransitionRequest):
        try:
            return sdk.transition(**req.model_dump()).model_dump()
        except WorldRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/evaluate")
    def evaluate(req: EvaluateRequest):
        return sdk.evaluate_run(**req.model_dump()).model_dump()

    @app.post("/compare-runs")
    def compare_runs(req: CompareRunsRequest):
        return sdk.compare_runs(**req.model_dump()).model_dump()

    @app.get("/world-view/{stable_id}")
    def world_view(stable_id: str):
        data = sdk.world_view(stable_id)
        if not data:
            raise HTTPException(status_code=404, detail="Entity not found")
        return data

    return app
