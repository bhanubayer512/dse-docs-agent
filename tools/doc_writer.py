"""Strands tool: writes Markdown documentation to the output/ folder."""
import os
from pathlib import Path
from strands import tool


@tool
def write_markdown_doc(filename: str, content: str) -> str:
    """Write documentation content to output/<filename>.md.

    Args:
        filename: Base filename (without .md extension).
        content: Full Markdown content to write.

    Returns:
        Confirmation message with the written file path.
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / f"{filename}.md"
    out_path.write_text(content)
    return f"Documentation written to {out_path}"
