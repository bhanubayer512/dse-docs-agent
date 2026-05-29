"""BranchDiffDocsAgent — detects code changes on a branch and generates/updates documentation."""
import os
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel

load_dotenv()

from tools.repo_scanner import scan_branch_diff, find_existing_docs, read_existing_doc
from tools.code_parser import read_code_file
from tools.pr_creator import extract_ticket_id, create_docs_pr


@dataclass
class NexusStep:
    name: str
    status: str = "pending"
    output: str = ""
    elapsed_seconds: float = 0.0


@dataclass
class NexusPipelineResult:
    repo_path: str
    branch: str
    steps: list[NexusStep] = field(default_factory=list)
    changed_files: str = ""
    existing_docs: str = ""
    generated_docs: str = ""
    ticket_id: str = ""
    pr_info: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def run_nexus_pipeline(repo_path: str, branch: str = "HEAD", base_branch: str = "origin/qa", docs_repo_path: str = None) -> NexusPipelineResult:
    """Run the branch diff doc generation pipeline.

    Steps:
      1. ScanChanges — diff the branch against base branch
      2. FindExistingDocs — search docs repo for related pages
      3. GenerateDocs — AI agent generates updated/new documentation
    """
    docs_repo = docs_repo_path or os.getenv("DOCS_REPO_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "ph-rnd-dse-docs"))
    result = NexusPipelineResult(repo_path=repo_path, branch=branch)
    pipeline_start = time.perf_counter()

    # Extract ticket ID from branch name
    result.ticket_id = extract_ticket_id(branch_name=branch)

    def _run_step(name: str, fn, *args) -> str:
        step = NexusStep(name=name, status="running")
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

    # Step 1: Scan branch changes
    result.changed_files = _run_step("ScanChanges", _scan_changes, repo_path, branch, base_branch)

    if not result.changed_files or "no changes" in result.changed_files.lower():
        result.error = "No changes detected between branches"
        result.elapsed_seconds = round(time.perf_counter() - pipeline_start, 2)
        return result

    # Step 2: Find existing docs
    keywords = _extract_keywords_from_diff(result.changed_files)
    result.existing_docs = _run_step("FindExistingDocs", _find_docs, docs_repo, keywords)

    # Step 3: Generate documentation using AI (with ticket context)
    result.generated_docs = _run_step(
        "GenerateDocs", _generate_docs,
        repo_path, branch, result.changed_files, result.existing_docs, docs_repo, result.ticket_id
    )

    result.elapsed_seconds = round(time.perf_counter() - pipeline_start, 2)
    return result


def create_pr_from_result(result: NexusPipelineResult, docs_repo_path: str) -> dict:
    """Create a PR in the docs repo from a completed pipeline result."""
    if not result.generated_docs:
        return {"status": "error", "message": "No generated docs to create PR from"}

    return create_docs_pr(
        docs_repo_path=docs_repo_path,
        branch_name=result.ticket_id or result.branch,
        ticket_id=result.ticket_id,
        generated_docs=result.generated_docs,
        source_branch=result.branch,
    )


def _scan_changes(repo_path: str, branch: str, base_branch: str) -> str:
    """Wrapper to call the scan_branch_diff tool."""
    return scan_branch_diff(repo_path=repo_path, branch=branch, base_branch=base_branch)


def _find_docs(docs_repo: str, keywords: str) -> str:
    """Wrapper to call find_existing_docs."""
    return find_existing_docs(docs_repo_path=docs_repo, keywords=keywords)


def _extract_keywords_from_diff(changed_files_output: str) -> str:
    """Extract meaningful keywords from the changed files list."""
    keywords = set()

    # Extract module names from changed files
    for match in re.finditer(r'/(\w+)\.py', changed_files_output):
        name = match.group(1)
        if name not in ("__init__", "__main__", "setup"):
            keywords.add(name)

    # Extract directory names for broader matching
    for match in re.finditer(r'src/(\w+)/', changed_files_output):
        keywords.add(match.group(1))

    # Fallback keywords if nothing found
    if not keywords:
        keywords.add("cli")
        keywords.add("config")

    return ",".join(keywords)


def _generate_docs(repo_path: str, branch: str, changed_files: str, existing_docs: str, docs_repo: str, ticket_id: str) -> str:
    """Use the AI agent to generate documentation based on code changes and existing docs."""
    agent = Agent(
        model=_make_model(),
        tools=[read_code_file, read_existing_doc, scan_branch_diff],
        system_prompt=(
            "You are a senior technical documentation writer. "
            "Your task is to generate or update user-facing documentation based on code changes detected between two branches.\n\n"
            "IMPORTANT GUIDELINES:\n"
            "- Write in the same style and tone as the existing documentation provided\n"
            "- Use MkDocs-compatible Markdown (admonitions with !!! note, !!! tip, etc.)\n"
            "- Focus on WHAT changed for the user, not internal implementation details\n"
            "- Include installation/usage commands where relevant\n"
            "- Be concise and practical — developers are the audience\n"
            "- If an existing doc should be updated, output the FULL updated document\n"
            "- If a new doc is needed, suggest a file path under docs/ and provide full content\n\n"
            "OUTPUT FORMAT:\n"
            "For each doc, output:\n"
            "## [UPDATE|NEW]: <file_path>\n"
            "<full markdown content>\n"
            "---\n"
        ),
    )

    ticket_context = ""
    if ticket_id:
        ticket_context = f"\n\nAzure DevOps Ticket: {ticket_id}\nInclude this ticket reference in any changelog or release notes sections.\n"

    prompt = (
        f"The source repository at '{repo_path}' has changes on branch '{branch}'.{ticket_context}\n\n"
        f"=== CODE CHANGES ===\n{changed_files}\n\n"
        f"=== EXISTING DOCUMENTATION ===\n{existing_docs}\n\n"
        "Based on these code changes:\n"
        "1. Read the changed source files using read_code_file to understand the full context\n"
        "2. Determine if existing docs need updating or new docs should be created\n"
        "3. Generate the documentation\n\n"
        "If code changes affect authentication, configuration, commands, or user-facing behavior, "
        "update the relevant docs. For entirely new features, create new doc pages."
    )

    response = agent(prompt)
    return str(response)
