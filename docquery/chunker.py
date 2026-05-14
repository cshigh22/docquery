import re
from dataclasses import dataclass

from .loader import Document

WORDS_PER_CHUNK = 500
OVERLAP_WORDS = 50
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: int


def _word_count(text: str) -> int:
    return len(text.split())


def _split_long_paragraph(para: str) -> list[str]:
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(para) if s.strip()]
    return sentences or [para]


def chunk_document(doc: Document) -> list[Chunk]:
    paragraphs = [p.strip() for p in doc.text.split("\n\n") if p.strip()]

    units: list[str] = []
    for para in paragraphs:
        if _word_count(para) > WORDS_PER_CHUNK:
            units.extend(_split_long_paragraph(para))
        else:
            units.append(para)

    chunks: list[Chunk] = []
    current: list[str] = []
    current_words = 0
    chunk_id = 0

    for unit in units:
        unit_words = _word_count(unit)
        if current and current_words + unit_words > WORDS_PER_CHUNK:
            chunks.append(
                Chunk(
                    text="\n\n".join(current),
                    source=doc.filename,
                    chunk_id=chunk_id,
                )
            )
            chunk_id += 1

            overlap: list[str] = []
            overlap_words = 0
            for prev in reversed(current):
                if overlap_words >= OVERLAP_WORDS:
                    break
                overlap.insert(0, prev)
                overlap_words += _word_count(prev)
            current = overlap
            current_words = overlap_words

        current.append(unit)
        current_words += unit_words

    if current:
        chunks.append(
            Chunk(
                text="\n\n".join(current),
                source=doc.filename,
                chunk_id=chunk_id,
            )
        )

    return chunks


def chunk_documents(docs: list[Document]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in docs:
        chunks.extend(chunk_document(doc))
    return chunks
