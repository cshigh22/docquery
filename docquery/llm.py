import os

from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided documents.

The context is a series of chunks, each prefixed with a header like:
    [Source: filename.pdf, chunk 3]

Rules:
- Answer ONLY from the provided context.
- Cite the source filename inline whenever you use information from a chunk, using square brackets, like [filename.pdf]. Do not include the chunk number in your citation, just the filename.
- If the context does not contain enough information to answer, respond exactly: "I don't have enough information."
"""


def answer(question: str, context: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    client = genai.Client(api_key=api_key)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        contents=prompt,
    )
    return response.text or ""
