"""Aspect cat interaction library v0 — story beats for specific planet-cat pairs."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import AspectCatInteraction


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b), key=str.lower))


_RAW_INTERACTIONS: list[AspectCatInteraction] = [
    AspectCatInteraction(
        planet_a="Pluto",
        planet_b="Venus",
        core_tension="Magnetism vs. control: who stirs the pot when desire meets depth (metaphorical shadow, not explicit).",
        constructive_channel="Shared consent to rename the 'spell' as a clear boundary conversation — still cartoon-cute.",
        scene_ideas=[
            "Pluto cat adjusts a small cartoon cauldron while Venus cat's tail shadow pools longer — playful metaphor of influence, not horror.",
            "Venus cat offers a heart-ribbon; Pluto cat counters with a velvet curtain pull — who controls the stage lighting (shadow vs. spotlight).",
            "Two round cats negotiate a single spotlight circle on the floor — push-pull as simple silhouette tug.",
            "Pluto cat slides a chalkboard 'rules' card; Venus cat flips it to 'values' — deadpan stare-off, thick outlines.",
        ],
        compensation_scene_ideas=[
            "They co-stir the cauldron with one spoon each, rhythm sync — teamwork beat, cauldron only as cute prop.",
            "Venus cat ties a bow on Pluto cat's cloak hem; Pluto cat straightens Venus cat's crown — mutual care, no dominance glam.",
        ],
        avoid_list=[
            "explicit horror, gore, occult sigils with readable text, sexual explicitness, fetish imagery",
        ],
    ),
    AspectCatInteraction(
        planet_a="Saturn",
        planet_b="Venus",
        core_tension="Standards vs. softness: cold frame around warm wants.",
        constructive_channel="One extra-soft cushion appears inside a firm outline box — structure serves comfort.",
        scene_ideas=[
            "Saturn cat measures Venus cat's bow with a ruler; Venus cat drapes fabric over the numbers — soft override.",
            "Venus cat tries a twirl; Saturn cat taps a metronome — timing vs. flow as comedy.",
            "Doorway too small: Saturn cat files edges; Venus cat adds a heart-shaped window cutout.",
            "Saturn cat stacks two blocks; Venus cat balances a flower on top — minimal tower.",
        ],
        compensation_scene_ideas=[
            "They build a tiny arch together: Saturn holds base, Venus threads ribbon keystone.",
            "Shared umbrella in star rain: Saturn holds shaft, Venus tilts canopy toward both.",
        ],
        avoid_list=["harsh humiliation, body shame cues, grim authoritarian violence"],
    ),
    AspectCatInteraction(
        planet_a="Mars",
        planet_b="Neptune",
        core_tension="Direct strike vs. dissolve: action meets fog.",
        constructive_channel="Mars aims the foam sword at a fog target; Neptune reveals it was a training dummy — clarity without cruelty.",
        scene_ideas=[
            "Mars cat charges; Neptune cat turns into a cardboard cutout — harmless dodge gag.",
            "Neptune cat sprays gentle mist; Mars cat's steam ears cool into heart puffs.",
            "Tug-of-war with a rope made of clouds — low contrast, readable silhouettes.",
            "Mars cat draws a straight line; Neptune cat wiggles it into a wave — comic physics.",
        ],
        compensation_scene_ideas=[
            "They co-paint a simple compass rose: Mars dots cardinal points, Neptune softens edges.",
            "Neptune offers a shell-phone; Mars uses it to order 'peace treaty pizza' (no brand box art).",
        ],
        avoid_list=["real weapons, blood, combat gore, drug cues"],
    ),
    AspectCatInteraction(
        planet_a="Moon",
        planet_b="Uranus",
        core_tension="Safety vs. surprise: feelings jolted awake.",
        constructive_channel="Moon cat's blanket becomes a parachute; Uranus cat clips it safely — shock with care.",
        scene_ideas=[
            "Uranus cat pops confetti; Moon cat catches pieces in a nightcap — startle then smile.",
            "Moon cat cradles a felt star; Uranus cat swaps it for a cube — gentle absurdity.",
            "Lightning outline frames Moon cat's yawn — not scary, just comic zig-zag.",
            "Moon cat hides under stool; Uranus cat wheels stool away slowly with 'oops' face.",
        ],
        compensation_scene_ideas=[
            "They build a blanket fort with ONE window star cutout — agreed novelty.",
            "Uranus offers mismatched socks; Moon picks the warmer pair — compromise gag.",
        ],
        avoid_list=["panic attack mockery, shaming neurodiversity, cruel pranks"],
    ),
    AspectCatInteraction(
        planet_a="Jupiter",
        planet_b="Mercury",
        core_tension="Big-picture teacher vs. detail analyst: scope mismatch as comedy.",
        constructive_channel="Mercury writes three bullet points on a tiny card; Jupiter enlarges only the kindest one — generous zoom.",
        scene_ideas=[
            "Jupiter cat looms with a huge pointer; Mercury cat balances on the tip like a tightrope — teacher scale vs. analyst poise.",
            "Mercury cat speed-flips flashcards; Jupiter cat catches them all in a graduation cape like a net — playful overwhelm.",
            "Debate at a two-tier chalkboard: Jupiter writes ONE big word; Mercury fills margins with neat ticks.",
            "Mercury offers a flowchart scroll; Jupiter turns it into a paper airplane — perspective joke.",
        ],
        compensation_scene_ideas=[
            "Shared podium: Mercury adjusts mic height; Jupiter adjusts spotlight warmth — co-host beat.",
            "Mercury underlines a footnote; Jupiter frames it with laurel — analyst detail honored by big-picture mentor.",
        ],
        avoid_list=["classroom humiliation, smug elitism, unreadable micro-text in frame"],
    ),
]

ASPECT_CAT_INTERACTIONS: dict[tuple[str, str], AspectCatInteraction] = {
    _pair_key(ix.planet_a, ix.planet_b): ix for ix in _RAW_INTERACTIONS
}


def get_aspect_interaction(planet_a: str, planet_b: str) -> AspectCatInteraction | None:
    """Return library row for the pair (order-insensitive), or None."""
    return ASPECT_CAT_INTERACTIONS.get(_pair_key(planet_a, planet_b))
