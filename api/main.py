"""FastAPI app — single-file doc generation and full multi-agent pipeline."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agents.doc_agent import generate_docs
from agents.orchestrator import run_pipeline, PipelineResult

app = FastAPI(
    title="AI Doc Authoring API",
    description="Generate documentation from source code using AI agents",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")


# ── Request / Response models ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    file_path: str


class GenerateResponse(BaseModel):
    doc: str


class PipelineRequest(BaseModel):
    file_path: str


class AgentStepOut(BaseModel):
    name: str
    status: str
    output: str
    elapsed_seconds: float


class PipelineResponse(BaseModel):
    file_path: str
    steps: list[AgentStepOut]
    git_summary: str
    ticket: str
    documentation: str
    final_report: str
    elapsed_seconds: float
    error: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def serve_ui():
    index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    return FileResponse(index_path)


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """Single-agent mode: generate documentation for a given source file."""
    if not Path(req.file_path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")
    result = generate_docs(req.file_path)
    return GenerateResponse(doc=result)


@app.post("/pipeline", response_model=PipelineResponse)
def pipeline(req: PipelineRequest):
    """Multi-agent pipeline: GitAgent → TicketAgent → DocsAgent → WriterAgent."""
    if not Path(req.file_path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")
    result: PipelineResult = run_pipeline(req.file_path)
    if result.error:
        raise HTTPException(status_code=500, detail=result.error)
    return PipelineResponse(
        file_path=result.file_path,
        steps=[AgentStepOut(**vars(s)) for s in result.steps],
        git_summary=result.git_summary,
        ticket=result.ticket,
        documentation=result.documentation,
        final_report=result.final_report,
        elapsed_seconds=result.elapsed_seconds,
        error=result.error,
    )
