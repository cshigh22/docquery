import argparse

from dotenv import load_dotenv

from .pipeline import Pipeline


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="docquery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser(
        "ask", help="Ask a question about documents in a folder"
    )
    ask_parser.add_argument("folder", help="Path to folder containing documents")
    ask_parser.add_argument("question", help="Question to ask")
    ask_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print retrieved chunks before the answer",
    )

    args = parser.parse_args()

    if args.command == "ask":
        pipeline = Pipeline.from_folder(args.folder)
        response, sources, chunks = pipeline.ask(args.question)
        if args.verbose:
            print("--- Retrieved chunks ---")
            for c in chunks:
                preview = c.text if len(c.text) <= 400 else c.text[:400] + "..."
                print(f"\n[Source: {c.source}, chunk {c.chunk_id}]")
                print(preview)
            print("--- End chunks ---\n")
        print(response)
        if sources:
            print(f"\nSources used: {', '.join(sources)}")


if __name__ == "__main__":
    main()
