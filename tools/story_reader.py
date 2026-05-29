"""Strands tool: reads USER_STORY.md from a repo root and parses it into structured sections."""
import os
from strands import tool


@tool
def read_user_story(repo_path: str) -> dict:
    """Read USER_STORY.md from the root of the given repo and return its parsed sections.

    Expected file format::

        ## Title
        Short one-line feature name

        ## Description
        What this feature does and why it exists.

        ## Acceptance Criteria
        - [ ] Criterion one
        - [ ] Criterion two

    Args:
        repo_path: Absolute path to the repository containing USER_STORY.md.

    Returns:
        Dict with keys ``title``, ``description``, ``acceptance_criteria``, ``raw``.
        If the file is not found, returns ``{"error": "<message>", "found": False}``.
    """
    story_path = os.path.join(repo_path, "USER_STORY.md")

    if not os.path.exists(story_path):
        return {
            "found": False,
            "error": (
                f"USER_STORY.md not found at {story_path}. "
                "Create this file at the repo root with ## Title, ## Description, "
                "and ## Acceptance Criteria sections."
            ),
        }

    raw = open(story_path, encoding="utf-8").read()

    # --- Section parser ---------------------------------------------------------
    # Splits on any line that starts with "## " so the format is flexible.
    sections: dict = {
        "found": True,
        "title": "",
        "description": "",
        "acceptance_criteria": "",
        "raw": raw,
    }

    _SECTION_MAP = {
        "title": ["## title"],
        "description": ["## description"],
        "acceptance_criteria": ["## acceptance criteria", "## acceptance_criteria"],
    }

    current_key: str | None = None
    buf: list[str] = []

    def _flush():
        if current_key:
            sections[current_key] = "\n".join(buf).strip()

    for line in raw.splitlines():
        lowered = line.strip().lower()
        matched = False
        for key, prefixes in _SECTION_MAP.items():
            if any(lowered.startswith(p) for p in prefixes):
                _flush()
                current_key = key
                buf = []
                matched = True
                break
        if not matched and current_key is not None:
            buf.append(line)

    _flush()
    return sections
