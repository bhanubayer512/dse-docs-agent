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
from agents.nexus_docs_agent import run_nexus_pipeline, NexusPipelineResult, create_pr_from_result

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


class NexusPipelineRequest(BaseModel):
    repo_path: str = "../ph-rnd-dse-nexus-cli"
    branch: str = "np(ngxp)/AB-524067-SIMPLE-PRO-MODE"
    base_branch: str = "origin/qa"
    docs_repo_path: str = "../ph-rnd-dse-docs"


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


class NexusStepOut(BaseModel):
    name: str
    status: str
    output: str
    elapsed_seconds: float


class NexusPipelineResponse(BaseModel):
    repo_path: str
    branch: str
    steps: list[NexusStepOut]
    changed_files: str
    existing_docs: str
    generated_docs: str
    ticket_id: str
    elapsed_seconds: float
    error: str


class CreatePRRequest(BaseModel):
    repo_path: str = "../ph-rnd-dse-nexus-cli"
    branch: str
    base_branch: str = "origin/qa"
    docs_repo_path: str = "../ph-rnd-dse-docs"
    generated_docs: str


class CreatePRResponse(BaseModel):
    status: str
    branch: str = ""
    files_written: list[str] = []
    commit_message: str = ""
    pr_url: str = ""
    message: str = ""


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


@app.post("/nexus-pipeline", response_model=NexusPipelineResponse)
def nexus_pipeline(req: NexusPipelineRequest):
    """Nexus CLI doc generation: detect branch changes and generate/update docs."""
    result: NexusPipelineResult = run_nexus_pipeline(req.repo_path, req.branch, req.base_branch, req.docs_repo_path)
    if result.error and not result.generated_docs:
        raise HTTPException(status_code=400, detail=result.error)
    return NexusPipelineResponse(
        repo_path=result.repo_path,
        branch=result.branch,
        steps=[NexusStepOut(**vars(s)) for s in result.steps],
        changed_files=result.changed_files,
        existing_docs=result.existing_docs,
        generated_docs=result.generated_docs,
        ticket_id=result.ticket_id,
        elapsed_seconds=result.elapsed_seconds,
        error=result.error,
    )


@app.post("/create-pr", response_model=CreatePRResponse)
def create_pr(req: CreatePRRequest):
    """Create a PR in the docs repo with the generated documentation."""
    from tools.pr_creator import extract_ticket_id, create_docs_pr

    ticket_id = extract_ticket_id(branch_name=req.branch)
    pr_result = create_docs_pr(
        docs_repo_path=req.docs_repo_path,
        branch_name=ticket_id or req.branch,
        ticket_id=ticket_id,
        generated_docs=req.generated_docs,
        source_branch=req.branch,
    )
    return CreatePRResponse(**pr_result)
