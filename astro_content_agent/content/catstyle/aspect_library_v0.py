"""Aspect cat interaction library v0 — story beats for specific planet-cat pairs."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import AspectCatInteraction


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b), key=str.lower))


_RAW_INTERACTIONS: list[AspectCatInteraction] = [
    AspectCatInteraction(
        planet_a="Pluto",
        planet_b="Venus",
        core_tension="Hypnotic pull vs. overwhelmed desire: depth tries to steer beauty; Venus feels trapped in the spell's metaphor (consent subtext via cartoon beats).",
        constructive_channel="Rename the trance as a boundary talk — two spoons, dimmed spiral eyes, mutual exhale at the cauldron rim.",
        scene_ideas=[
            "Pluto cat stirs a black cartoon cauldron while Venus cat is half-submerged in bubbling purple potion — overwhelmed expression, not spa-happy; absurd comic tension only.",
            "Pluto cat's flat shadow ring and soft tendrils tug Venus cat into a tight orbit — puppetry metaphor, no ropes on limbs, readable silhouette tug-of-war.",
            "Pluto cat locks spiral-hypnotic eyes; Venus cat looks dazed and unable to step back — mesmerized beat, thick outlines, deadpan comedy.",
            "Pluto cat as playful puppet-master with shadow-string silhouettes only; Venus cat looks emotionally caught mid-step — metaphorical strings, not bondage imagery.",
        ],
        compensation_scene_ideas=[
            "They negotiate at the cauldron rim with two spoons each — consent rhythm, bubbles stay cute and non-graphic.",
            "Venus cat sets one rose on the rim; Pluto cat softens spiral pupils into plain dots — relief gag, still tense-funny.",
        ],
        avoid_list=[
            "explicit horror, gore, occult sigils with readable text, sexual explicitness, fetish imagery, joyful spa Venus glam, romantic syrup sweetness",
        ],
    ),
    AspectCatInteraction(
        planet_a="Saturn",
        planet_b="Venus",
        core_tension="Pleasure under audit: Saturn frames beauty, fashion, and want like a deadline-heavy business meeting.",
        constructive_channel="Design studio collaboration — architecture models, fashion sketches, jewelry or watch layout as teamwork, minimal luxury clutter.",
        scene_ideas=[
            "Saturn cat in pinstripe and hat slides a blank contract across a tiny desk; Venus cat with single rose and moodboard swatches looks boxed-in — comedy meeting.",
            "Saturn cat checks a visible wristwatch while Venus cat holds fabric bolt and mannequin outline — beauty waiting on Saturn's clock.",
            "Their ring silhouettes overlap like a stamped seal trap — paperwork aura, not horror, just absurd obligation.",
            "Saturn cat clipboard tallies 'pleasure units' as a joke meter; Venus cat clutches one pearl strand and mirror back — aesthetic vs audit.",
        ],
        compensation_scene_ideas=[
            "Shared design studio: flat fabric swatches, tiny architecture model, Venus pins one accent gem while Saturn steadies ruler; they swap stylish blank business cards and co-sketch a watch face — no logos.",
            "Joint jewelry layout on mat (Saturn measures band, Venus picks one stone) beside a real-estate tabletop shopfront model — Saturn frames structure, Venus picks window dress; build-together metaphor.",
        ],
        avoid_list=[
            "harsh humiliation, body shame cues, grim authoritarian violence, overcrowded bling, glossy runway excess",
        ],
    ),
    AspectCatInteraction(
        planet_a="Mars",
        planet_b="Neptune",
        core_tension="Fire vs fog: direct Mars heat collides with Neptune's dissolve; steam, waves, and blank absorption as absurd comedy.",
        constructive_channel="They aim the foam sword at a fog training dummy; steam clears enough to see the joke — clarity without cruelty.",
        scene_ideas=[
            "Mars cat charges with bandana and flame tuft; Neptune cat floats inside a wall of fog that blocks the lane — Mars bonks harmless cotton fog.",
            "Mars cat lobbing a cartoon fireball meets Neptune's wave splash — huge comic steam cloud hides both, then two peek out surprised.",
            "Neptune cat blankly lets Mars cat's direct shove pass through like mist — fish-bubble motif wobbles beside Neptune's cheek.",
            "Shared cauldron beat: Mars adds spark, Neptune adds mist puff — collaborative steam chemistry, silly not scary.",
        ],
        compensation_scene_ideas=[
            "They co-paint a compass rose on a star map: Mars dots cardinal ticks, Neptune adds two fish silhouettes in the margin.",
            "Neptune offers shell-phone; Mars orders 'peace treaty pizza' — steam from box, no brand art.",
        ],
        avoid_list=["real weapons, blood, combat gore, drug cues"],
    ),
    AspectCatInteraction(
        planet_a="Moon",
        planet_b="Uranus",
        core_tension="Comfort vs chaos: Uranus bursts through novelty; Moon wants pillow, blanket pled, and predictable cozy orbit.",
        constructive_channel="Moon's blanket becomes a parachute clipped safe by Uranus — shock with care, weird gadget solves mood.",
        scene_ideas=[
            "Uranus cat bursts from an electric portal hoop with rock-and-roll pose; Moon cat on a cloud couch jolts awake clutching pillow and blanket pled.",
            "Moon cat slumped with pillow + blanket pled, grumpy eyebrows; Uranus cat lands with devil-horns paw gesture — Moon looks theatrically offended, absurd not cruel.",
            "Lightning zig slices through Moon cat's emotional fog cloud — Moon hugs blanket tighter; Uranus shrugs 'oops' sparkle.",
            "Emotional tide-wave silhouette meets electric zig-zag bolt — silhouettes bonk like cartoons, thick outlines held crisp.",
        ],
        compensation_scene_ideas=[
            "Weird mood machine: Uranus twists chaos knob while Moon adjusts cozy thermostat on blanket cape; rhythm gag with lightning metronome vs pillow rock.",
            "Uranus unveils plush portal pillow comfort gadget; Moon skeptically tries it — soft punchline, caring not cruel.",
        ],
        avoid_list=["panic attack mockery, shaming neurodiversity, cruel pranks, mean-spirited humiliation"],
    ),
    AspectCatInteraction(
        planet_a="Jupiter",
        planet_b="Mercury",
        core_tension="Big-picture teacher vs. detail analyst: scope mismatch as comedy.",
        constructive_channel="Mercury writes three precise points on a star-map card; Jupiter enlarges only the kindest constellation meaning — generous zoom.",
        scene_ideas=[
            "Jupiter cat sage-scarf lecture at podium; Mercury cat interrupts with checklist notepad and pencil taps — deadpan classroom absurdity.",
            "Tug-of-war over a star map scroll: Jupiter yanks toward wild adventure arrow; Mercury yanks toward footnote corner — rope goes slack as joke.",
            "Mercury cat chalks tiny corrections under Jupiter cat's one giant chalk word — teacher vs analyst staredown.",
            "Travel planning gag: Jupiter points at horizon sticker; Mercury counts steps on tiny abacus — logistics vs wanderlust.",
        ],
        compensation_scene_ideas=[
            "Mercury plots three exact stars; Jupiter circles just one generous constellation outline — shared atlas harmony; co-teaching with laurel magnifier framing Mercury's bullets.",
            "Shared classroom desk: Jupiter's open blank book beside Mercury's annotated sticky stack — cooperation silhouette.",
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
