from fastapi.testclient import TestClient

from novaedit.server.main import app


client = TestClient(app)


def test_edit_success():
    payload = {
        "language": "python",
        "code": "x = 1\nprint(xx)\n",
        "start_line": 1,
        "end_line": 2,
        "diagnostics": ["NameError: name 'xx' is not defined"],
    }
    resp = client.post("/v1/edit", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "edits" in body
    assert body["edits"]


def test_edit_rejects_bad_range():
    payload = {
        "language": "python",
        "code": "x = 1\n",
        "start_line": 3,
        "end_line": 1,
    }
    resp = client.post("/v1/edit", json=payload)
    assert resp.status_code == 400


def test_edit_rejects_unsupported_language():
    payload = {
        "language": "java",
        "code": "public class A {}",
        "start_line": 1,
        "end_line": 1,
    }
    resp = client.post("/v1/edit", json=payload)
    assert resp.status_code == 400


def test_health_includes_backend():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "backend" in body
