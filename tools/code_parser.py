"""Strands tool: reads a Python source file and returns its content."""
from strands import tool


@tool
def read_code_file(file_path: str) -> str:
    """Read a Python source file and return its contents.

    Args:
        file_path: Path to the Python file to read.

    Returns:
        The full source code as a string, or an error message if not found.
    """
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
