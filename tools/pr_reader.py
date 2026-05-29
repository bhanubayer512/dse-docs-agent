"""Strands tool: reads open PR details for the current branch via the `gh` CLI."""
import json
import subprocess
from strands import tool


@tool
def read_open_pr(repo_path: str, branch: str = "") -> dict:
    """Return the open GitHub PR for *branch* in the repo at *repo_path*.

    Uses the ``gh`` CLI (no extra Python dependencies).  Always passes
    ``cwd=repo_path`` so ``gh`` resolves the correct GitHub remote regardless
    of the caller's working directory.

    Args:
        repo_path: Absolute path to the local git repository.
        branch:    Branch name to look up.  Auto-detected from HEAD if omitted.

    Returns:
        On success: dict with ``found=True`` plus ``number``, ``title``,
            ``body``, ``url``, ``labels``, ``reviewRequests``, ``branch``.
        When no PR exists: ``{"found": False, "branch": "<name>"}``.
        On error: ``{"found": False, "error": "<message>", "branch": "<name>"}``.
    """
    # --- Auto-detect branch ---------------------------------------------------
    if not branch:
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            branch = r.stdout.strip()
        except subprocess.CalledProcessError as exc:
            return {"found": False, "error": f"Could not detect branch: {exc.stderr}"}

    # --- Query GitHub ---------------------------------------------------------
    try:
        result = subprocess.run(
            [
                "gh", "pr", "list",
                "--head", branch,
                "--state", "open",
                "--json", "number,title,body,url,labels,reviewRequests",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        return {
            "found": False,
            "branch": branch,
            "error": exc.stderr or "gh CLI call failed",
        }
    except FileNotFoundError:
        return {
            "found": False,
            "branch": branch,
            "error": "gh CLI not found — install via https://cli.github.com/",
        }

    try:
        prs = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"found": False, "branch": branch, "error": "Unexpected gh output"}

    if not prs:
        return {"found": False, "branch": branch}

    pr = prs[0]
    pr["found"] = True
    pr["branch"] = branch
    return pr
