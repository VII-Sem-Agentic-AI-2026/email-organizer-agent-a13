# Assignment 4 — Memory & Retrieval

## Aim
Separate short-term run state from long-term stored email history, then retrieve relevant history using tags and similarity.

## What is implemented
- `RunState`: holds the current email and draft for the active run only.
- `MemoryItem`: typed long-term record containing text, tags, source and metadata.
- `MemoryStore`: stores historical items separately from current run state.
- Tag retrieval: returns records matching requested tags.
- Similarity retrieval: ranks prior records and returns the top `k` matches.
- `MemoryAgent`: calls both retrieval methods.
- Tests verify tag retrieval, similarity ranking, top-k, and separation of state from archive.

## Run on Windows
```powershell
py -3.11 main.py
```

Run tests:
```powershell
py -3.11 -m unittest discover -s tests -v
```

No external packages or credentials are required.

## Important implementation note
The build book describes tag filters and embedding similarity. This standalone assignment implements tag filtering and an offline cosine-similarity baseline over token-frequency vectors so it runs immediately without downloading a model. This is similarity retrieval, but it is **not neural embedding retrieval**. A sentence-embedding provider can be added later behind the same retrieval interface if the course requires actual embeddings.

## Project relationship
The main Email Organizer project already has `memory.py` and `thread_grounding.py`. The project notes describe its existing memory as keyword/tag-based retrieval and thread grounding as word-overlap matching, not vector embeddings. This assignment isolates short-term run state from the archive and demonstrates tag + ranked similarity retrieval without changing the main project files.
