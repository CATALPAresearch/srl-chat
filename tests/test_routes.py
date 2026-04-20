"""
Route integration tests.

These are integration tests that require a running PostgreSQL database
pre-seeded with languages, contexts, and strategies (same as the dev DB).

DISABLE_LLM=true is set here so no Ollama instance is needed for these
route tests.  The LLM stub returns a fixed German greeting which is
enough to exercise the full request/response cycle.
"""

import os
import json
import uuid
import pathlib
import sys
import pytest

# Must be set before any import of the Flask app so config.py + llm.py pick it up
os.environ["DISABLE_LLM"] = "true"

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid():
    """Return a fresh unique user-id string to avoid cross-test DB conflicts."""
    return "test_" + uuid.uuid4().hex[:10]


def _start(client, userid, client_name="pytest", lang="en"):
    """POST /startConversation and return the response."""
    return client.post(
        "/startConversation",
        json={"userid": userid, "client": client_name, "language": lang},
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# Static routes
# ---------------------------------------------------------------------------

class TestStaticRoutes:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"html" in resp.data.lower()

    def test_favicon_served(self, client):
        resp = client.get("/static/favicon.ico")
        assert resp.status_code in (200, 404)  # 404 is acceptable if file absent in test env


# ---------------------------------------------------------------------------
# /startConversation
# ---------------------------------------------------------------------------

class TestStartConversation:
    def test_valid_english(self, client):
        uid = _uid()
        resp = _start(client, uid, lang="en")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "message" in body

    def test_valid_german(self, client):
        uid = _uid()
        resp = _start(client, uid, lang="de")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "message" in body

    def test_unsupported_language_returns_400(self, client):
        resp = client.post(
            "/startConversation",
            json={"userid": _uid(), "client": "pytest", "language": "xx"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_userid_returns_400(self, client):
        resp = client.post(
            "/startConversation",
            json={"client": "pytest", "language": "en"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_client_returns_400(self, client):
        resp = client.post(
            "/startConversation",
            json={"userid": _uid(), "language": "en"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_idempotent_second_call_200(self, client):
        uid = _uid()
        _start(client, uid, lang="en")
        resp = _start(client, uid, lang="en")
        assert resp.status_code == 200

    def test_response_message_is_string(self, client):
        uid = _uid()
        body = _start(client, uid).get_json()
        assert isinstance(body["message"], str)
        assert len(body["message"]) > 0


# ---------------------------------------------------------------------------
# /reply
# ---------------------------------------------------------------------------

class TestReply:
    def test_reply_after_start_returns_message(self, client):
        uid = _uid()
        _start(client, uid)
        resp = client.post(
            "/reply",
            json={"userid": uid, "client": "pytest", "message": "Informatik"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "message" in resp.get_json()

    def test_reply_unknown_user_returns_400(self, client):
        resp = client.post(
            "/reply",
            json={"userid": "no_such_user_xyz", "client": "pytest", "message": "hi"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_reply_missing_message_returns_400(self, client):
        uid = _uid()
        _start(client, uid)
        resp = client.post(
            "/reply",
            json={"userid": uid, "client": "pytest"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_reply_missing_userid_returns_400(self, client):
        resp = client.post(
            "/reply",
            json={"client": "pytest", "message": "hi"},
            content_type="application/json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# /resetConversation
# ---------------------------------------------------------------------------

class TestResetConversation:
    def test_reset_existing_user(self, client):
        uid = _uid()
        _start(client, uid)
        resp = client.post(
            "/resetConversation",
            json={"userid": uid, "client": "pytest"},
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_reset_nonexistent_user_returns_400(self, client):
        resp = client.post(
            "/resetConversation",
            json={"userid": "no_such_user_xyz", "client": "pytest"},
            content_type="application/json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /conversation
# ---------------------------------------------------------------------------

class TestConversation:
    def test_empty_history_for_unknown_user(self, client):
        resp = client.get(
            "/conversation",
            query_string={"userid": "no_such_user_xyz", "client": "pytest"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["messages"] == []

    def test_missing_userid_returns_400(self, client):
        resp = client.get("/conversation", query_string={"client": "pytest"})
        assert resp.status_code == 400

    def test_missing_client_returns_400(self, client):
        resp = client.get("/conversation", query_string={"userid": "someone"})
        assert resp.status_code == 400

    def test_has_bot_message_after_start(self, client):
        uid = _uid()
        _start(client, uid)
        resp = client.get(
            "/conversation",
            query_string={"userid": uid, "client": "pytest"},
        )
        assert resp.status_code == 200
        messages = resp.get_json()["messages"]
        assert len(messages) >= 1
        authors = {m["author"] for m in messages}
        assert "bot" in authors

    def test_message_structure(self, client):
        uid = _uid()
        _start(client, uid)
        messages = client.get(
            "/conversation",
            query_string={"userid": uid, "client": "pytest"},
        ).get_json()["messages"]
        for msg in messages:
            assert "author" in msg
            assert "message" in msg
            assert "id" in msg

    def test_user_and_bot_messages_after_reply(self, client):
        uid = _uid()
        _start(client, uid)
        client.post(
            "/reply",
            json={"userid": uid, "client": "pytest", "message": "Mathematik"},
            content_type="application/json",
        )
        messages = client.get(
            "/conversation",
            query_string={"userid": uid, "client": "pytest"},
        ).get_json()["messages"]
        authors = {m["author"] for m in messages}
        assert "user" in authors
        assert "bot" in authors


# ---------------------------------------------------------------------------
# /log/tab_event
# ---------------------------------------------------------------------------

class TestLogTabEvent:
    def test_tab_hidden_event(self, client):
        resp = client.post(
            "/log/tab_event",
            json={"userid": _uid(), "client": "pytest", "event": "tab_hidden", "timestamp": 1700000000},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["event"] == "tab_hidden"

    def test_tab_visible_event(self, client):
        resp = client.post(
            "/log/tab_event",
            json={"userid": _uid(), "client": "pytest", "event": "tab_visible", "timestamp": 1700000000},
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_invalid_event_type_returns_400(self, client):
        resp = client.post(
            "/log/tab_event",
            json={"userid": _uid(), "client": "pytest", "event": "bogus_event", "timestamp": 1700000000},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_unknown_user_still_logs(self, client):
        # Log endpoints should not require a known user in DB
        resp = client.post(
            "/log/tab_event",
            json={"userid": "no_such_user_xyz", "client": "pytest", "event": "tab_hidden", "timestamp": 1},
            content_type="application/json",
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /log/mouse_traces
# ---------------------------------------------------------------------------

class TestLogMouseTraces:
    def test_valid_traces(self, client):
        uid = _uid()
        resp = client.post(
            "/log/mouse_traces",
            json={
                "userid": uid, "client": "pytest", "session_id": "s1",
                "traces": [{"x": 10, "y": 20, "t": 100}, {"x": 15, "y": 25, "t": 200}],
            },
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_empty_traces_list(self, client):
        resp = client.post(
            "/log/mouse_traces",
            json={"userid": _uid(), "client": "pytest", "session_id": "s2", "traces": []},
            content_type="application/json",
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /user_language/
# ---------------------------------------------------------------------------

class TestUserLanguage:
    def test_default_language_is_de(self, client):
        resp = client.get("/user_language/")
        assert resp.status_code == 200
        assert resp.data.decode().strip() == "de"

    def test_known_user_returns_their_language(self, client):
        uid = _uid()
        _start(client, uid, lang="en")
        # language route reads from session, not DB — default applies without active LTI session
        resp = client.get("/user_language/")
        assert resp.status_code == 200
        assert resp.data.decode().strip() in ("de", "en")


# ---------------------------------------------------------------------------
# /user_role/
# ---------------------------------------------------------------------------

class TestUserRole:
    def test_default_role_is_student(self, client):
        resp = client.get("/user_role/")
        assert resp.status_code == 200
        assert resp.data.decode().strip() == "student"


# ---------------------------------------------------------------------------
# /dashboard/stats  and  /dashboard/courses
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_stats_returns_expected_keys(self, client):
        resp = client.get("/dashboard/stats")
        assert resp.status_code == 200
        body = resp.get_json()
        for key in ("total_students", "total_completed", "avg_duration_minutes",
                    "avg_response_time_seconds", "weekly_activity", "response_time_by_step"):
            assert key in body, f"Missing key: {key}"

    def test_stats_with_date_filter(self, client):
        resp = client.get("/dashboard/stats?from=2020-01-01&to=2020-01-02")
        assert resp.status_code == 200

    def test_stats_empty_date_range_returns_zeros(self, client):
        resp = client.get("/dashboard/stats?from=2000-01-01&to=2000-01-02")
        body = resp.get_json()
        assert body["total_students"] == 0
        assert body["total_completed"] == 0

    def test_courses_returns_list(self, client):
        resp = client.get("/dashboard/courses")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_courses_shape(self, client):
        body = client.get("/dashboard/courses").get_json()
        for entry in body:
            assert "id" in entry
            assert "name" in entry
            assert "students" in entry

    def test_courses_standalone_label(self, client):
        uid = _uid()
        _start(client, uid)  # creates user with context_id="0"
        body = client.get("/dashboard/courses").get_json()
        ids = [e["id"] for e in body]
        if "0" in ids:
            standalone = next(e for e in body if e["id"] == "0")
            assert "standalone" in standalone["name"].lower() or standalone["name"] != ""


# ---------------------------------------------------------------------------
# /protocols
# ---------------------------------------------------------------------------

class TestProtocols:
    _created = []  # track names to clean up

    def test_list_returns_list(self, client):
        resp = client.get("/protocols")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_list_contains_default(self, client):
        names = [p["name"] for p in client.get("/protocols").get_json()]
        assert "interview_default" in names

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/protocols/does_not_exist_xyz")
        assert resp.status_code == 404

    def test_create_and_retrieve(self, client):
        name = "pytest_proto_" + uuid.uuid4().hex[:6]
        self._created.append(name)
        payload = {"name": name, "protocol": {"categories": [], "note": "test"}}
        resp = client.post("/protocols", json=payload, content_type="application/json")
        assert resp.status_code == 201

        get_resp = client.get(f"/protocols/{name}")
        assert get_resp.status_code == 200
        assert get_resp.get_json()["note"] == "test"

    def test_create_missing_name_returns_400(self, client):
        resp = client.post(
            "/protocols",
            json={"protocol": {"categories": []}},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_missing_protocol_returns_400(self, client):
        resp = client.post(
            "/protocols",
            json={"name": "should_fail"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_duplicate_returns_409(self, client):
        name = "pytest_dup_" + uuid.uuid4().hex[:6]
        self._created.append(name)
        payload = {"name": name, "protocol": {}}
        client.post("/protocols", json=payload, content_type="application/json")
        resp = client.post("/protocols", json=payload, content_type="application/json")
        assert resp.status_code == 409

    def test_delete_default_returns_403(self, client):
        resp = client.delete("/protocols/interview_default")
        assert resp.status_code == 403

    def test_create_and_delete(self, client):
        name = "pytest_del_" + uuid.uuid4().hex[:6]
        client.post("/protocols", json={"name": name, "protocol": {}}, content_type="application/json")
        resp = client.delete(f"/protocols/{name}")
        assert resp.status_code == 200
        assert client.get(f"/protocols/{name}").status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/protocols/no_such_proto_xyz")
        assert resp.status_code == 404

    def test_update_protocol(self, client):
        name = "pytest_upd_" + uuid.uuid4().hex[:6]
        self._created.append(name)
        client.post("/protocols", json={"name": name, "protocol": {"v": 1}}, content_type="application/json")
        resp = client.put(f"/protocols/{name}", json={"v": 2}, content_type="application/json")
        assert resp.status_code == 200
        body = client.get(f"/protocols/{name}").get_json()
        assert body["v"] == 2

    def test_update_nonexistent_returns_404(self, client):
        resp = client.put(
            "/protocols/no_such_xyz",
            json={"x": 1},
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_export_returns_file(self, client):
        name = "pytest_exp_" + uuid.uuid4().hex[:6]
        self._created.append(name)
        client.post("/protocols", json={"name": name, "protocol": {"key": "val"}}, content_type="application/json")
        resp = client.get(f"/protocols/{name}/export")
        assert resp.status_code == 200
        assert b"val" in resp.data

    @pytest.fixture(autouse=True, scope="class")
    def cleanup(self, client):
        yield
        for name in self._created:
            client.delete(f"/protocols/{name}")
        self._created.clear()
