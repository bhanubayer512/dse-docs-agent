"""GitAgent — analyses git history and diffs to produce a structured change summary."""
import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel

load_dotenv()

from tools.git_diff import get_git_diff
from tools.git_log import get_git_log


def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def run_git_agent(file_path: str) -> str:
    """Analyse git history and diff for *file_path* and return a Markdown summary.

    The summary covers:
    - Recent commits that touched the file
    - What changed in the working-tree diff
    - An overall change-risk assessment (Low / Medium / High)
    """
    agent = Agent(
        model=_make_model(),
        tools=[get_git_diff, get_git_log],
        system_prompt=(
            "You are a senior software engineer specialising in code-change analysis. "
            "When given a file path you must: "
            "1. Retrieve its recent commit history with get_git_log. "
            "2. Retrieve the current diff with get_git_diff. "
            "3. Return a concise Markdown report with sections: "
            "   ## Recent Commits, ## Current Changes, ## Change Risk (Low/Medium/High with justification). "
            "Be specific and factual. Do not hallucinate filenames or commit hashes."
        ),
    )
    response = agent(
        f"Analyse git activity for the file '{file_path}'. "
        "Use get_git_log and get_git_diff, then write the Markdown report."
    )
    return str(response)
