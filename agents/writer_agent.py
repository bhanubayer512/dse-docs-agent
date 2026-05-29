"""WriterAgent — assembles all agent outputs into a final polished documentation report."""
import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel

load_dotenv()

from tools.doc_writer import write_markdown_doc


def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def run_writer_agent(
    file_path: str,
    git_summary: str,
    ticket: str,
    documentation: str,
) -> str:
    """Assemble all pipeline outputs into a final report and persist it.

    Writes a file to output/<stem>_report.md and returns the full Markdown content.
    """
    from pathlib import Path

    stem = Path(file_path).stem + "_report"

    agent = Agent(
        model=_make_model(),
        tools=[write_markdown_doc],
        system_prompt=(
            "You are a technical writer producing final documentation packages. "
            "You will receive four inputs: file path, git summary, engineering ticket, and raw documentation. "
            "Your job: "
            "1. Combine these into a single cohesive Markdown report with a professional structure. "
            "2. Use these top-level sections: "
            "   # <Module Name> — Documentation Report\n"
            "   ## Overview\n"
            "   ## Change Log (from git summary)\n"
            "   ## Engineering Ticket\n"
            "   ## API Documentation\n"
            "   ## Usage Examples\n"
            "3. Write the assembled report using write_markdown_doc. "
            "4. Return the complete Markdown content. "
            "Ensure consistency of style, remove duplication, and add transitions where helpful."
        ),
    )
    response = agent(
        f"File path: '{file_path}'\n"
        f"Output filename (no extension): '{stem}'\n\n"
        f"--- GIT SUMMARY ---\n{git_summary}\n\n"
        f"--- ENGINEERING TICKET ---\n{ticket}\n\n"
        f"--- DOCUMENTATION ---\n{documentation}\n\n"
        "Assemble the final report and write it with write_markdown_doc."
    )
    return str(response)
