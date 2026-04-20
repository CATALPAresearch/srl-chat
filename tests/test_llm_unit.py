"""
Unit tests for app/llm.py.

These tests are purely unit-level: they mock HTTP calls and env vars so
that no Ollama instance is required.  The tests are independent of the
database and of each other.
"""

import os
import sys
import json
import pathlib
import types
from unittest.mock import patch, MagicMock

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(content: str):
    """Build the same mock object that get_response() creates internally."""
    msg = types.SimpleNamespace(content=content)
    return types.SimpleNamespace(message=msg)


# ---------------------------------------------------------------------------
# get_llm_response — DISABLE_LLM guard
# ---------------------------------------------------------------------------

class TestDisableLlm:
    """When DISABLE_LLM=true, no HTTP call should be made and the stub is returned."""

    def test_returns_stub_string(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "true"}):
            from app.llm import get_llm_response  # noqa: PLC0415
            with patch("app.llm.get_response") as mock_get:
                result = get_llm_response("system prompt")
        mock_get.assert_not_called()
        assert "Hallo" in result or "Interview" in result  # German stub

    def test_returns_string_type(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "true"}):
            from app.llm import get_llm_response
            result = get_llm_response("x", user_prompt="y")
        assert isinstance(result, str)

    def test_false_value_does_not_short_circuit(self):
        """DISABLE_LLM=false should proceed to call get_response."""
        with patch.dict(os.environ, {"DISABLE_LLM": "false"}):
            from app.llm import get_llm_response
            with patch("app.llm.get_response") as mock_get:
                mock_get.return_value = _mock_response("Hello!")
                result = get_llm_response("system")
        mock_get.assert_called()
        assert result == "Hello!"


# ---------------------------------------------------------------------------
# get_response — HTTP layer
# ---------------------------------------------------------------------------

class TestGetResponse:
    """Tests for get_response(), which wraps the Ollama HTTP API."""

    def _make_ollama_json(self, content: str) -> dict:
        return {"message": {"content": content}}

    def test_returns_mock_with_message_content(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://localhost:11434"}):
            from app.llm import get_response
            with patch("app.llm.requests.post") as mock_post:
                mock_post.return_value.json.return_value = self._make_ollama_json("Answer text")
                result = get_response([{"role": "user", "content": "hi"}], 0.0)
        assert result is not None
        assert hasattr(result, "message")
        assert result.message.content == "Answer text"

    def test_returns_none_on_http_exception(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://localhost:11434"}):
            from app.llm import get_response
            with patch("app.llm.requests.post", side_effect=ConnectionError("refused")):
                result = get_response([{"role": "user", "content": "hi"}], 0.0)
        assert result is None

    def test_returns_none_on_timeout(self):
        import requests as req
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://localhost:11434"}):
            from app.llm import get_response
            with patch("app.llm.requests.post", side_effect=req.exceptions.Timeout):
                result = get_response([{"role": "user", "content": "hi"}], 0.0)
        assert result is None

    def test_empty_content_returns_mock_with_empty_string(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://localhost:11434"}):
            from app.llm import get_response
            with patch("app.llm.requests.post") as mock_post:
                mock_post.return_value.json.return_value = {"message": {"content": ""}}
                result = get_response([], 0.0)
        assert result is not None
        assert result.message.content == ""

    def test_malformed_json_returns_none(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://localhost:11434"}):
            from app.llm import get_response
            with patch("app.llm.requests.post") as mock_post:
                mock_post.return_value.json.side_effect = json.JSONDecodeError("bad", "", 0)
                result = get_response([], 0.0)
        assert result is None


# ---------------------------------------------------------------------------
# get_llm_response — retry logic
# ---------------------------------------------------------------------------

class TestGetLlmResponseRetry:
    """Verify retry behaviour when get_response returns None or empty content."""

    def test_retries_and_eventually_succeeds(self):
        side_effects = [None, None, _mock_response("Final answer")]
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://x"}):
            from app.llm import get_llm_response
            with patch("app.llm.get_response", side_effect=side_effects):
                with patch("app.llm.time.sleep"):  # skip actual sleep
                    result = get_llm_response("sys", user_prompt="q")
        assert result == "Final answer"

    def test_raises_assertion_when_all_retries_fail(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://x"}):
            from app.llm import get_llm_response
            with patch("app.llm.get_response", return_value=None):
                with patch("app.llm.time.sleep"):
                    with pytest.raises(AssertionError, match="empty response"):
                        get_llm_response("sys")

    def test_retries_on_empty_content(self):
        side_effects = [_mock_response(""), _mock_response(""), _mock_response("Got it")]
        with patch.dict(os.environ, {"DISABLE_LLM": "false", "BASE_URL": "http://x"}):
            from app.llm import get_llm_response
            with patch("app.llm.get_response", side_effect=side_effects):
                with patch("app.llm.time.sleep"):
                    result = get_llm_response("sys")
        assert result == "Got it"


# ---------------------------------------------------------------------------
# Prompt builder helpers (no DB needed — they only do string operations
# on prompts loaded from config/ and user.language_id via get_language_by_id)
# ---------------------------------------------------------------------------

class TestPromptBuilders:
    """Test that prompt builder functions substitute placeholders correctly."""

    def _make_user(self, lang_code="en", study_subject="Computer Science"):
        user = MagicMock()
        user.language_id = 1
        user.study_subject = study_subject
        return user

    def _stub_language(self, lang_code="en"):
        lang = MagicMock()
        lang.lang_code = lang_code
        return lang

    def _load_prompts(self, lang_code="en") -> dict:
        prompts_path = BACKEND_DIR / "config" / "prompts.json"
        with open(prompts_path, encoding="utf-8") as f:
            return json.load(f)[lang_code]

    def test_get_intro_prompt_replaces_limit(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false"}):
            from app.llm import get_intro_prompt
            user = self._make_user()
            with patch("app.llm.get_language_by_id", return_value=self._stub_language("en")):
                result = get_intro_prompt(user, limit=6)
        assert "${limit}" not in result
        assert "6" in result

    def test_get_context_prompt_replaces_context_and_subject(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false"}):
            from app.llm import get_context_prompt
            user = self._make_user(study_subject="Physics")
            with patch("app.llm.get_language_by_id", return_value=self._stub_language("en")):
                result = get_context_prompt("lectures", user)
        assert "${context}" not in result
        assert "${subject}" not in result
        assert "lectures" in result
        assert "Physics" in result

    def test_get_frequency_prompt_replaces_strategy_and_context(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false"}):
            from app.llm import get_frequency_prompt
            user = self._make_user()
            with patch("app.llm.get_language_by_id", return_value=self._stub_language("en")):
                result = get_frequency_prompt(user, context="exams", strategy="spaced repetition")
        assert "${strategy}" not in result
        assert "${context}" not in result
        assert "spaced repetition" in result
        assert "exams" in result

    def test_get_prompt_system_returns_string(self):
        with patch.dict(os.environ, {"DISABLE_LLM": "false"}):
            from app.llm import get_prompt
            user = self._make_user()
            with patch("app.llm.get_language_by_id", return_value=self._stub_language("en")):
                result = get_prompt(user, "system")
        assert isinstance(result, str)
        assert len(result) > 10
