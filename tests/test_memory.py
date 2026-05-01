import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_store():
    """Return a MemoryStore backed by mocked ChromaDB collections."""
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
