"""Strands tools: read the nexus repo structure and write a doc + raise a PR."""
import os
import re
import subprocess
from strands import tool


# ---------------------------------------------------------------------------
# read_nexus_structure
# ---------------------------------------------------------------------------

@tool
def read_nexus_structure(nexus_path: str) -> str:
    """Return a depth-limited directory tree of the nexus docs repo.

    Only ``.md`` and ``.mdx`` files are listed so the output stays within the
    model's context window.  Hidden directories (``.git``, ``.github``,
    ``node_modules``, ``__pycache__``) are skipped.

    Args:
        nexus_path: Absolute path to the nexus repository root.

    Returns:
        A plain-text tree string the agent can read to decide where a new doc
        should be placed (e.g. ``"backend/modelforge/batch-inference.md"``).
    """
    lines: list[str] = []
    for root, dirs, files in os.walk(nexus_path):
        # Prune unwanted dirs in-place (modifies os.walk's traversal)
        dirs[:] = sorted(
            d for d in dirs
            if not d.startswith(".")
            and d not in {"node_modules", "__pycache__", ".venv", "venv"}
        )

        depth = root.replace(nexus_path, "").count(os.sep)
        if depth > 4:
            continue

        indent = "  " * depth
        folder_name = os.path.basename(root) or os.path.basename(nexus_path)
        lines.append(f"{indent}{folder_name}/")

        sub_indent = "  " * (depth + 1)
        for fname in sorted(files):
            if fname.endswith((".md", ".mdx")):
                lines.append(f"{sub_indent}{fname}")

    return "\n".join(lines) if lines else "(empty repo)"


# ---------------------------------------------------------------------------
# write_doc_and_raise_pr
# ---------------------------------------------------------------------------

@tool
def write_doc_and_raise_pr(
    nexus_path: str,
    doc_path: str,
    doc_content: str,
    branch_name: str,
    pr_title: str,
    pr_body: str,
) -> dict:
    """Write a documentation file to the nexus repo and open a GitHub PR.

    Steps performed:
    1. Fetch + pull the default branch (``main`` / ``master``) so the PR base
       is always up-to-date.
    2. Create or reset ``branch_name`` with ``git checkout -B``.
    3. Write ``doc_content`` to ``nexus_path/doc_path`` (creates dirs as needed).
    4. ``git add`` → ``git commit`` → ``git push --force-with-lease``.
    5. ``gh pr create`` (or detect existing PR URL if the branch already has one).

    Args:
        nexus_path:  Absolute path to the local nexus repository.
        doc_path:    Relative path inside the nexus repo for the new file,
                     e.g. ``"backend/modelforge/batch-inference.md"``.
        doc_content: Full Markdown content to write.
        branch_name: Name of the docs branch to create, e.g.
                     ``"docs/batch-inference"``.
        pr_title:    Title for the GitHub PR.
        pr_body:     Body / description for the GitHub PR.

    Returns:
        ``{"success": True, "pr_url": "...", "doc_path": "..."}``
        or ``{"success": False, "error": "..."}``.
    """
    try:
        # ── 1. Ensure we start from an up-to-date default branch ──────────────
        default_branch = _get_default_branch(nexus_path)
        _run(["git", "fetch", "origin"], nexus_path)
        _run(["git", "checkout", default_branch], nexus_path)
        _run(["git", "pull", "origin", default_branch], nexus_path)

        # ── 2. Create / reset the docs branch ─────────────────────────────────
        # -B: create if missing, reset to current HEAD if it already exists.
        _run(["git", "checkout", "-B", branch_name], nexus_path)

        # ── 3. Write the file ─────────────────────────────────────────────────
        abs_doc_path = os.path.join(nexus_path, doc_path)
        os.makedirs(os.path.dirname(abs_doc_path), exist_ok=True)
        with open(abs_doc_path, "w", encoding="utf-8") as fh:
            fh.write(doc_content)

        # ── 4. Commit and push ────────────────────────────────────────────────
        _run(["git", "add", doc_path], nexus_path)
        _run(["git", "commit", "-m", f"docs: {pr_title}"], nexus_path)
        _run(
            ["git", "push", "-u", "origin", branch_name, "--force-with-lease"],
            nexus_path,
        )

        # ── 5. Raise the PR via gh CLI ────────────────────────────────────────
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", pr_title,
                "--body", pr_body,
                "--head", branch_name,
                "--base", default_branch,
            ],
            cwd=nexus_path,
            capture_output=True,
            text=True,
        )
        # ``gh pr create`` exits 1 with the existing PR URL if a PR already
        # exists for this branch — extract the URL either way.
        pr_url = _extract_pr_url(result.stdout + result.stderr)

        if not pr_url and result.returncode != 0:
            return {"success": False, "error": result.stderr.strip()}

        return {"success": True, "pr_url": pr_url, "doc_path": doc_path}

    except subprocess.CalledProcessError as exc:
        return {
            "success": False,
            "error": f"Git/gh command failed: {exc.stderr or exc}",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: str) -> None:
    """Run a shell command in *cwd*, raising CalledProcessError on failure."""
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _get_default_branch(repo_path: str) -> str:
    """Return the remote default branch name (main / master / etc.)."""
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # e.g. "refs/remotes/origin/main" → "main"
        return result.stdout.strip().split("/")[-1]
    return "main"  # safe fallback


def _extract_pr_url(text: str) -> str:
    """Extract the first GitHub PR URL found in *text*."""
    match = re.search(r"https://github\.com/\S+/pull/\d+", text)
    return match.group(0) if match else ""
