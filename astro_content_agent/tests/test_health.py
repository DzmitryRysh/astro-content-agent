def test_health_ok() -> None:
    from astro_content_agent.main import app

    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_ok_versioned_prefix() -> None:
    from astro_content_agent.main import app

    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

