from __future__ import annotations

from datetime import date

from astro_content_agent.astro.engine import AstroEngineV0, EngineInput


def test_engine_deterministic_by_brand_and_day() -> None:
    engine = AstroEngineV0()
    day = date(2026, 4, 3)

    a1 = engine.generate_day(EngineInput(brand_profile_id="brand-a", day=day)).model_dump(mode="json")
    a2 = engine.generate_day(EngineInput(brand_profile_id="brand-a", day=day)).model_dump(mode="json")
    b1 = engine.generate_day(EngineInput(brand_profile_id="brand-b", day=day)).model_dump(mode="json")

    assert a1["signals"] == a2["signals"]
    assert a1["signals"] != b1["signals"]


def test_engine_payload_shape() -> None:
    engine = AstroEngineV0()
    payload = engine.generate_day(EngineInput(brand_profile_id="brand-a", day=date(2026, 4, 3)))

    assert payload.engine_version == "v0.stub"
    assert payload.day == date(2026, 4, 3)
    assert 3 <= len(payload.signals) <= 5
    for s in payload.signals:
        assert s.key
        assert s.headline
        assert 0.0 <= s.intensity <= 1.0

