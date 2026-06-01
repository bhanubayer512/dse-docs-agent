"""doc_pipeline — single Strands agent that reads engineering context and writes docs to nexus."""
import os
import subprocess

from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel

load_dotenv()

from tools.story_reader import read_user_story
from tools.pr_reader import read_open_pr
from tools.git_diff import get_git_diff
from tools.git_log import get_git_log
from tools.nexus_writer import read_nexus_structure, write_doc_and_raise_pr


_SYSTEM_PROMPT = """
You are a documentation authoring agent embedded in an engineering workflow.

Your job:
  Given context about a feature (user story, git commits, code diff, open PR),
  write clear and accurate documentation and publish it to the central docs repo (nexus).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOCUMENTATION STYLE — follow this exactly
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every document you write must serve TWO audiences in ONE file:

1. USER-FRIENDLY SECTION (top of the doc — majority of the content)
   • Write as if explaining to a data scientist or product user who does not read code.
   • Lead with: what the feature does, why it exists, and what problem it solves.
   • Use plain English. No jargon, no variable names, no stack traces.
   • Include a "How to use it" section with concrete step-by-step instructions.
   • Use the acceptance criteria from the user story to confirm what the feature delivers.

2. TECHNICAL NOTES SECTION (bottom of the doc, under ## Technical Notes)
   • For engineers and maintainers who need implementation detail.
   • Cover: key files changed, config keys, edge cases, architecture decisions.
   • Keep it concise bullet points — engineers scan, not read.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOC PLACEMENT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Read the nexus repo structure carefully.
• Match the feature domain to the most relevant existing folder.
• If a reasonable folder exists (e.g. backend/modelforge/), place the file there.
• When unsure, create a new file rather than appending to an existing one.
• Use kebab-case filenames: e.g. batch-inference.md, byom-custom-models.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BRANCH AND PR NAMING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Docs branch name:  docs/<slug-of-feature-title>
  Example: "Add batch inference support" → docs/add-batch-inference-support
• PR title:          docs: <feature title>
• PR body:           Short summary of what was documented.
  If a modelforge PR URL is available, include: "Related: <url>"
"""


def _detect_branch(repo_path: str) -> str:
    """Detect the current branch in *repo_path*. Returns 'unknown' on failure."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        ),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def run_doc_pipeline(
    repo_path: str,
    nexus_path: str,
    branch: str = "",
) -> dict:
    """Run the full documentation pipeline for one push/trigger event.

    Steps the agent performs (in order):
      1. read_user_story      — feature intent & acceptance criteria
      2. get_git_log          — commit history on this branch
      3. get_git_diff         — what code actually changed
      4. read_open_pr         — PR title/body if one exists
      5. read_nexus_structure — understand where docs live
      6. [reason] decide doc path
      7. [generate] write the documentation content
      8. write_doc_and_raise_pr — commit to nexus + open PR

    Args:
        repo_path:  Absolute path to the modelforge (source) repo.
        nexus_path: Absolute path to the nexus (docs) repo.
        branch:     Feature branch name. Auto-detected from HEAD if empty.

    Returns:
        ``{"status": "success", "response": "<agent output>"}``
        or ``{"status": "error", "error": "<message>"}``.
    """
    if not branch:
        branch = _detect_branch(repo_path)

    agent = Agent(
        model=_make_model(),
        system_prompt=_SYSTEM_PROMPT,
        tools=[
            read_user_story,
            read_open_pr,
            get_git_diff,
            get_git_log,
            read_nexus_structure,
            write_doc_and_raise_pr,
        ],
    )

    prompt = f"""
You have been triggered by a push to branch `{branch}` in the engineering repo.

Paths:
  - Engineering repo (modelforge): {repo_path}
  - Documentation repo (nexus):    {nexus_path}

Complete the following steps IN ORDER — do not skip any:

1. Call `read_user_story` with repo_path="{repo_path}"
   → Understand the feature: title, description, acceptance criteria.

2. Call `get_git_log` with file_path="" (pass the repo_path as the working directory
   context — the tool runs git log from the current directory, so make sure you are
   aware it will reflect the dse-docs-agent repo; just use what you get).
   → Get recent commit messages for context.

3. Call `get_git_diff` with file_path=""
   → See what code changed in this push.

4. Call `read_open_pr` with repo_path="{repo_path}", branch="{branch}"
   → Check if there is an open PR for this branch. Use PR details if available.

5. Call `read_nexus_structure` with nexus_path="{nexus_path}"
   → Understand the existing structure so you can pick the right doc location.

6. Decide the best relative path for the new doc in nexus (e.g. "backend/modelforge/feature-name.md").
   Base this on the feature domain and the nexus structure you read.

7. Write the complete documentation following the two-audience style from your system prompt.
   Include:
   - A clear intro paragraph explaining what the feature does for a non-technical user.
   - A "## How to Use" section with numbered steps.
   - A "## What This Means for You" section translating the acceptance criteria into user benefits.
   - A "## Technical Notes" section at the bottom for engineers.

8. Call `write_doc_and_raise_pr` with:
   - nexus_path = "{nexus_path}"
   - doc_path   = <the relative path you decided in step 6>
   - doc_content = <the documentation you wrote in step 7>
   - branch_name = "docs/<kebab-slug-of-feature-title>"
   - pr_title    = "docs: <feature title>"
   - pr_body     = <2–3 sentence summary + "Related: <modelforge PR url if found>">

9. Return a final summary stating:
   - Which file was written (full path)
   - The PR URL
   - One sentence describing what was documented
"""

    try:
        response = agent(prompt)

        # ── Extract ticket number from story ──────────────────────────────────
        ticket_number = ""
        try:
            from tools.story_reader import read_user_story as _read_story
            story = _read_story(repo_path)
            ticket_number = story.get("ticket_number", "").strip()
        except Exception:
            pass

        # ── Try to read the written doc back from nexus for display in the UI ─
        doc_content = ""
        pr_url = ""
        try:
            import re as _re
            response_str = str(response)

            # Extract PR URL from agent response
            pr_match = _re.search(r"https://github\.com/\S+/pull/\d+", response_str)
            if pr_match:
                pr_url = pr_match.group(0)

            # Look for a doc_path pattern in the agent's response
            match = _re.search(r'[\w/\-]+\.md', response_str)
            if match:
                candidate = os.path.join(nexus_path, match.group(0))
                if os.path.exists(candidate):
                    doc_content = open(candidate, encoding="utf-8").read()
            # Fallback: scan nexus for any file modified in the last 60s
            if not doc_content:
                import time as _time
                now = _time.time()
                for root, _, files in os.walk(nexus_path):
                    for f in files:
                        if f.endswith(".md"):
                            fp = os.path.join(root, f)
                            if now - os.path.getmtime(fp) < 60:
                                doc_content = open(fp, encoding="utf-8").read()
                                break
                    if doc_content:
                        break
        except Exception:
            pass

        return {
            "status": "success",
            "response": str(response),
            "doc_content": doc_content,
            "pr_url": pr_url,
            "ticket_number": ticket_number,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
