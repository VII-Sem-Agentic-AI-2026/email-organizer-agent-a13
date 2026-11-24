import math
import re
from collections import Counter
from models import MemoryItem, RunState, RetrievalHit

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

class MemoryStore:
    """
    Long-term archive of prior email items.
    Current run state is kept separately in RunState.
    """
    def __init__(self, items: list[MemoryItem] | None = None):
        self._items = list(items or [])

    def add(self, item: MemoryItem) -> None:
        if not isinstance(item, MemoryItem):
            raise TypeError("Only MemoryItem objects can be stored.")
        self._items.append(item)

    def all_items(self) -> list[MemoryItem]:
        return list(self._items)

    def retrieve_by_tags(self, tags: list[str]) -> list[RetrievalHit]:
        wanted = {tag.strip().lower() for tag in tags if tag.strip()}
        hits = []
        for item in self._items:
            item_tags = {tag.lower() for tag in item.tags}
            matched = sorted(wanted & item_tags)
            if matched:
                hits.append(RetrievalHit(item=item, score=len(matched), matched_tags=matched))
        return sorted(hits, key=lambda hit: (-hit.score, hit.item.item_id))

    def retrieve_similar(self, query: str, k: int = 5) -> list[RetrievalHit]:
        """
        Lightweight cosine similarity baseline using token-frequency vectors.
        It is deterministic and runs offline. It is not a neural embedding model.
        """
        if k < 1:
            raise ValueError("k must be at least 1.")
        query_tokens = Counter(tokenize(query))
        if not query_tokens:
            return []

        scored = []
        for item in self._items:
            item_tokens = Counter(tokenize(item.text))
            if not item_tokens:
                continue
            common = set(query_tokens) & set(item_tokens)
            dot = sum(query_tokens[t] * item_tokens[t] for t in common)
            q_norm = math.sqrt(sum(v * v for v in query_tokens.values()))
            d_norm = math.sqrt(sum(v * v for v in item_tokens.values()))
            score = dot / (q_norm * d_norm) if q_norm and d_norm else 0.0
            if score > 0:
                scored.append(RetrievalHit(item=item, score=score))
        return sorted(scored, key=lambda hit: (-hit.score, hit.item.item_id))[:k]

class MemoryAgent:
    def __init__(self, store: MemoryStore):
        self.store = store

    def retrieve(self, task_tags: list[str], current_draft: str, k: int = 5):
        # Tag retrieval and similarity retrieval are separate operations.
        tagged = self.store.retrieve_by_tags(task_tags)
        similar = self.store.retrieve_similar(current_draft, k=k)
        return {"tagged": tagged, "similar": similar}
