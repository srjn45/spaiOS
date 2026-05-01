import json
from pathlib import Path

import chromadb
import ollama

_MEMORY_DIR = Path.home() / ".local" / "share" / "spaiOS" / "memory"


class _OllamaEmbedFn:
    def __call__(self, input: list[str]) -> list[list[float]]:
        return [
            ollama.embeddings(model="nomic-embed-text", prompt=text)["embedding"]
            for text in input
        ]


class MemoryStore:
    def __init__(self, path: Path = _MEMORY_DIR) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        embed_fn = _OllamaEmbedFn()
        self._sessions = self._client.get_or_create_collection(
            "session_log", embedding_function=embed_fn
        )
        self._profile = self._client.get_or_create_collection("user_profile")
        self._snippets = self._client.get_or_create_collection(
            "context_snippets", embedding_function=embed_fn
        )

    def store_session(
        self,
        date: str,
        summary: str,
        apps_used: list[str],
        tasks_completed: list[str],
    ) -> None:
        doc = (
            f"Date: {date}\n"
            f"Summary: {summary}\n"
            f"Apps: {', '.join(apps_used)}\n"
            f"Tasks: {', '.join(tasks_completed)}"
        )
        self._sessions.upsert(
            ids=[date],
            documents=[doc],
            metadatas=[{"date": date}],
        )

    def get_recent_sessions(self, n: int = 5) -> list[str]:
        results = self._sessions.get(include=["documents", "metadatas"])
        docs = results["documents"]
        metas = results["metadatas"]
        if not docs:
            return []
        pairs = sorted(
            zip(metas, docs),
            key=lambda p: p[0]["date"],
            reverse=True,
        )
        return [doc for _, doc in pairs[:n]]
