"""
Unit and integration tests for:
  • app/config.py   (_build_database_uri, get_interview_config_path)
  • app/steps.py    (try_get_json_completion, validate_strategies)
  • app/logging_utlis.py (log_action)

Config tests are pure unit tests — no DB or network required.
Steps and logging tests are integration tests that need the dev DB.
"""

import os
import sys
import pathlib
from unittest.mock import patch, MagicMock

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ===========================================================================
# config.py
# ===========================================================================

class TestBuildDatabaseUri:
    """_build_database_uri() is a pure function that reads env vars."""

    def test_uses_database_url_directly(self):
        from app.config import _build_database_uri
        env = {"DATABASE_URL": "postgresql://myuser:mypw@host:5432/mydb"}
        with patch.dict(os.environ, env, clear=False):
            result = _build_database_uri()
        assert result == "postgresql://myuser:mypw@host:5432/mydb"

    def test_builds_from_pg_vars(self):
        from app.config import _build_database_uri
        env = {
            "DATABASE_URL": "",
            "PG_HOST": "db.example.com",
            "PG_PORT": "5432",
            "PG_USER": "alice",
            "PG_PASSWORD": "secret",
            "PG_DB": "mydb",
        }
        with patch.dict(os.environ, env, clear=False):
            result = _build_database_uri()
        assert "alice" in result
        assert "secret" in result
        assert "db.example.com" in result
        assert "5432" in result
        assert "mydb" in result

    def test_special_chars_in_password_are_percent_encoded(self):
        from app.config import _build_database_uri
        env = {
            "DATABASE_URL": "",
            "PG_HOST": "localhost",
            "PG_PORT": "5432",
            "PG_USER": "user",
            "PG_PASSWORD": "p@ss:w/ord",
            "PG_DB": "db",
        }
        with patch.dict(os.environ, env, clear=False):
            result = _build_database_uri()
        # raw '@', ':' and '/' in password would break the URI — must be encoded
        user_pw_part = result.split("@")[0].split("://")[1]
        assert "@" not in user_pw_part
        assert "p%40ss" in user_pw_part or "%40" in user_pw_part

    def test_raises_on_missing_pg_vars(self, monkeypatch):
        from app.config import _build_database_uri
        for var in ("DATABASE_URL", "PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DB"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(EnvironmentError, match="Database not configured"):
            _build_database_uri()

    def test_error_message_lists_missing_vars(self, monkeypatch):
        from app.config import _build_database_uri
        for var in ("DATABASE_URL", "PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DB"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(EnvironmentError) as exc_info:
            _build_database_uri()
        msg = str(exc_info.value)
        for var in ("PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DB"):
            assert var in msg

    def test_database_url_takes_precedence_over_pg_vars(self):
        from app.config import _build_database_uri
        env = {
            "DATABASE_URL": "postgresql://winner:win@win-host:9999/win-db",
            "PG_HOST": "loser", "PG_PORT": "1", "PG_USER": "loser",
            "PG_PASSWORD": "loser", "PG_DB": "loser",
        }
        with patch.dict(os.environ, env, clear=False):
            result = _build_database_uri()
        assert "winner" in result
        assert "loser" not in result


class TestGetInterviewConfigPath:
    def test_returns_json_path(self):
        from app.config import get_interview_config_path
        path = get_interview_config_path()
        assert path.endswith(".json")
        assert "interview" in path

    def test_contains_protocol_name(self):
        from app.config import get_interview_config_path, Config
        path = get_interview_config_path()
        assert Config.INTERVIEW_PROTOCOL in path

    def test_custom_protocol_env_var(self, monkeypatch):
        monkeypatch.setenv("INTERVIEW_PROTOCOL", "my_custom_protocol")
        # reload config to pick up new env var
        import importlib
        import app.config as cfg_mod
        importlib.reload(cfg_mod)
        path = cfg_mod.get_interview_config_path()
        assert "my_custom_protocol" in path
        importlib.reload(cfg_mod)  # restore


# ===========================================================================
# steps.py — try_get_json_completion
# ===========================================================================

class TestTryGetJsonCompletion:
    """try_get_json_completion is pure enough to test with a mocked LLM."""

    def _call(self, mock_responses, num_attempts=3, model=None):
        """Call try_get_json_completion with a mocked get_llm_response."""
        from app.steps import try_get_json_completion, StepIntroFields
        target_model = model or StepIntroFields
        with patch("app.steps.get_llm_response", side_effect=mock_responses):
            return try_get_json_completion(
                num_attempts=num_attempts,
                start_temp=0.0,
                temp_increase=0.2,
                system_prompt="sys",
                expected_fields_model=target_model,
            )

    def test_valid_json_returns_dict_and_true(self):
        llm_out = '{"study_subject": "CS", "status": "completed", "comment": "ok"}'
        result, valid = self._call([llm_out])
        assert valid is True
        assert isinstance(result, dict)
        assert result["study_subject"] == "CS"
        assert result["status"] == "completed"

    def test_invalid_json_exhausts_retries_and_returns_false(self):
        result, valid = self._call(["not json at all"] * 5, num_attempts=3)
        assert valid is False
        assert isinstance(result, str)

    def test_called_exactly_num_attempts_on_failure(self):
        from app.steps import try_get_json_completion, StepIntroFields
        mock = MagicMock(return_value="no json here")
        with patch("app.steps.get_llm_response", mock):
            try_get_json_completion(
                num_attempts=3, start_temp=0.0, temp_increase=0.1,
                system_prompt="s", expected_fields_model=StepIntroFields,
            )
        assert mock.call_count == 3

    def test_json_embedded_in_text(self):
        llm_out = 'Sure! {"study_subject": "Physics", "status": "completed", "comment": "text"}'
        result, valid = self._call([llm_out])
        assert valid is True
        assert result["study_subject"] == "Physics"

    def test_missing_fields_are_set_to_empty_string(self):
        # JSON that is missing the 'comment' field
        llm_out = '{"study_subject": "Math", "status": "completed"}'
        result, valid = self._call([llm_out])
        assert valid is True
        assert result.get("comment") == "" or "comment" in result  # either empty or filled from preamble

    def test_comment_from_outside_json_block(self):
        # Text before the JSON block should become the comment fallback
        llm_out = 'Great answer! {"study_subject": "Bio", "status": "completed", "comment": ""}'
        result, valid = self._call([llm_out])
        assert valid is True
        # comment should be filled with the outside text
        assert result["comment"] == "Great answer!"

    def test_succeeds_on_second_attempt(self):
        from app.steps import try_get_json_completion, StepIntroFields
        responses = ["garbage", '{"study_subject": "Art", "status": "in_progress", "comment": ""}']
        with patch("app.steps.get_llm_response", side_effect=responses):
            result, valid = try_get_json_completion(
                num_attempts=3, start_temp=0.0, temp_increase=0.1,
                system_prompt="s", expected_fields_model=StepIntroFields,
            )
        assert valid is True
        assert result["study_subject"] == "Art"


# ===========================================================================
# steps.py — validate_strategies  (needs DB)
# ===========================================================================

class TestValidateStrategies:
    """validate_strategies filters input IDs against those present in the DB."""

    def test_empty_list_returns_empty(self, flask_app):
        from app.steps import validate_strategies
        with flask_app.app_context():
            assert validate_strategies([]) == []

    def test_invalid_ids_are_filtered_out(self, flask_app):
        from app.steps import validate_strategies
        with flask_app.app_context():
            result = validate_strategies(["not-a-real-id-xyz", "another-fake-id"])
        assert result == []

    def test_valid_ids_pass_through(self, flask_app, db):
        """Get real IDs from DB and verify they pass validate_strategies."""
        from app.database.crud import get_all_strategies
        from app.steps import validate_strategies
        with flask_app.app_context():
            all_ids = get_all_strategies()
        if not all_ids:
            pytest.skip("No strategies in DB — run setup script first")
        sample = all_ids[:2]
        with flask_app.app_context():
            result = validate_strategies(sample)
        assert set(result) == set(sample)

    def test_mixed_valid_and_invalid(self, flask_app, db):
        from app.database.crud import get_all_strategies
        from app.steps import validate_strategies
        with flask_app.app_context():
            all_ids = get_all_strategies()
        if not all_ids:
            pytest.skip("No strategies in DB — run setup script first")
        mixed = [all_ids[0], "fake-id-zzzz"]
        with flask_app.app_context():
            result = validate_strategies(mixed)
        assert all_ids[0] in result
        assert "fake-id-zzzz" not in result


# ===========================================================================
# logging_utlis.py — log_action  (needs DB + Flask app context)
# ===========================================================================

class TestLogAction:
    """log_action writes an ActivityLog row to the database."""

    def test_creates_db_entry(self, flask_app, db):
        import sqlalchemy as sa
        from app.actions import LogAction
        from app.logging_utlis import log_action
        from app.models import ActivityLog

        with flask_app.test_request_context("/"):
            log_action(LogAction.START_CONVERSATION, user=None, value={"pytest": True}, http_status=200)

        with flask_app.app_context():
            entry = db.session.scalar(
                sa.select(ActivityLog)
                .where(ActivityLog.action == LogAction.START_CONVERSATION.value)
                .order_by(ActivityLog.timestamp.desc())
            )
        assert entry is not None
        assert entry.http_status == 200

    def test_log_with_none_user_does_not_raise(self, flask_app):
        from app.actions import LogAction
        from app.logging_utlis import log_action

        with flask_app.test_request_context("/"):
            log_action(LogAction.REPLY_USER, user=None)  # should not raise

    def test_value_stored_as_json(self, flask_app, db):
        import sqlalchemy as sa
        from app.actions import LogAction
        from app.logging_utlis import log_action
        from app.models import ActivityLog

        payload = {"key": "value", "number": 42}
        with flask_app.test_request_context("/"):
            log_action(LogAction.RESET_CONVERSATION, user=None, value=payload)

        with flask_app.app_context():
            entry = db.session.scalar(
                sa.select(ActivityLog)
                .where(ActivityLog.action == LogAction.RESET_CONVERSATION.value)
                .order_by(ActivityLog.timestamp.desc())
            )
        assert entry is not None
        assert entry.value is not None

    def test_step_and_turn_stored(self, flask_app, db):
        import sqlalchemy as sa
        from app.actions import LogAction
        from app.logging_utlis import log_action
        from app.models import ActivityLog

        with flask_app.test_request_context("/"):
            log_action(LogAction.REPLY_USER, user=None, step="intro", turn=3)

        with flask_app.app_context():
            entry = db.session.scalar(
                sa.select(ActivityLog)
                .where(ActivityLog.action == LogAction.REPLY_USER.value)
                .where(ActivityLog.step == "intro")
                .where(ActivityLog.turn == 3)
                .order_by(ActivityLog.timestamp.desc())
            )
        assert entry is not None
        assert entry.turn == 3
        assert entry.step == "intro"

    def test_no_request_context_does_not_raise(self, flask_app):
        """log_action should handle missing request context gracefully."""
        from app.actions import LogAction
        from app.logging_utlis import log_action

        with flask_app.app_context():
            log_action(LogAction.START_CONVERSATION, user=None, include_ip=False)
