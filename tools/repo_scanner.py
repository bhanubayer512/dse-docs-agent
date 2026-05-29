"""Strands tools: scan branch diffs and find existing docs."""
import os
import subprocess
from pathlib import Path
from strands import tool


@tool
def scan_branch_diff(repo_path: str, branch: str = "HEAD", base_branch: str = "main") -> str:
    """Get the diff of a branch compared to a base branch in a given repository.

    Args:
        repo_path: Absolute or relative path to the git repository.
        branch: The feature branch to compare (default HEAD for working changes).
        base_branch: The base branch to compare against (default main).

    Returns:
        A summary of changed files and their diffs.
    """
    repo = Path(repo_path).resolve()
    if not (repo / ".git").exists():
        return f"Error: {repo} is not a git repository"

    # Get list of changed files
    if branch == "HEAD":
        # Compare working tree + staged against base
        cmd_files = ["git", "diff", "--name-status", base_branch]
        cmd_diff = ["git", "diff", base_branch]
    else:
        cmd_files = ["git", "diff", "--name-status", f"{base_branch}...{branch}"]
        cmd_diff = ["git", "diff", f"{base_branch}...{branch}"]

    files_result = subprocess.run(cmd_files, capture_output=True, text=True, cwd=str(repo))
    diff_result = subprocess.run(cmd_diff, capture_output=True, text=True, cwd=str(repo))

    if files_result.returncode != 0:
        return f"Error running git diff: {files_result.stderr}"

    changed_files = files_result.stdout.strip()
    if not changed_files:
        return "(no changes found between branches)"

    output = f"## Changed Files ({base_branch} → {branch})\n\n"
    output += "```\n" + changed_files + "\n```\n\n"
    output += "## Full Diff\n\n"
    output += "```diff\n" + (diff_result.stdout[:15000] if len(diff_result.stdout) > 15000 else diff_result.stdout) + "\n```"
    return output


@tool
def find_existing_docs(docs_repo_path: str, keywords: str) -> str:
    """Search existing documentation repo for pages related to given keywords.

    Args:
        docs_repo_path: Path to the documentation repository (e.g., ../ph-rnd-dse-docs).
        keywords: Comma-separated keywords to search for (e.g., "dsecli,auth,login,config").

    Returns:
        List of matching doc files with relevant excerpts.
    """
    docs_root = Path(docs_repo_path).resolve() / "docs"
    if not docs_root.exists():
        return f"Error: docs directory not found at {docs_root}"

    keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    if not keyword_list:
        return "Error: no keywords provided"

    matches = []
    for md_file in docs_root.rglob("*.md"):
        rel_path = str(md_file.relative_to(docs_root.parent))
        filename_lower = md_file.name.lower()

        # Check filename match
        name_match = any(kw in filename_lower for kw in keyword_list)

        # Check content match
        try:
            content = md_file.read_text(errors="ignore")
        except Exception:
            continue

        content_lower = content.lower()
        content_match = any(kw in content_lower for kw in keyword_list)

        if name_match or content_match:
            matched_kws = [kw for kw in keyword_list if kw in filename_lower or kw in content_lower]
            # Extract a relevant excerpt (first 500 chars)
            excerpt = content[:500].strip()
            matches.append(f"### {rel_path}\n**Matched keywords:** {', '.join(matched_kws)}\n\n```\n{excerpt}\n```\n")

    if not matches:
        return f"No existing docs found matching keywords: {', '.join(keyword_list)}"

    return f"## Found {len(matches)} Matching Doc(s)\n\n" + "\n---\n".join(matches)


@tool
def read_existing_doc(doc_path: str) -> str:
    """Read the full content of an existing documentation file.

    Args:
        doc_path: Path to the documentation file.

    Returns:
        The full content of the file.
    """
    try:
        return Path(doc_path).read_text(errors="ignore")
    except FileNotFoundError:
        return f"Error: File not found: {doc_path}"
