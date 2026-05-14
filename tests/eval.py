import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

from docquery.pipeline import Pipeline  # noqa: E402

SAMPLE_DOCS = Path(__file__).resolve().parent / "sample_docs"

# Each item is a dict with keys:
#   name: str
#   question: str
#   expected_keywords: list[str]   # all must appear (case-insensitive) in the answer
#   expected_source: str | None    # filename expected in retrieved sources, or None to skip
TEST_CASES: list[dict] = [
    {
        "name": "faithfulness_mockingbird",
        "question": "In To Kill a Mockingbird, what is the name of the sheriff of Maycomb?",
        "expected_keywords": ["don't have enough information"],
        "expected_source": None,
    },
    {
        "name": "aggregation_nc_meals",
        "question": "What was the total amount spent on all meals (breakfast, lunch, dinner, coffee) during the North Carolina trip?",
        "expected_keywords": ["162"],
        "expected_source": "travel-notes.txt",
    },
    {
        "name": "negative_constraint_tuna_brand",
        "question": "What was the brand of the tuna used in the quick kimchi stew recipe?",
        "expected_keywords": ["don't have enough information"],
        "expected_source": None,
    },
    {
        "name": "source_attribution_messi",
        "question": "How many Ballon d'Ors has Lionel Messi won according to the documents?",
        "expected_keywords": ["8", "eight"],
        "expected_source": "goat.txt",
    },
    {
        "name": "ingredient_extraction",
        "question": "How much gochugaru is needed for the seasoning base of the pork belly kimchi stew?",
        "expected_keywords": ["tbsp"],
        "expected_source": "recipes.md",
    },
]


def _missing_keywords(answer: str, keywords: list[str]) -> list[str]:
    lower = answer.lower()
    return [kw for kw in keywords if kw.lower() not in lower]


def _source_ok(sources: list[str], expected: str | None) -> bool:
    if expected is None:
        return True
    return expected in sources


def run_eval(verbose: bool = False) -> int:
    load_dotenv(_REPO_ROOT / ".env")
    pipeline = Pipeline.from_folder(str(SAMPLE_DOCS))

    failed: list[str] = []
    for case in TEST_CASES:
        name: str = case["name"]
        question: str = case["question"]
        expected_keywords: list[str] = case["expected_keywords"]
        expected_source: str | None = case["expected_source"]

        response, sources, chunks = pipeline.ask(question)

        missing = _missing_keywords(response, expected_keywords)
        src_ok = _source_ok(sources, expected_source)
        passed = not missing and src_ok

        marker = "✓" if passed else "✗"
        print(f"{marker} {name}: {question}")

        if verbose:
            retrieved = [f"{c.source}#{c.chunk_id}" for c in chunks]
            print(f"  retrieved: {retrieved}")

        if not passed:
            failed.append(name)
            if missing:
                print(f"  keywords missing: {missing}")
            if not src_ok:
                print(f"  expected source {expected_source!r} not in {sources}")
            preview = response[:200] + ("..." if len(response) > 200 else "")
            print(f"  answer: {preview}")

    total = len(TEST_CASES)
    passed_count = total - len(failed)
    print()
    print(f"Passed {passed_count}/{total} tests.")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run docquery eval suite.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print retrieved chunk sources for each test",
    )
    args = parser.parse_args()
    sys.exit(run_eval(verbose=args.verbose))


if __name__ == "__main__":
    main()
