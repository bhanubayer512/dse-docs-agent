#!/usr/bin/env python3
"""CLI entrypoint for the DSE Docs Agent.

Called directly by the post-push git hook or any developer who wants to
trigger documentation generation manually.

Usage::

    python run_agent.py --repo /path/to/ph-rnd-dse-modelforge
    python run_agent.py --repo /path/to/ph-rnd-dse-modelforge --branch feature/my-feature
    python run_agent.py --repo /path/to/ph-rnd-dse-modelforge \\
                        --nexus /path/to/ph-rnd-dse-nexus \\
                        --branch feature/my-feature
"""
import argparse
import os
import sys


DEFAULT_NEXUS_PATH = "/Users/bhanupratap.rathore/ph-rnd-dse-nexus"
DEFAULT_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dse-docs-agent",
        description="Generate documentation from a modelforge feature branch and raise a PR to nexus.",
    )
    parser.add_argument(
        "--repo",
        required=True,
        metavar="PATH",
        help="Absolute path to the modelforge (engineering) repository.",
    )
    parser.add_argument(
        "--nexus",
        default=DEFAULT_NEXUS_PATH,
        metavar="PATH",
        help=f"Absolute path to the nexus (docs) repository. Default: {DEFAULT_NEXUS_PATH}",
    )
    parser.add_argument(
        "--branch",
        default="",
        metavar="BRANCH",
        help="Feature branch name. Auto-detected from the repo HEAD if omitted.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # ── Validate paths ────────────────────────────────────────────────────────
    for path, label in [(args.repo, "--repo"), (args.nexus, "--nexus")]:
        if not os.path.isdir(path):
            print(f"❌  {label} path not found: {path}", file=sys.stderr)
            sys.exit(1)

    print()
    print("🤖  DSE Docs Agent")
    print(f"    repo:   {args.repo}")
    print(f"    nexus:  {args.nexus}")
    print(f"    branch: {args.branch or '(auto-detect from HEAD)'}")
    print()

    # ── Deferred import so startup/path errors surface cleanly before boto3 ──
    # Add the agent directory to sys.path so relative imports work when the
    # script is invoked from a different working directory (e.g. from the hook).
    if DEFAULT_AGENT_DIR not in sys.path:
        sys.path.insert(0, DEFAULT_AGENT_DIR)

    try:
        from agents.doc_pipeline import run_doc_pipeline
    except ImportError as exc:
        print(
            f"❌  Failed to import doc_pipeline: {exc}\n"
            "    Make sure you have run: pip install -e '.[dev]' inside dse-docs-agent",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Run the pipeline ──────────────────────────────────────────────────────
    result = run_doc_pipeline(
        repo_path=args.repo,
        nexus_path=args.nexus,
        branch=args.branch,
    )

    if result.get("status") == "success":
        print("✅  Documentation pipeline completed successfully!\n")
        print(result.get("response", ""))
        print()
    else:
        error = result.get("error", "Unknown error")
        print(f"❌  Pipeline failed:\n    {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
