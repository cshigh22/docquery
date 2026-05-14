import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .pipeline import Pipeline


def _die(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def _format_sources(sources: list[str]) -> str:
    return f"Sources: {', '.join(sources)}" if sources else "Sources: (none)"


def _build_pipeline(folder: str) -> Pipeline:
    path = Path(folder)
    if not path.exists():
        _die(f"folder not found: {folder}")
    if not path.is_dir():
        _die(f"not a directory: {folder}")
    try:
        return Pipeline.from_folder(folder)
    except ValueError as e:
        _die(str(e))
    except Exception as e:
        _die(f"failed to load {folder}: {e}")


def _run_ask(pipeline: Pipeline, question: str, verbose: bool) -> None:
    try:
        response, sources, chunks = pipeline.ask(question)
    except Exception as e:
        _die(f"failed to answer question: {e}")
    if verbose:
        print("--- Retrieved chunks ---")
        for c in chunks:
            preview = c.text if len(c.text) <= 400 else c.text[:400] + "..."
            print(f"\n[Source: {c.source}, chunk {c.chunk_id}]")
            print(preview)
        print("--- End chunks ---\n")
    print(response)
    print(_format_sources(sources))


def _run_chat(pipeline: Pipeline) -> None:
    print(
        f"Loaded {len(pipeline.docs)} documents, "
        f"{len(pipeline.chunks)} chunks. "
        f"Ask a question (or 'exit'):"
    )
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            return
        try:
            response, sources, _ = pipeline.ask(question)
        except Exception as e:
            _die(f"failed to answer question: {e}")
        print(response)
        print(_format_sources(sources))


def main() -> None:
    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        _die(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )

    parser = argparse.ArgumentParser(prog="docquery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser(
        "ask", help="Ask a single question about documents in a folder"
    )
    ask_parser.add_argument("folder", help="Path to folder containing documents")
    ask_parser.add_argument("question", help="Question to ask")
    ask_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print retrieved chunks before the answer",
    )

    chat_parser = subparsers.add_parser(
        "chat", help="Open a REPL to ask questions about documents in a folder"
    )
    chat_parser.add_argument("folder", help="Path to folder containing documents")

    args = parser.parse_args()

    pipeline = _build_pipeline(args.folder)

    try:
        if args.command == "ask":
            _run_ask(pipeline, args.question, args.verbose)
        elif args.command == "chat":
            _run_chat(pipeline)
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
