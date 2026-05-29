"""DocsAgent — generates structured Markdown documentation from Python source files."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from strands import Agent
from strands.models.bedrock import BedrockModel

load_dotenv()

from tools.code_parser import read_code_file
from tools.doc_writer import write_markdown_doc
from tools.git_diff import get_git_diff


def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def generate_docs(file_path: str) -> str:
    """Run the docs agent on a source file and return the generated documentation.

    Also persists output to output/<stem>.md via write_markdown_doc.
    """
    agent = Agent(
        model=_make_model(),
        tools=[read_code_file, write_markdown_doc, get_git_diff],
        system_prompt=(
            "You are a technical documentation expert. "
            "When given a Python source file: "
            "1. Read the file using read_code_file. "
            "2. Generate Markdown docs covering: overview, classes, methods, "
            "   parameters, return types, and usage examples. "
            "3. Write the docs using write_markdown_doc (base filename, no extension). "
            "Return the full generated documentation as Markdown."
        ),
    )
    stem = Path(file_path).stem
    response = agent(
        f"Document the Python file at '{file_path}'. "
        f"Write output as '{stem}' via write_markdown_doc."
    )
    return str(response)


# Alias used by the orchestrator pipeline.
run_docs_agent = generate_docs


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_code/example.py"
    result = generate_docs(path)
    print(result)
