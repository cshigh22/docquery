from .chunker import Chunk, chunk_documents
from .llm import answer
from .loader import Document, load_folder
from .retriever import BM25Retriever


class Pipeline:
    def __init__(self, docs: list[Document]) -> None:
        self.docs = docs
        self.chunks = chunk_documents(docs)
        self.retriever = BM25Retriever(self.chunks)

    @classmethod
    def from_folder(cls, path: str) -> "Pipeline":
        return cls(load_folder(path))

    def ask(self, question: str, k: int = 6) -> tuple[str, list[str], list[Chunk]]:
        top_chunks = self.retriever.search(question, k=k)
        context = "\n\n".join(
            f"[Source: {c.source}, chunk {c.chunk_id}]\n{c.text}"
            for c in top_chunks
        )
        response = answer(question, context)

        seen: set[str] = set()
        sources: list[str] = []
        for c in top_chunks:
            if c.source not in seen:
                seen.add(c.source)
                sources.append(c.source)
        return response, sources, top_chunks
