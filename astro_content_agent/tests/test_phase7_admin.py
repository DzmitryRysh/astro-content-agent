from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from astro_content_agent.repositories.content_pillars import ContentPillarRepository


# ---------------------------------------------------------------------------
# Brand profile CRUD
# ---------------------------------------------------------------------------


def test_create_brand_profile(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/admin/brand-profile",
        json={
            "name": "Test Astro Brand",
            "description": "A test brand",
            "tone_preset": "warm-grounded",
            "banned_terms": ["guaranteed"],
            "default_hashtags": ["#astro"],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Test Astro Brand"
    assert body["tone_preset"] == "warm-grounded"
    assert "guaranteed" in body["banned_terms"]
    assert body["id"]


def test_list_brand_profiles_empty(client: TestClient) -> None:
    resp = client.get("/api/v1/admin/brand-profile")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_list_brand_profiles_after_create(client: TestClient) -> None:
    client.post("/api/v1/admin/brand-profile", json={"name": "Brand A"})
    client.post("/api/v1/admin/brand-profile", json={"name": "Brand B"})

    resp = client.get("/api/v1/admin/brand-profile")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_get_brand_profile_by_id(client: TestClient) -> None:
    create_resp = client.post("/api/v1/admin/brand-profile", json={"name": "Brand X"})
    bp_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/admin/brand-profile/{bp_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == bp_id


def test_get_brand_profile_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/admin/brand-profile/does-not-exist")
    assert resp.status_code == 404


def test_create_brand_profile_name_required(client: TestClient) -> None:
    resp = client.post("/api/v1/admin/brand-profile", json={"name": ""})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Content pillars
# ---------------------------------------------------------------------------


def test_create_content_pillars(client: TestClient, brand_profile) -> None:
    resp = client.post(
        "/api/v1/admin/content-pillars",
        json={
            "brand_profile_id": brand_profile.id,
            "pillars": [
                {"brand_profile_id": brand_profile.id, "name": "Daily Transit", "description": "Daily guidance"},
                {"brand_profile_id": brand_profile.id, "name": "Mindset", "description": None},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert body["items"][0]["name"] == "Daily Transit"


def test_list_content_pillars(client: TestClient, brand_profile) -> None:
    client.post(
        "/api/v1/admin/content-pillars",
        json={
            "brand_profile_id": brand_profile.id,
            "pillars": [{"brand_profile_id": brand_profile.id, "name": "Pillar 1"}],
        },
    )
    resp = client.get(f"/api/v1/admin/content-pillars?brand_profile_id={brand_profile.id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_content_pillars_reset_flag(client: TestClient, brand_profile, db_session: Session) -> None:
    # Seed initial pillars
    client.post(
        "/api/v1/admin/content-pillars",
        json={
            "brand_profile_id": brand_profile.id,
            "pillars": [
                {"brand_profile_id": brand_profile.id, "name": "Old Pillar"},
            ],
        },
    )
    # Re-seed with reset=True
    resp = client.post(
        "/api/v1/admin/content-pillars",
        json={
            "brand_profile_id": brand_profile.id,
            "reset": True,
            "pillars": [
                {"brand_profile_id": brand_profile.id, "name": "New Pillar A"},
                {"brand_profile_id": brand_profile.id, "name": "New Pillar B"},
            ],
        },
    )
    assert resp.status_code == 201
    # Only new pillars should remain
    repo = ContentPillarRepository()
    all_pillars = repo.list_for_brand(db_session, brand_profile.id)
    names = {p.name for p in all_pillars}
    assert "Old Pillar" not in names
    assert "New Pillar A" in names
    assert "New Pillar B" in names


def test_content_pillars_unknown_brand_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/admin/content-pillars",
        json={
            "brand_profile_id": "missing-brand",
            "pillars": [{"brand_profile_id": "missing-brand", "name": "Pillar"}],
        },
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Seed script logic (unit, no HTTP)
# ---------------------------------------------------------------------------


def test_seed_brand_profile_script_idempotent(db_session: Session) -> None:
    from astro_content_agent.db.models import BrandProfile
    from astro_content_agent.repositories.brand_profiles import BrandProfileRepository

    repo = BrandProfileRepository()
    bp = repo.create(db_session, name="Astro Content Co")
    db_session.commit()
    db_session.refresh(bp)

    # Calling list_all should return exactly one entry
    all_bps = repo.list_all(db_session)
    assert len(all_bps) == 1
    assert all_bps[0].name == "Astro Content Co"


def test_content_pillar_repository_delete_for_brand(db_session: Session, brand_profile) -> None:
    repo = ContentPillarRepository()
    repo.create(db_session, brand_profile_id=brand_profile.id, name="P1")
    repo.create(db_session, brand_profile_id=brand_profile.id, name="P2")
    db_session.commit()

    count = repo.delete_for_brand(db_session, brand_profile.id)
    db_session.commit()

    assert count == 2
    remaining = repo.list_for_brand(db_session, brand_profile.id)
    assert remaining == []
