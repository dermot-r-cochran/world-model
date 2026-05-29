"""FastAPI platform API exposing explicit world view commands and queries.

Run with: uvicorn worldview.api:create_app --factory --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .domain import ClaimCreate, EntityCreate, EvidenceCreate, RelationCreate, TransitionCommand
from .errors import WorldViewError
from .sdk import WorldViewSDK


def create_app(db_url: str = "sqlite:///./worldview.db") -> FastAPI:
    """Create FastAPI app with world view SDK-backed endpoints."""

    app = FastAPI(title="World View Platform", version="0.1.0")
    sdk = WorldViewSDK(db_url=db_url)

    @app.post("/entities")
    def create_entity(command: EntityCreate):
        try:
            return sdk.create_entity(command).model_dump()
        except WorldViewError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/relations")
    def create_relation(command: RelationCreate):
        try:
            return sdk.create_relation(command).model_dump()
        except WorldViewError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/evidence")
    def add_evidence(command: EvidenceCreate):
        try:
            return sdk.add_evidence(command).model_dump()
        except WorldViewError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/transitions")
    def apply_transition(command: TransitionCommand):
        try:
            return sdk.apply_transition(command).model_dump()
        except WorldViewError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/claims")
    def create_claim(command: ClaimCreate):
        try:
            return sdk.create_claim(command).model_dump()
        except WorldViewError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/world-view/{stable_id}")
    def get_world_view(stable_id: str):
        data = sdk.world_view(stable_id)
        if not data:
            raise HTTPException(status_code=404, detail="Entity not found")
        return data

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
