"""Orchestrator — coordinates GitAgent → TicketAgent → DocsAgent → WriterAgent."""
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from agents.git_agent import run_git_agent
from agents.ticket_agent import run_ticket_agent
from agents.doc_agent import run_docs_agent
from agents.writer_agent import run_writer_agent


@dataclass
class AgentStep:
    name: str
    status: str = "pending"   # pending | running | done | error
    output: str = ""
    elapsed_seconds: float = 0.0


@dataclass
class PipelineResult:
    file_path: str
    steps: list[AgentStep] = field(default_factory=list)
    git_summary: str = ""
    ticket: str = ""
    documentation: str = ""
    final_report: str = ""
    elapsed_seconds: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def run_pipeline(file_path: str) -> PipelineResult:
    """Run the full four-agent documentation pipeline for *file_path*.

    Pipeline stages (sequential):
      1. GitAgent      — analyses git history & diff
      2. TicketAgent   — generates an engineering ticket
      3. DocsAgent     — produces API/module documentation
      4. WriterAgent   — assembles everything into a final report

    Returns a :class:`PipelineResult` with all intermediate and final outputs.
    """
    if not Path(file_path).exists():
        return PipelineResult(
            file_path=file_path,
            error=f"File not found: {file_path}",
        )

    result = PipelineResult(file_path=file_path)
    pipeline_start = time.perf_counter()

    def _run_step(name: str, fn, *args) -> str:
        step = AgentStep(name=name, status="running")
        result.steps.append(step)
        t0 = time.perf_counter()
        try:
            output = fn(*args)
            step.status = "done"
            step.output = output
        except Exception as exc:
            step.status = "error"
            step.output = str(exc)
            output = ""
        step.elapsed_seconds = round(time.perf_counter() - t0, 2)
        return output

    result.git_summary = _run_step("GitAgent", run_git_agent, file_path)
    result.ticket = _run_step("TicketAgent", run_ticket_agent, file_path, result.git_summary)
    result.documentation = _run_step("DocsAgent", run_docs_agent, file_path)
    result.final_report = _run_step(
        "WriterAgent",
        run_writer_agent,
        file_path,
        result.git_summary,
        result.ticket,
        result.documentation,
    )

    result.elapsed_seconds = round(time.perf_counter() - pipeline_start, 2)
    return result


if __name__ == "__main__":
    import sys, json

    path = sys.argv[1] if len(sys.argv) > 1 else "sample_code/example.py"
    res = run_pipeline(path)
    print(json.dumps(res.to_dict(), indent=2))
