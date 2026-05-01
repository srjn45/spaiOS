# M4: Persistent Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give spaiOS memory that survives across overlay sessions — storing what was worked on each day so it can answer "what have I been working on?" and carry relevant context forward automatically.

**Architecture:** A `MemoryStore` class wraps ChromaDB with three collections: `session_log` (one entry per session, chronological), `user_profile` (a single JSON doc), and `context_snippets` (things the user explicitly asks to remember, retrieved by semantic similarity). A `summarize_session()` function calls `llama3.2:3b` to generate a 2–3 sentence summary of the conversation when the overlay is hidden. The `Orchestrator` loads the last 5 session summaries on init and injects them into every system prompt. On hide, `Overlay` calls `end_session()` in a background thread so the UI doesn't freeze.

**Tech Stack:** `chromadb` (PersistentClient), `ollama` (nomic-embed-text embeddings + llama3.2:3b summarization), `pytest` + `unittest.mock`

---

## File Map

| File | Status | Responsibility |
|---|---|---|
| `src/spaiOS/core/memory.py` | **Create** | `MemoryStore` — all ChromaDB reads/writes |
| `src/spaiOS/core/summarizer.py` | **Create** | `summarize_session(history)` — calls Ollama |
| `src/spaiOS/core/orchestrator.py` | **Modify** | Accept `MemoryStore`, inject memory into prompt, add `end_session()` |
| `src/spaiOS/ui/overlay.py` | **Modify** | Create `MemoryStore`, pass to Orchestrator, call `end_session()` on hide |
| `tests/test_memory.py` | **Create** | Unit tests for `MemoryStore` |
| `tests/test_summarizer.py` | **Create** | Unit tests for `summarize_session` |
| `pyproject.toml` | **Modify** | Add `chromadb` dependency |

---

## Task 1: Install chromadb + pull nomic-embed-text

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add chromadb to pyproject.toml**

```toml
# In the [project] dependencies list, add:
"chromadb>=0.6.0",
```

- [ ] **Step 2: Install the dependency**

```bash
uv sync
```

Expected: resolves and installs chromadb and its dependencies (may take 1–2 minutes).

- [ ] **Step 3: Pull nomic-embed-text model**

```bash
ollama pull nomic-embed-text
```

Expected output ends with: `success` and model appears in `ollama list`.

- [ ] **Step 4: Smoke test both**

```bash
uv run python -c "
import chromadb, ollama
client = chromadb.EphemeralClient()
col = client.create_collection('smoke')
emb = ollama.embeddings(model='nomic-embed-text', prompt='hello world')
print('chromadb ok, embedding dims:', len(emb['embedding']))
"
```

Expected: prints `chromadb ok, embedding dims: 768`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Add chromadb dependency for persistent memory"
```

---

## Task 2: MemoryStore — session_log

**Files:**
- Create: `src/spaiOS/core/memory.py`
- Create: `tests/test_memory.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_memory.py`:

```python
import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_store():
    """Return a MemoryStore backed by an in-memory ChromaDB client."""
    with patch("chromadb.PersistentClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        sessions_col = MagicMock()
        profile_col = MagicMock()
        snippets_col = MagicMock()

        def get_or_create(name, **kwargs):
            if name == "session_log":
                return sessions_col
            if name == "user_profile":
                return profile_col
            return snippets_col

        mock_client.get_or_create_collection.side_effect = get_or_create

        from spaiOS.core.memory import MemoryStore
        store = MemoryStore.__new__(MemoryStore)
        store._client = mock_client
        store._sessions = sessions_col
        store._profile = profile_col
        store._snippets = snippets_col
        return store, sessions_col, profile_col, snippets_col


class TestStoreSession:
    def test_upserts_document_with_date_id(self):
        store, sessions_col, _, _ = _make_store()
        store.store_session("2026-05-01", "Worked on memory module", ["code"], ["memory impl"])
        sessions_col.upsert.assert_called_once()
        kwargs = sessions_col.upsert.call_args[1]
        assert kwargs["ids"] == ["2026-05-01"]
        assert "2026-05-01" in kwargs["documents"][0]
        assert "memory module" in kwargs["documents"][0]

    def test_document_contains_apps_and_tasks(self):
        store, sessions_col, _, _ = _make_store()
        store.store_session("2026-05-01", "Did stuff", ["chrome", "code"], ["browsed", "coded"])
        doc = sessions_col.upsert.call_args[1]["documents"][0]
        assert "chrome" in doc
        assert "browsed" in doc


class TestGetRecentSessions:
    def test_returns_empty_list_when_no_sessions(self):
        store, sessions_col, _, _ = _make_store()
        sessions_col.get.return_value = {"documents": [], "metadatas": []}
        result = store.get_recent_sessions()
        assert result == []

    def test_returns_last_n_sorted_by_date(self):
        store, sessions_col, _, _ = _make_store()
        sessions_col.get.return_value = {
            "documents": ["doc_old", "doc_new", "doc_mid"],
            "metadatas": [
                {"date": "2026-04-20"},
                {"date": "2026-05-01"},
                {"date": "2026-04-25"},
            ],
        }
        result = store.get_recent_sessions(n=2)
        assert result == ["doc_new", "doc_mid"]

    def test_returns_all_when_fewer_than_n(self):
        store, sessions_col, _, _ = _make_store()
        sessions_col.get.return_value = {
            "documents": ["only_one"],
            "metadatas": [{"date": "2026-05-01"}],
        }
        result = store.get_recent_sessions(n=5)
        assert result == ["only_one"]
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_memory.py -v
```

Expected: `ModuleNotFoundError: No module named 'spaiOS.core.memory'`

- [ ] **Step 3: Create `src/spaiOS/core/memory.py` with session_log**

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_memory.py::TestStoreSession tests/test_memory.py::TestGetRecentSessions -v
```

Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/spaiOS/core/memory.py tests/test_memory.py
git commit -m "Add MemoryStore with session_log collection"
```

---

## Task 3: MemoryStore — user_profile

**Files:**
- Modify: `src/spaiOS/core/memory.py`
- Modify: `tests/test_memory.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_memory.py`:

```python
class TestUserProfile:
    def test_get_returns_empty_dict_when_no_profile(self):
        store, _, profile_col, _ = _make_store()
        profile_col.get.return_value = {"documents": []}
        result = store.get_user_profile()
        assert result == {}

    def test_get_returns_stored_profile(self):
        store, _, profile_col, _ = _make_store()
        profile_col.get.return_value = {
            "documents": ['{"name": "Srajan", "timezone": "IST"}']
        }
        result = store.get_user_profile()
        assert result == {"name": "Srajan", "timezone": "IST"}

    def test_set_upserts_json_with_fixed_id(self):
        store, _, profile_col, _ = _make_store()
        store.set_user_profile({"name": "Srajan", "timezone": "IST"})
        profile_col.upsert.assert_called_once()
        kwargs = profile_col.upsert.call_args[1]
        assert kwargs["ids"] == ["profile"]
        stored = json.loads(kwargs["documents"][0])
        assert stored["name"] == "Srajan"
```

- [ ] **Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_memory.py::TestUserProfile -v
```

Expected: `AttributeError: 'MemoryStore' object has no attribute 'get_user_profile'`

- [ ] **Step 3: Add profile methods to `src/spaiOS/core/memory.py`**

Add after `get_recent_sessions`:

```python
    def get_user_profile(self) -> dict:
        results = self._profile.get(ids=["profile"])
        if not results["documents"]:
            return {}
        return json.loads(results["documents"][0])

    def set_user_profile(self, data: dict) -> None:
        self._profile.upsert(
            ids=["profile"],
            documents=[json.dumps(data)],
        )
```

- [ ] **Step 4: Run to confirm they pass**

```bash
uv run pytest tests/test_memory.py::TestUserProfile -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/spaiOS/core/memory.py tests/test_memory.py
git commit -m "Add user_profile get/set to MemoryStore"
```

---

## Task 4: MemoryStore — context_snippets

**Files:**
- Modify: `src/spaiOS/core/memory.py`
- Modify: `tests/test_memory.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_memory.py`:

```python
class TestContextSnippets:
    def test_store_snippet_upserts_with_hash_id(self):
        store, _, _, snippets_col = _make_store()
        store.store_snippet("ZeroDivisionError in utils.py line 42")
        snippets_col.upsert.assert_called_once()
        kwargs = snippets_col.upsert.call_args[1]
        assert len(kwargs["ids"]) == 1
        assert "ZeroDivisionError" in kwargs["documents"][0]

    def test_search_snippets_returns_empty_on_no_results(self):
        store, _, _, snippets_col = _make_store()
        snippets_col.query.return_value = {"documents": [[]]}
        result = store.search_snippets("error in python")
        assert result == []

    def test_search_snippets_returns_matched_docs(self):
        store, _, _, snippets_col = _make_store()
        snippets_col.query.return_value = {
            "documents": [["ZeroDivisionError in utils.py line 42"]]
        }
        result = store.search_snippets("division error")
        assert result == ["ZeroDivisionError in utils.py line 42"]
```

- [ ] **Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_memory.py::TestContextSnippets -v
```

Expected: `AttributeError: 'MemoryStore' object has no attribute 'store_snippet'`

- [ ] **Step 3: Add snippet methods to `src/spaiOS/core/memory.py`**

Add after `set_user_profile`:

```python
    def store_snippet(self, text: str) -> None:
        import hashlib
        snippet_id = hashlib.sha256(text.encode()).hexdigest()[:16]
        self._snippets.upsert(ids=[snippet_id], documents=[text])

    def search_snippets(self, query: str, n: int = 3) -> list[str]:
        results = self._snippets.query(query_texts=[query], n_results=n)
        docs = results.get("documents", [[]])
        return docs[0] if docs else []
```

- [ ] **Step 4: Run to confirm they pass**

```bash
uv run pytest tests/test_memory.py::TestContextSnippets -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest tests/test_memory.py -v
```

Expected: all 11 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/spaiOS/core/memory.py tests/test_memory.py
git commit -m "Add context_snippets store/search to MemoryStore"
```

---

## Task 5: Session Summarizer

**Files:**
- Create: `src/spaiOS/core/summarizer.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_summarizer.py`:

```python
from unittest.mock import patch


class TestSummarizeSession:
    def test_returns_empty_string_for_empty_history(self):
        from spaiOS.core.summarizer import summarize_session
        result = summarize_session([])
        assert result == ""

    def test_calls_ollama_with_user_and_assistant_turns(self):
        from spaiOS.core.summarizer import summarize_session

        history = [
            {"role": "user", "content": "list my files"},
            {"role": "assistant", "content": "You have 3 files in sandbox."},
            {"role": "system", "content": "ignored system message"},
        ]
        with patch("ollama.generate") as mock_gen:
            mock_gen.return_value = {"response": "User listed files in sandbox."}
            result = summarize_session(history)

        assert result == "User listed files in sandbox."
        call_prompt = mock_gen.call_args[1]["prompt"]
        assert "USER: list my files" in call_prompt
        assert "ASSISTANT: You have 3 files" in call_prompt
        assert "system" not in call_prompt.lower().split("conversation")[0]

    def test_strips_whitespace_from_response(self):
        from spaiOS.core.summarizer import summarize_session

        with patch("ollama.generate") as mock_gen:
            mock_gen.return_value = {"response": "  Summary with spaces.  "}
            result = summarize_session([{"role": "user", "content": "hi"}])

        assert result == "Summary with spaces."

    def test_truncates_long_history_before_sending(self):
        from spaiOS.core.summarizer import summarize_session

        long_msg = "x" * 500
        history = [{"role": "user", "content": long_msg}] * 20

        with patch("ollama.generate") as mock_gen:
            mock_gen.return_value = {"response": "Short summary."}
            summarize_session(history)

        call_prompt = mock_gen.call_args[1]["prompt"]
        assert len(call_prompt) < 6000
```

- [ ] **Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_summarizer.py -v
```

Expected: `ModuleNotFoundError: No module named 'spaiOS.core.summarizer'`

- [ ] **Step 3: Create `src/spaiOS/core/summarizer.py`**

```python
import ollama

_PROMPT_TEMPLATE = (
    "Summarize the following work session in 2-3 sentences. "
    "Describe what the user worked on, what was accomplished, "
    "and any important context for next time. Be concise and factual.\n\n"
    "Conversation:\n{history}\n\nSummary:"
)
_MAX_HISTORY_CHARS = 3000


def summarize_session(history: list[dict]) -> str:
    turns = [
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in history
        if msg.get("role") in ("user", "assistant")
    ]
    if not turns:
        return ""
    history_text = "\n".join(turns)[:_MAX_HISTORY_CHARS]
    prompt = _PROMPT_TEMPLATE.format(history=history_text)
    response = ollama.generate(model="llama3.2:3b", prompt=prompt)
    return response["response"].strip()
```

- [ ] **Step 4: Run to confirm they pass**

```bash
uv run pytest tests/test_summarizer.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/spaiOS/core/summarizer.py tests/test_summarizer.py
git commit -m "Add session summarizer using llama3.2:3b"
```

---

## Task 6: Wire MemoryStore into Orchestrator

**Files:**
- Modify: `src/spaiOS/core/orchestrator.py`
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_orchestrator.py` (check for existing test helpers first and reuse them):

```python
class TestOrchestratorMemory:
    def test_no_memory_context_when_memory_is_none(self):
        from spaiOS.core.orchestrator import Orchestrator
        orc = Orchestrator(memory=None)
        assert orc._memory_context == ""

    def test_memory_context_loaded_from_store_on_init(self):
        from unittest.mock import MagicMock
        from spaiOS.core.orchestrator import Orchestrator

        mock_memory = MagicMock()
        mock_memory.get_recent_sessions.return_value = [
            "Date: 2026-04-30\nSummary: Worked on voice pipeline."
        ]
        orc = Orchestrator(memory=mock_memory)
        assert "voice pipeline" in orc._memory_context

    def test_end_session_stores_summary_and_clears_history(self):
        from unittest.mock import MagicMock, patch
        from spaiOS.core.orchestrator import Orchestrator

        mock_memory = MagicMock()
        mock_memory.get_recent_sessions.return_value = []
        orc = Orchestrator(memory=mock_memory)
        orc._history = [
            {"role": "user", "content": "list files"},
            {"role": "assistant", "content": "You have 2 files."},
        ]

        with patch("spaiOS.core.summarizer.summarize_session", return_value="User listed files."):
            orc.end_session()

        mock_memory.store_session.assert_called_once()
        call_kwargs = mock_memory.store_session.call_args[0]
        assert "User listed files." in call_kwargs
        assert orc._history == []

    def test_end_session_is_noop_when_memory_is_none(self):
        from spaiOS.core.orchestrator import Orchestrator
        orc = Orchestrator(memory=None)
        orc._history = [{"role": "user", "content": "hi"}]
        orc.end_session()
        assert orc._history == []

    def test_system_prompt_includes_memory_context(self):
        from unittest.mock import MagicMock
        from spaiOS.core.orchestrator import Orchestrator, _build_system_prompt

        mock_memory = MagicMock()
        mock_memory.get_recent_sessions.return_value = [
            "Date: 2026-04-30\nSummary: Worked on voice pipeline."
        ]
        orc = Orchestrator(memory=mock_memory)
        prompt = _build_system_prompt({}, orc._memory_context)
        assert "voice pipeline" in prompt
```

- [ ] **Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_orchestrator.py::TestOrchestratorMemory -v
```

Expected: fails on `Orchestrator() takes no arguments` or similar.

- [ ] **Step 3: Update `Orchestrator.__init__` in `src/spaiOS/core/orchestrator.py`**

Find the `Orchestrator` class `__init__` (currently around line 370) and replace:

```python
    def __init__(self) -> None:
        self._history: list[dict] = []
        self._file_agent = FileAgent()
        self._chrome_agent = ChromeAgent()
        self._pending_delete: str | None = None
```

With:

```python
    def __init__(self, memory=None) -> None:
        self._history: list[dict] = []
        self._file_agent = FileAgent()
        self._chrome_agent = ChromeAgent()
        self._pending_delete: str | None = None
        self._memory = memory
        self._memory_context: str = self._load_memory_context()
```

- [ ] **Step 4: Add `_load_memory_context` and `end_session` to Orchestrator**

Add these two methods to the `Orchestrator` class, after `__init__`:

```python
    def _load_memory_context(self) -> str:
        if self._memory is None:
            return ""
        sessions = self._memory.get_recent_sessions(5)
        if not sessions:
            return ""
        return "\n---\n".join(sessions)

    def end_session(self) -> None:
        if self._memory is not None and self._history:
            import datetime
            from spaiOS.core.summarizer import summarize_session

            summary = summarize_session(self._history)
            if summary:
                self._memory.store_session(
                    datetime.date.today().isoformat(), summary, [], []
                )
                self._memory_context = self._load_memory_context()
        self.clear_history()
```

- [ ] **Step 5: Update `_build_system_prompt` signature to accept memory_context**

Find the current `_build_system_prompt` function (around line 57) and replace:

```python
def _build_system_prompt(ctx_data: dict) -> str:
    parts = []
    if ctx_data.get("app_name"):
        parts.append(f"Active app: {ctx_data['app_name']}")
    if ctx_data.get("window_title"):
        parts.append(f"Window title: {ctx_data['window_title']}")
    if not parts:
        return _BASE_SYSTEM_PROMPT
    screen_section = (
        "\n\nAdditional screen context (for general questions only — "
        "do NOT use this to answer file management requests):\n" + "\n".join(parts)
    )
    return _BASE_SYSTEM_PROMPT + screen_section
```

With:

```python
def _build_system_prompt(ctx_data: dict, memory_context: str = "") -> str:
    parts = []
    if ctx_data.get("app_name"):
        parts.append(f"Active app: {ctx_data['app_name']}")
    if ctx_data.get("window_title"):
        parts.append(f"Window title: {ctx_data['window_title']}")
    prompt = _BASE_SYSTEM_PROMPT
    if memory_context:
        prompt += (
            "\n\nRecent session history (use this to answer questions about "
            "what the user has been working on):\n" + memory_context
        )
    if parts:
        prompt += (
            "\n\nCurrent screen context (for general questions only — "
            "do NOT use this to answer file management requests):\n"
            + "\n".join(parts)
        )
    return prompt
```

- [ ] **Step 6: Update the `ask` method to pass memory_context**

Find in `ask()` the line:

```python
        system_prompt = _build_system_prompt(ctx_data)
```

Replace with:

```python
        system_prompt = _build_system_prompt(ctx_data, self._memory_context)
```

- [ ] **Step 7: Run tests to confirm they pass**

```bash
uv run pytest tests/test_orchestrator.py -v
```

Expected: all tests including new `TestOrchestratorMemory` pass.

- [ ] **Step 8: Commit**

```bash
git add src/spaiOS/core/orchestrator.py tests/test_orchestrator.py
git commit -m "Wire MemoryStore into Orchestrator — memory context in system prompt"
```

---

## Task 7: Wire session lifecycle into Overlay

**Files:**
- Modify: `src/spaiOS/ui/overlay.py`

There are no unit tests for Overlay (it requires a display). Verify manually.

- [ ] **Step 1: Add MemoryStore import and creation in `Overlay.__init__`**

In `src/spaiOS/ui/overlay.py`, add to the imports at the top:

```python
import threading
```

Find the `__init__` method. After `self._orchestrator = Orchestrator()`, replace it with:

```python
        try:
            from spaiOS.core.memory import MemoryStore
            _memory = MemoryStore()
        except Exception as exc:
            print(f"[spaiOS] Memory unavailable: {exc}")
            _memory = None
        self._orchestrator = Orchestrator(memory=_memory)
```

- [ ] **Step 2: Replace `clear_history()` with `end_session()` in hide paths**

There are three hide paths that should summarize + save (toggle, idle, Escape). The `/clear` command stays as `clear_history()` — user is explicitly resetting context, not ending a session.

In `toggle()` (around line 119), replace:

```python
            self._orchestrator.clear_history()
            self._idle_timer.stop()
            self.hide()
```

With:

```python
            threading.Thread(target=self._orchestrator.end_session, daemon=True).start()
            self._idle_timer.stop()
            self.hide()
```

In `_on_idle_timeout()` (around line 113), replace:

```python
            self._orchestrator.clear_history()
            self.hide()
```

With:

```python
            threading.Thread(target=self._orchestrator.end_session, daemon=True).start()
            self.hide()
```

In `keyPressEvent` Escape handler (around line 289), replace:

```python
                self._orchestrator.clear_history()
                self._idle_timer.stop()
                self.hide()
```

With:

```python
                threading.Thread(target=self._orchestrator.end_session, daemon=True).start()
                self._idle_timer.stop()
                self.hide()
```

- [ ] **Step 3: Run the full test suite to confirm no regressions**

```bash
uv run pytest tests/ -q
```

Expected: all tests pass (Overlay is not unit-tested so no new failures).

- [ ] **Step 4: Manual smoke test**

```bash
uv run spaiOS
```

1. Say "hey Jarvis" or press `Super+Space` to open overlay
2. Type "what should I remember about today?" — AI should answer from memory if sessions exist, or say it has none
3. Type anything (e.g. "list my files")
4. Press `Super+Space` again to hide — observe terminal for any errors in the background thread
5. Reopen overlay, type "what did we just talk about?" — AI should say something about listing files (from memory context loaded on next open)

Note: The memory is loaded once at `Orchestrator.__init__` (overlay start). After `end_session()` stores the new summary, the *next* time you open the overlay the Orchestrator is recreated with the updated memory. This is correct behavior — memory for the *current* session is not reflected until next open.

- [ ] **Step 5: Commit**

```bash
git add src/spaiOS/ui/overlay.py
git commit -m "Wire MemoryStore + end_session into Overlay lifecycle"
```

---

## Task 8: Wire /remember command for manual snippets

**Files:**
- Modify: `src/spaiOS/ui/overlay.py`
- Modify: `src/spaiOS/core/orchestrator.py`

The AI can't yet decide what's worth remembering. Add a `/remember <text>` slash command so the user can manually save anything.

- [ ] **Step 1: Add `remember_snippet` to Orchestrator**

In `src/spaiOS/core/orchestrator.py`, add after `end_session`:

```python
    def remember_snippet(self, text: str) -> str:
        if self._memory is None:
            return "Memory is not available."
        self._memory.store_snippet(text)
        return f"Remembered: {text}"
```

- [ ] **Step 2: Handle `/remember` in Overlay's `_on_prompt_submitted`**

In `src/spaiOS/ui/overlay.py`, in `_on_prompt_submitted`, add this block after the `/clear` handler (around line 141):

```python
        if prompt.strip().lower().startswith("/remember "):
            text = prompt.strip()[len("/remember "):].strip()
            if text:
                msg = self._orchestrator.remember_snippet(text)
            else:
                msg = "Usage: /remember <something to remember>"
            self._input_row.clear()
            self._response_view.show_response(msg)
            self._input_row.set_enabled(True)
            self._input_row.focus()
            self._reset_idle_timer()
            return
```

- [ ] **Step 3: Run full test suite**

```bash
uv run pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 4: Manual test**

Open overlay, type `/remember I prefer dark theme and lo-fi music while coding`. Should respond: `Remembered: I prefer dark theme and lo-fi music while coding.`

- [ ] **Step 5: Commit**

```bash
git add src/spaiOS/ui/overlay.py src/spaiOS/core/orchestrator.py
git commit -m "Add /remember slash command for manual context snippets"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by |
|---|---|
| ChromaDB with nomic-embed-text | Task 1 + 2 (`_OllamaEmbedFn`) |
| session_log collection | Task 2 |
| user_profile collection | Task 3 |
| context_snippets collection | Task 4 |
| Load last 5 sessions into system prompt | Task 6 |
| Auto-summarize on session end | Task 6 (`end_session`) |
| Triggered on overlay close | Task 7 |
| "what have I been working on?" scenario | Covered by Task 6 prompt injection |
| Manual snippet storage | Task 8 |

**Gaps / deferred:**
- `apps_used` and `tasks_completed` fields in `store_session` are always `[]` for now — the AI would need to extract these from the summary, which adds complexity. Left as empty lists; the summary text carries the real content.
- Auto-semantic injection of snippets into prompts (searching snippets per query and injecting top matches) is not in this plan — the snippets are stored and searchable but not yet auto-injected. Add in a future iteration once the base is stable.
- `user_profile` is stored but nothing writes to it yet. `/profile set name=Srajan` command can be added in a future iteration.

**Placeholder scan:** None found.

**Type consistency:** `MemoryStore` methods use `list[str]` for `apps_used`/`tasks_completed`. `summarize_session` takes `list[dict]`. `_build_system_prompt` takes `str` for `memory_context`. All consistent across tasks.
