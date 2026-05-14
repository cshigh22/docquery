# How I used AI tools

I used Claude Code (Anthropic's CLI) throughout this build, mostly for scaffolding and structural review rather than open-ended design. The workflow was vertical-slicing: I described the next end-to-end slice in detail. I aksed for skeleton, then .md/.pdf support, then chunking + BM25 retrieval, then chat mode, then the eval harness. I let Claude draft the modules, read the diff, and either accepted, tweaked, or rewrote whichever parts seemed wrong. Most of the code came out of Claude on the first pass; the parts I rewrote were small but load-bearing.

## Where it helped

The most useful applications were the ones where the structure was obvious but the boilerplate was tedious.

### Initial repo scaffolding

I described the file layout, the dataclass shape, the CLI command, and the system prompt for the LLM, and Claude produced the full directory tree with working code in one pass. This saved twenty-plus minutes of `__init__.py` creation, argparse setup, and `.env`/`.gitignore` boilerplate that I would otherwise have copy-pasted from a previous project.

### The chunker algorithm

I specified the chunking behavior in prose — paragraph-pack to about 500 words, about 50 words of overlap, sentence-split fallback for oversized paragraphs — and Claude produced a working implementation in one pass, including the edge case where the overlap is built from the just-emitted chunk before appending the next paragraph. Writing this by hand would have taken longer and probably produced an off-by-one error on the overlap window.

## Where I overrode it

Three places stand out.

### Stopword list

Claude generated a stopword list of about thirty common function words including some I considered too aggressive ("had", "do", "does", "will", "would"). I trimmed those out and added a few it had missed ("being", "but", "if", "i", "you", "he", "she", "we", "they"), and left a comment in `retriever.py` explaining the reason: long NLTK-style stopword lists hurt BM25 on short queries because too many query tokens get dropped before scoring. This is the kind of judgment Claude does not have without being told.

### Chunker overlap cap

Claude's initial chunker exited the overlap loop early if it had already grabbed two paragraphs, regardless of word count. I removed that condition because for documents with short paragraphs the 50-word target should drive the cap, not an arbitrary paragraph count — three short paragraphs of fifteen words each is still well within the overlap budget and gives the next chunk more useful context.

### CLI error handling and chat mode

I asked Claude for a minimal CLI initially and got one. When I went to add `chat`, I refactored the file myself instead of asking — pulling out `_die`, `_build_pipeline`, `_run_ask`, and `_run_chat` helpers, validating the folder path with a clear error before attempting to load, and handling `EOFError`/`KeyboardInterrupt` in the REPL loop. What Claude would have produced if I had asked would probably have been correct but flatter, and I wanted the structure to make adding future subcommands obvious.

## Where I did not trust it: evaluation

The substantive human contribution to this project is the eval. I wrote the five cases in `tests/eval.py` myself, picked the sample corpus, and chose the assertion shape for each case (keyword presence, optional expected source filename). I did not ask Claude to generate test cases or to suggest what would be worth testing. The reason is structural. An eval is the contract that tells you whether the rest of the system works, and if the same tool writes both the implementation and the test, the test's notion of "correct" is whatever the tool already believes the implementation does. Any blind spot in the implementation is mirrored in the spec, and the suite passes by construction. Whoever is going to be surprised by a failure has to be the one who writes the assertions.

The stopword and chunker overrides above are real, but they are local judgment calls that any careful reader of the diff would have caught. The decision not to delegate the eval is the one that determined whether I could believe anything else in this repo. The comment I left in `retriever.py` about the stopword list serves the same instinct in miniature: when an override exists for a non-obvious reason, the reason goes in a comment at the call site, not just in this document.

## What I wrote without AI

The eval suite and sample corpus are covered in the section above. Beyond those:

- The vertical-slicing approach to the build itself — each prompt scoped to one end-to-end slice with explicit "do not add X" constraints.
- The framing of each design decision as a tradeoff rather than a feature, and the choice of which decisions were worth calling out at all.
- The section ordering of this document and of the README — Claude scaffolded what I asked for, but the order of sections is the argument.
