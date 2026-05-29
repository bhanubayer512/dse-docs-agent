"""TicketAgent — generates a structured engineering ticket from source code and git context."""
import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel

load_dotenv()

from tools.code_parser import read_code_file


def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def run_ticket_agent(file_path: str, git_summary: str) -> str:
    """Generate a Markdown engineering ticket for *file_path* using the git summary.

    The ticket includes:
    - **Title** — one-line summary of the change
    - **Summary** — 2-3 sentence description
    - **Technical Changes** — bullet list of what was modified
    - **Impact Assessment** — downstream effects and risks
    - **Acceptance Criteria** — verifiable done conditions
    """
    agent = Agent(
        model=_make_model(),
        tools=[read_code_file],
        system_prompt=(
            "You are a technical project manager creating engineering tickets. "
            "You will receive a file path and a git change summary. "
            "Steps: "
            "1. Read the source file using read_code_file. "
            "2. Using the code content and the provided git summary, produce a complete "
            "   engineering ticket in Markdown with these sections: "
            "   ## Title, ## Summary, ## Technical Changes, ## Impact Assessment, ## Acceptance Criteria. "
            "Keep it concise, actionable, and developer-friendly."
        ),
    )
    response = agent(
        f"File: '{file_path}'\n\n"
        f"Git Summary:\n{git_summary}\n\n"
        "Read the source file and create the engineering ticket."
    )
    return str(response)
