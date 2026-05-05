"""Deterministic premium comic art-direction for Catstyle image prompts (no LLM)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from astro_content_agent.content.catstyle.character_skins_v0 import get_character_skin
from astro_content_agent.content.catstyle.models import CatstylePromptPack

CatstyleArtEnergy = Literal["charged", "supportive", "balanced"]

_PREMIUM_HEADER = "Premium comic direction (deterministic v0):"


def resolve_art_energy(editorial_profile: str | None, mode: str) -> CatstyleArtEnergy:
    """
    Map editorial + mode to art-direction energy.

    Editorial wins when set to charged/supportive; otherwise mode biases tension/compensation.
    """
    ep = (editorial_profile or "").strip().lower()
    if ep == "charged":
        return "charged"
    if ep == "supportive":
        return "supportive"
    m = (mode or "").strip().lower()
    if m == "tension":
        return "charged"
    if m == "compensation":
        return "supportive"
    return "balanced"


@dataclass(frozen=True)
class CatstyleArtDirectionProfile:
    """Inputs for deterministic prompt enrichment (v0)."""

    energy: CatstyleArtEnergy
    planet_a: str
    planet_b: str
    mode: str
    editorial_profile: str | None
    skin_a: str | None
    skin_b: str | None

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "version": "catstyle-art-direction-v0",
            "energy": self.energy,
            "editorial_profile": self.editorial_profile,
            "mode": self.mode,
            "planet_a": self.planet_a,
            "planet_b": self.planet_b,
            "skin_a": self.skin_a,
            "skin_b": self.skin_b,
        }


def build_catstyle_art_direction_profile(
    *,
    editorial_profile: str | None,
    mode: str,
    planet_a: str,
    planet_b: str,
    skin_a: str | None,
    skin_b: str | None,
) -> CatstyleArtDirectionProfile:
    raw_ep = (editorial_profile or "").strip().lower()
    ep_norm = raw_ep if raw_ep in ("charged", "balanced", "supportive") else None
    return CatstyleArtDirectionProfile(
        energy=resolve_art_energy(editorial_profile, mode),
        planet_a=planet_a,
        planet_b=planet_b,
        mode=(mode or "").strip().lower(),
        editorial_profile=ep_norm,
        skin_a=skin_a,
        skin_b=skin_b,
    )


def composition_line() -> str:
    return (
        "Cinematic comic-panel composition with poster-like clarity: strong silhouette readability, "
        "decisive foreground/background separation, one focal action readable at thumbnail size. "
        "Not a flat mascot pose, not a centered sticker-like character floating in empty space—"
        "stage the beat like a premium comic panel or movie one-sheet while staying cartony flat-color Catstyle "
        "(never photoreal, never glossy prestige portrait). "
        "Keep each planet's [IDENTITY MARKERS v1] symbol/prop stamps readable at thumbnail scale beside faces/bodies."
    )


def scene_intensity_line(energy: CatstyleArtEnergy) -> str:
    if energy == "charged":
        return (
            "Scene energy (charged): dynamic action read, impact moment, conflict staging, expressive motion, "
            "meme/movie-archetype hook—two bodies clearly interacting with readable cause/effect."
        )
    if energy == "supportive":
        return (
            "Scene energy (supportive): elegant collaboration—calmer but deliberately composed; complementary gestures "
            "and shared staging; still premium comic clarity, never a bland neutral mascot tableau."
        )
    return (
        "Scene energy (balanced): readable staged interaction with clear depth planes; avoid low-energy neutral "
        "posing and empty dead space behind the characters."
    )


def visual_gag_line(energy: CatstyleArtEnergy) -> str:
    if energy == "charged":
        return (
            "Visual timing: push silhouette-first comedy and contrast (slow vs fast, big vs small); "
            "readable antagonist/protagonist frame inspired by trailer/memetic beats—without copying specific IP."
        )
    if energy == "supportive":
        return (
            "Visual timing: cooperative micro-beat—props and poses echo partnership and constructive rhythm, "
            "not chaotic slapstick or random clutter."
        )
    return (
        "Visual timing: one crisp readable gag beat; avoid random clutter, nursery-soft diffusion, or generic "
        "stock cartoon staging."
    )


def skin_emphasis_block(
    planet_a: str,
    planet_b: str,
    skin_a: str | None,
    skin_b: str | None,
) -> str:
    if not skin_a and not skin_b:
        return ""
    lines: list[str] = [
        "Character skin mandate: named skins are scene-defining overlays—not optional decoration. "
        "Let each skin's props, body language, and library scene hooks steer setting, pose, and prop staging "
        "(the planet-cat bible identity stays primary).",
    ]
    pa = planet_a.strip()
    pb = planet_b.strip()
    if skin_a:
        sk = get_character_skin(pa, skin_a)
        lines.append(
            f"{pa} ({sk.display_name}): prioritize staging from hooks—{sk.scene_hooks}. "
            f"Accent body language: {sk.body_language}. Signature props: {sk.prop_elements}."
        )
    if skin_b:
        sk = get_character_skin(pb, skin_b)
        lines.append(
            f"{pb} ({sk.display_name}): prioritize staging from hooks—{sk.scene_hooks}. "
            f"Accent body language: {sk.body_language}. Signature props: {sk.prop_elements}."
        )
    return " ".join(lines)


def compose_premium_catstyle_prompt(base_image_prompt: str, profile: CatstyleArtDirectionProfile) -> str:
    chunks = [
        composition_line(),
        scene_intensity_line(profile.energy),
        visual_gag_line(profile.energy),
    ]
    skin = skin_emphasis_block(profile.planet_a, profile.planet_b, profile.skin_a, profile.skin_b)
    if skin:
        chunks.append(skin)
    premium = " ".join(chunks)
    return f"{base_image_prompt.strip()}\n\n{_PREMIUM_HEADER} {premium}"


def strengthen_negative_prompt(base_negative: str, profile: CatstyleArtDirectionProfile) -> str:
    universal = [
        "bland mascot pose",
        "sticker-like centered character floating in empty space",
        "empty background with no staging or depth",
        "low-energy neutral stand",
        "random prop clutter without story purpose",
        "generic nursery-cartoon softness",
        "weak unclear interaction between the two planet-cats",
    ]
    extra: list[str] = []
    if profile.energy == "charged":
        extra.extend(
            [
                "overly soft babyish vibe when conflict is readable",
                "symmetrical dull posing",
                "both cats disconnected like separate stickers",
            ]
        )
    elif profile.energy == "supportive":
        extra.extend(
            [
                "grim slapstick gore beats",
                "chaotic overcrowding that kills readability",
            ]
        )
    else:
        extra.append("poster-like energy collapses into flat icon poses")

    chunks = [base_negative.strip().rstrip(",").strip(), *universal, *extra]
    return ", ".join(c for c in chunks if c)


def enrich_animation_prompt(base_animation: str, profile: CatstyleArtDirectionProfile) -> str:
    if profile.energy == "charged":
        motion = (
            "Motion direction: readable squash/stretch on the focal interaction; comic timing beat hits mid-loop; "
            "silhouettes stay crisp—avoid mushy drift."
        )
    elif profile.energy == "supportive":
        motion = (
            "Motion direction: cooperative rhythm—paired gestures echo collaboration; keep outlines crisp and staging "
            "legible at reel size."
        )
    else:
        motion = (
            "Motion direction: one primary motion read per loop; silhouettes and staging stay readable; "
            "avoid floaty idle sway."
        )
    return f"{base_animation.strip()}\n\n{motion}"


def enrich_carousel_idea(base_carousel: str, profile: CatstyleArtDirectionProfile) -> str:
    if profile.energy == "charged":
        tail = (
            " Carousel staging: vary angles like sequential comic panels—each slide keeps poster/panel energy "
            "without on-image text."
        )
    elif profile.energy == "supportive":
        tail = (
            " Carousel staging: composed variations that reinforce partnership beats—still premium comic clarity, "
            "no bland repetition."
        )
    else:
        tail = " Carousel staging: treat slides as panel iterations with consistent depth and focal hierarchy."
    return f"{base_carousel.strip()}{tail}"


def apply_art_direction_to_prompt_pack(pack: CatstylePromptPack, profile: CatstyleArtDirectionProfile) -> CatstylePromptPack:
    meta = profile.to_metadata_dict()
    return CatstylePromptPack(
        image_prompts=[compose_premium_catstyle_prompt(p, profile) for p in pack.image_prompts],
        animation_prompt=enrich_animation_prompt(pack.animation_prompt, profile),
        negative_prompt=strengthen_negative_prompt(pack.negative_prompt, profile),
        carousel_idea=enrich_carousel_idea(pack.carousel_idea, profile),
        art_direction_profile=meta,
    )


build_catstyle_art_direction = build_catstyle_art_direction_profile


__all__ = [
    "CatstyleArtDirectionProfile",
    "CatstyleArtEnergy",
    "apply_art_direction_to_prompt_pack",
    "build_catstyle_art_direction",
    "build_catstyle_art_direction_profile",
    "compose_premium_catstyle_prompt",
    "composition_line",
    "enrich_animation_prompt",
    "enrich_carousel_idea",
    "resolve_art_energy",
    "scene_intensity_line",
    "skin_emphasis_block",
    "strengthen_negative_prompt",
    "visual_gag_line",
]
