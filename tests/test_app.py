from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.text == "ok"


def test_visualize_bad_input():
    r = client.post("/api/visualize", data={"turtle": "this is not turtle"})
    assert r.status_code == 400
    assert "Parse error" in r.json()["detail"]


def test_visualize_ok():
    ttl = "@prefix ex: <http://example.org/> . ex:a ex:b ex:c ."
    r = client.post("/api/visualize", data={"turtle": ttl})
    assert r.status_code == 200
    assert "<html" in r.text.lower()
    assert "vis-network" in r.text
