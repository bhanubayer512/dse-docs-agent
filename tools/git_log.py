"""Strands tool: retrieves git commit history for a file or repository."""
import subprocess
from strands import tool


@tool
def get_git_log(file_path: str = "", max_commits: int = 10) -> str:
    """Get recent git commit history, optionally scoped to a specific file.

    Args:
        file_path: Optional path to scope history to a specific file.
        max_commits: Maximum number of commits to return (default 10).

    Returns:
        Formatted commit log as a string, or a message if no history found.
    """
    cmd = ["git", "log", "--oneline", "--no-merges", "-n", str(max_commits)]
    if file_path:
        cmd.extend(["--", file_path])
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    if not output:
        return "(no commit history found)"
    return output
