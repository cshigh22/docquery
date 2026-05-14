import re

from rank_bm25 import BM25Okapi

from .chunker import Chunk

# Small list (~35): articles, light function words, common auxiliaries.
# Avoid long NLTK-style lists — they hurt BM25 on short queries.
STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "to",
        "of",
        "in",
        "on",
        "at",
        "for",
        "with",
        "by",
        "from",
        "as",
        "and",
        "or",
        "but",
        "if",
        "that",
        "this",
        "it",
        "its",
        "i",
        "you",
        "he",
        "she",
        "we",
        "they",
    }
)


def _tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"\w+", text.lower()) if w not in STOPWORDS]


class BM25Retriever:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.tokenized_chunks = [_tokenize(c.text) for c in chunks]
        self.bm25 = BM25Okapi(self.tokenized_chunks)

    def search(self, query: str, k: int = 6) -> list[Chunk]:
        query_tokens = _tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        top_idx = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:k]
        return [self.chunks[i] for i in top_idx]
