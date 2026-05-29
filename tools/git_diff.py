from strands import tool
import subprocess


@tool
def get_git_diff(file_path: str = "") -> str:
    "Git diff tool"
    cmd = ["git", "diff", "HEAD"]
    if file_path:
        cmd.append(file_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout or "(no changes)"
