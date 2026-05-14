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

    args = parser.parse_args()

    if args.command == "ask":
        pipeline = Pipeline.from_folder(args.folder)
        print(pipeline.ask(args.question))


if __name__ == "__main__":
    main()
