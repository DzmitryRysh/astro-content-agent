"""Catstyle v0 optional character skins / archetypes (Mars, Jupiter, Saturn only — prompt layer)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterSkin:
    skin_key: str
    planet_name: str
    display_name: str
    costume_elements: str
    prop_elements: str
    body_language: str
    scene_hooks: str
    signature_details: str
    avoid_elements: str


_SKINS: dict[tuple[str, str], CharacterSkin] = {
    ("Mars", "spartan_king"): CharacterSkin(
        skin_key="spartan_king",
        planet_name="Mars",
        display_name="Spartan King",
        costume_elements="minimal bronze-lined cape or leather harness strip, hoplite silhouette",
        prop_elements="round shield, spear, optional Mars glyph on shield face",
        body_language="war-cry stance, planted feet, cliff-kick forward energy",
        scene_hooks="cliff edge silhouette, wind dust, dawn rim light",
        signature_details="Mars symbol tattoo on shoulder OR Mars symbol on shield (flat icon, not readable text)",
        avoid_elements="realistic gore, blood, historical hate imagery, legible Greek text",
    ),
    ("Mars", "rambo"): CharacterSkin(
        skin_key="rambo",
        planet_name="Mars",
        display_name="Rambo",
        costume_elements="headband, ammo belts (cartoon blocks), mud streaks",
        prop_elements="toy machine gun silhouette, survival bandolier",
        body_language="survival rage, square shoulders, self-stitching / battlefield survival beat (cartoon stitches only)",
        scene_hooks="jungle silhouette, rain sheet, mud splash",
        signature_details="battle scars as simple ink lines; Mars symbol tattoo on shoulder",
        avoid_elements="realistic gore, readable military patches, photoreal weapons",
    ),
    ("Mars", "gladiator"): CharacterSkin(
        skin_key="gladiator",
        planet_name="Mars",
        display_name="Gladiator",
        costume_elements="minimal arena pads, open chest plate cartoon shape",
        prop_elements="helmet with crest plume, weapon variation (foam trident or short sword)",
        body_language="brutal competitive forward lean, arena stare-down",
        scene_hooks="sand circle floor, gate shadow, crowd as simple silhouettes (no faces)",
        signature_details="bitten ear nick echoes core Mars cat; dust impact puffs",
        avoid_elements="actual violence, broken bones, crowded facial detail",
    ),
    ("Jupiter", "philosopher_mentor"): CharacterSkin(
        skin_key="philosopher_mentor",
        planet_name="Jupiter",
        display_name="Philosopher Mentor",
        costume_elements="draped sage robes, simple stole, seated thinker silhouette",
        prop_elements="scroll (blank), small olive branch, open book with blank pages",
        body_language="open palm teaching gesture, chin rested on paw ponder",
        scene_hooks="star-chart rug pattern (no readable labels), column silhouette",
        signature_details="monocle glint line, laurel hint in outline only",
        avoid_elements="preachy readable quotes, cluttered library shelves, religious icon detail",
    ),
    ("Jupiter", "king_coach"): CharacterSkin(
        skin_key="king_coach",
        planet_name="Jupiter",
        display_name="King Coach",
        costume_elements="tiny crown, sideline jacket drape, whistle on cord",
        prop_elements="clipboard (blank), foam whistle, stadium glow rim",
        body_language="pointing stadium direction, dad-energy encouragement stance",
        scene_hooks="bleacher silhouette, spotlight oval, confetti as flat shapes",
        signature_details="big cheek laugh held readable at small size",
        avoid_elements="readable scoreboard numbers, brand logos, mascot IP",
    ),
    ("Saturn", "pinstripe_boss"): CharacterSkin(
        skin_key="pinstripe_boss",
        planet_name="Saturn",
        display_name="Pinstripe Boss",
        costume_elements="sharper pinstripe suit read, wide-brim hat tilt, ring-hoop belt accent",
        prop_elements="heavier briefcase silhouette, blank-dial wristwatch, skeleton key cartoon",
        body_language="boardroom patience stare, slow folder snap",
        scene_hooks="glass tower silhouette, ticking clock motif (no numerals), elevator floor line",
        signature_details="ring silhouette echo; graphite edge light on hat brim",
        avoid_elements="readable contracts, micro spreadsheet text, grim reaper tropes",
    ),
    ("Saturn", "old_money_architect"): CharacterSkin(
        skin_key="old_money_architect",
        planet_name="Saturn",
        display_name="Old-Money Architect",
        costume_elements="tailored chalk-stripe suit, cuff links as flat dots, silent appraisal posture",
        prop_elements="drafting triangle, T-square, thin scale ruler",
        body_language="measured nod, arms folded with one paw holding triangle",
        scene_hooks="marble foyer steps (minimal), blueprint scroll (blank), portico shadow",
        signature_details="ring belt hoop; cold bronze rim light on cheek",
        avoid_elements="readable blueprints, luxury brand marks, baroque clutter",
    ),
}

_CANONICAL_PLANET = {"mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn"}


def normalize_skin_key(skin_key: str) -> str:
    return (skin_key or "").strip().lower().replace("-", "_")


def _canonical_planet_for_skins(name: str) -> str:
    key = (name or "").strip().lower()
    if key not in _CANONICAL_PLANET:
        raise ValueError(
            f"Character skins v0 only support Mars, Jupiter, Saturn (got {name!r}). "
            f"Known planets for skins: {', '.join(sorted(_CANONICAL_PLANET.values()))}."
        )
    return _CANONICAL_PLANET[key]


def list_character_skins(planet_name: str) -> list[str]:
    """Return sorted skin_key strings registered for ``planet_name``."""
    planet = _canonical_planet_for_skins(planet_name)
    keys = [sk for (p, sk) in _SKINS if p == planet]
    return sorted(keys)


def get_character_skin(planet_name: str, skin_key: str) -> CharacterSkin:
    """
    Resolve a skin for a planet. ``planet_name`` and ``skin_key`` are normalized robustly.

    Raises:
        ValueError: unknown planet for v0 skins, unknown skin, or skin/planet mismatch.
    """
    planet = _canonical_planet_for_skins(planet_name)
    sk = normalize_skin_key(skin_key)
    if not sk:
        raise ValueError("skin_key must be non-empty.")
    skin = _SKINS.get((planet, sk))
    if skin is None:
        available = ", ".join(list_character_skins(planet)) or "(none)"
        raise ValueError(
            f"No character skin {sk!r} for {planet}. Available for this planet: {available}."
        )
    return skin


__all__ = [
    "CharacterSkin",
    "get_character_skin",
    "list_character_skins",
    "normalize_skin_key",
]
