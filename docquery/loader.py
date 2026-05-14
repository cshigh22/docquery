from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class Document:
    filename: str
    text: str


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def _read_text(file: Path) -> str:
    return file.read_text(encoding="utf-8")


def _read_pdf(file: Path) -> str:
    reader = PdfReader(str(file))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def load_folder(path: str) -> list[Document]:
    docs: list[Document] = []
    folder = Path(path)
    for file in sorted(folder.rglob("*")):
        if not file.is_file():
            continue
        ext = file.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"Warning: skipping unsupported file: {file.name}")
            continue
        try:
            text = _read_pdf(file) if ext == ".pdf" else _read_text(file)
        except Exception as e:
            print(f"Skipping {file.name}: {e}")
            continue
        docs.append(Document(filename=file.name, text=text))
    if not docs:
        raise ValueError(
            f"No documents loaded from {path!r}. "
            f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}."
        )
    return docs
