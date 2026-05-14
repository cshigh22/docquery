from .llm import answer
from .loader import Document, load_folder


class Pipeline:
    def __init__(self, docs: list[Document]) -> None:
        self.docs = docs

    @classmethod
    def from_folder(cls, path: str) -> "Pipeline":
        return cls(load_folder(path))

    def ask(self, question: str) -> str:
        context = "\n\n".join(
            f"=== {doc.filename} ===\n{doc.text}" for doc in self.docs
        )
        return answer(question, context)
