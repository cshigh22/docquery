from dataclasses import dataclass
from pathlib import Path


@dataclass
class Document:
    filename: str
    text: str


def load_folder(path: str) -> list[Document]:
    docs: list[Document] = []
    folder = Path(path)
    for file in sorted(folder.rglob("*")):
        if not file.is_file():
            continue
        if file.suffix.lower() == ".txt":
            docs.append(Document(filename=file.name, text=file.read_text()))
        else:
            print(f"Warning: skipping non-.txt file: {file.name}")
    return docs
