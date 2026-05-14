# docquery

A command-line tool for asking natural-language questions about a folder of text, markdown, and PDF documents. It runs BM25 retrieval over chunked documents and grounds the answer in the retrieved chunks via Gemini 2.5 Flash, with inline source citations.

## Quickstart

```bash
git clone https://github.com/cshigh22/docquery && cd docquery
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit and set GEMINI_API_KEY
python -m docquery.cli ask tests/sample_docs "What does docquery do?"
```

## Example

```
$ python -m docquery.cli ask tests/sample_docs "What is the remote-work stipend at Acme Robotics, and what is it intended to cover?"
The standard remote-work stipend at Acme Robotics is $75 per month [acme_remote_policy.md]. It is intended to offset internet and utility costs [acme_remote_policy.md].

Sources: acme_remote_policy.md, 1706.03762v7.pdf
```

## How it works

The loader walks the folder, reads `.txt` and `.md` as UTF-8 text and `.pdf` via pypdf, and skips a single unreadable file with a warning rather than crashing the whole load. The chunker splits each document on double newlines, packs paragraphs into chunks of about 500 words with roughly 50 words of overlap, and falls back to sentence splitting if a single paragraph exceeds the chunk size. The retriever tokenizes chunks into lowercase word tokens, drops a short stopword list, and indexes them with `rank_bm25.BM25Okapi`. For each question, the top six chunks by BM25 score are concatenated with `[Source: filename, chunk N]` headers and passed as context to Gemini 2.5 Flash, which is system-prompted to answer only from that context, cite the source filename inline, or refuse explicitly when the context is insufficient.

A single `ask` call runs the full chain once. The `chat` subcommand builds the index once and reuses it across questions.

## Design decisions

I called out the choices below because each had a credible alternative I deliberately did not take.

### BM25 over embeddings

BM25 was the right tool for the time budget: no embedding API calls during indexing, no second .env key, a build that completes in milliseconds for the included corpus, and a dependency footprint of one small package. The cost is lexical-only matching. A query about "PTO" will not retrieve a chunk that uses "vacation," and `notes.txt` documents this rather than papering over it. Embeddings are the obvious next step but would have required another client, persistence to avoid re-embedding on every run, and time I did not have.

### CLI over web

A CLI iterates faster than a web stack, composes with shell pipes, and is reproducible from a single command in this README. A web UI would have meant adding a server, a frontend, and a hosting story, none of which exercises the retrieval question I actually wanted to answer. The cost is accessibility for non-technical users, which the quickstart partially mitigates.

### Gemini 2.5 Flash specifically

Flash gives extractive-QA quality close to Pro at a fraction of the cost and latency, which matters for `chat` mode where every prompt is a billable round-trip. The 1M-token context window means we never need to truncate, so the chunker can target chunk quality rather than fitting under a context budget. The model name lives only in `docquery/llm.py:answer` and is the single point of change for swapping providers.

### Paragraph-aware chunking with ~500-word target

Splitting on paragraph breaks preserves the semantic units the author already put in the document. About 500 words is the largest chunk size that lets six chunks fit comfortably alongside the question and instructions in the prompt; 50 words of overlap covers facts that span a paragraph break (a definition in one paragraph, the example in the next). The sentence-split fallback handles PDFs where pypdf yields one giant blob with no paragraph structure to find.

### Stuff retrieved chunks into context; no conversation memory

Each `ask` retrieves independently. `chat` reuses the index but not prior turns. This makes every answer cite the exact chunks it was grounded in, keeps prompt size bounded, and removes a class of confusion where follow-ups silently inherit context the user has forgotten. The cost is true conversational follow-up — "what about the second one?" has to be rephrased — which felt acceptable for a Q&A tool over static documents.

## What I skipped

- Scanned PDFs (no OCR) — pypdf returns empty strings on image-only pages, and adding an OCR path doubles the dependency surface for one document class.
- `.docx`, `.html`, and other formats — each new format adds a parser, an encoding edge case, and an error mode; `.txt`/`.md`/`.pdf` covers the spec.
- Semantic / embedding retrieval — see "BM25 over embeddings"; this is the highest-leverage future addition, not a v1 feature.
- Web UI — see "CLI over web"; the UI does not change the retrieval question.
- Conversation memory in chat mode — see "Stuff retrieved chunks into context"; `chat` is a REPL, not a chatbot.
- Persistence / caching of the BM25 index — the index rebuilds in well under a second on the included corpus; persistence would add cache invalidation without yet solving a real problem.
- Streaming output from Gemini — response sizes are small enough that streaming buys less than a second of perceived latency at the cost of complicating the REPL input loop.

## Known weaknesses

The most important is BM25's blindness to synonyms — a question about "PTO" will not retrieve a chunk about "vacation policy," and the loader, chunker, and model cannot fix this (`notes.txt` covers it in detail). PDF text extraction is noisy on multi-column or formula-heavy pages: chunk 15 of `1706.03762v7.pdf` ("Attention Visualizations") is a good demonstration, with word-per-line layout and `<EOS>`/`<pad>` artifacts that BM25 happily indexes as real tokens. When the corpus is small and only one chunk is actually relevant to a query, top-6 retrieval still returns five irrelevant chunks; Gemini ignores them but they cost prompt tokens. There is no rate-limit or retry handling around the Gemini call — hitting a 429 on the free tier crashes the eval mid-suite and would crash an interactive `chat` session the same way. Finally, the BM25 index rebuilds on every `ask` invocation; the included corpus makes this invisible, but it would not scale.

## Evaluation

`tests/eval.py` runs five hand-picked test cases against `tests/sample_docs/` — covering faithfulness (refusing when the answer is not in context), aggregation across a document, refusal on a missing detail, source attribution, and ingredient extraction. Each case checks that expected keywords appear as case-insensitive substrings of the answer and that the expected source filename appears in the retrieved set. The script loads the pipeline once, exits 0 on a clean run, 1 on any failure.


## With more time

1. Rate-limit and retry handling around the Gemini call. The eval crash above is reason enough, and the same failure mode would hit any `chat` session that ran past 20 questions in a day.
2. Hybrid retrieval: keep BM25 for rare/exact-term recall, add a small embedding model for synonym matching, blend the scores. Highest-leverage quality win.
3. Better PDF extraction via `pdfplumber` or a vision-model fallback for multi-column pages, to fix the chunk-15 problem visibly.
4. Persistence of the BM25 index keyed by a hash of the folder contents, so `chat` startup is instant on a stable corpus and re-runs on changed corpora.
5. A richer eval: more cases per category, and a tiny regression file so a bad change shows up as a delta rather than a single boolean.
6. Streaming output from Gemini in `chat` mode for perceived responsiveness on longer answers.
7. Web UI to be friendly for all users.

## Weakest part

The weakest part is PDF text extraction. `pypdf.extract_text()` is the only PDF path, and it produces visibly garbage tokens on the kinds of documents people will actually try first — multi-column academic papers, anything with formulas, tables, or footnotes. Chunk 15 of `1706.03762v7.pdf` shows the failure mode plainly: each word on its own line, `<EOS>` and `<pad>` artifacts indexed as real terms, and no way for the downstream pipeline to tell that this chunk is mostly noise. 
