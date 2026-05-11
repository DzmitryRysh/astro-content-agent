"""Catstyle v0 — 25 social/outer-to-personal transit pair seed map (deterministic text only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

Mode = Literal["tension", "compensation", "mixed", "flow"]

OUTER_PLANETS: Final[frozenset[str]] = frozenset({"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"})
PERSONAL_PLANETS: Final[frozenset[str]] = frozenset({"Sun", "Moon", "Mercury", "Venus", "Mars"})


@dataclass(frozen=True)
class CatstyleTransitPairSeed:
    outer_planet: str
    personal_planet: str
    core_tension: str
    visual_metaphor: str
    constructive_channel: str
    suggested_scene_angles: tuple[str, ...]
    avoid: tuple[str, ...]
    base_mode: Mode = "mixed"


def _s(*lines: str) -> tuple[str, ...]:
    return tuple(lines)


def _a(*items: str) -> tuple[str, ...]:
    return tuple(items)


_TRANSIT_PAIR_SEEDS: dict[tuple[str, str], CatstyleTransitPairSeed] = {
    ("Jupiter", "Sun"): CatstyleTransitPairSeed(
        outer_planet="Jupiter",
        personal_planet="Sun",
        core_tension="Identity expands into big meaning; confidence can inflate like a parade balloon.",
        visual_metaphor="Jupiter puts a giant spotlight or comic crown on Sun cat until the little stage bends.",
        constructive_channel="Leadership with wisdom, generosity, healthy visibility—big stage, kind intent.",
        suggested_scene_angles=_s(
            "Jupiter inflates Sun’s tiny crown into a huge foam crown—Sun wobbles but grins.",
            "Sun cat stands on a podium while Jupiter opens a giant blank book of purpose behind them.",
            "Jupiter launches Sun into a constellation-shaped stage outline—flat star cutouts only.",
            "Sun’s corona halo gets a Jupiter-sized laurel frame—comedy scale mismatch.",
        ),
        avoid=_a("smug elitism", "empty guru cliché", "unreadable micro-text on props"),
        base_mode="mixed",
    ),
    ("Jupiter", "Moon"): CatstyleTransitPairSeed(
        outer_planet="Jupiter",
        personal_planet="Moon",
        core_tension="Feelings swell—comfort wants a hug, Jupiter wants a saga.",
        visual_metaphor="Jupiter’s giant story scroll unrolls through Moon’s pillow fort like a tidal wave of paper.",
        constructive_channel="Emotional generosity, protective optimism, mood uplift without invalidating.",
        suggested_scene_angles=_s(
            "Moon hugs pillow while Jupiter drapes a huge optimistic banner over the fort window.",
            "Jupiter offers oversized cookie; Moon slides tide-chart like a shield—soft comedy.",
            "Moon’s cloud bed gets Jupiter lecture pointer as a seesaw plank—gentle absurdity.",
            "Jupiter magnifies a single felt star until it becomes Moon’s whole ceiling—cozy overwhelm.",
        ),
        avoid=_a("dismissive toxic positivity", "panic mockery", "crowded sentimental clutter"),
        base_mode="mixed",
    ),
    ("Jupiter", "Mercury"): CatstyleTransitPairSeed(
        outer_planet="Jupiter",
        personal_planet="Mercury",
        core_tension="Big-picture teacher vs detail analyst—scope mismatch as comedy.",
        visual_metaphor="Jupiter’s lecture pointer spears Mercury’s star-map card like a kabob.",
        constructive_channel="Generous zoom on meaning; Mercury’s facts get honored in the footnote margin.",
        suggested_scene_angles=_s(
            "Mercury speed-flips flashcards; Jupiter catches them in a graduation cape net.",
            "Debate at two-tier chalkboard: Jupiter writes one giant word; Mercury fills ticks in margins.",
            "Travel planning: Jupiter points to wild horizon sticker; Mercury counts steps on tiny abacus.",
            "Mercury offers flowchart scroll; Jupiter folds it into a paper airplane—perspective joke.",
        ),
        avoid=_a("classroom humiliation", "smug elitism", "unreadable micro-text"),
        base_mode="mixed",
    ),
    ("Jupiter", "Venus"): CatstyleTransitPairSeed(
        outer_planet="Jupiter",
        personal_planet="Venus",
        core_tension="Values and taste meet luck and excess—more is more vs enough is beautiful.",
        visual_metaphor="Jupiter inflates Venus’s single rose into a bouquet the size of a parade float.",
        constructive_channel="Generous aesthetics, shared values, celebratory harmony without clutter glam.",
        suggested_scene_angles=_s(
            "Venus offers one pearl; Jupiter counters with a comically oversized gift box (blank).",
            "Jupiter drapes Venus in laurel twice her size—she deadpans under the weight.",
            "Venus balances on Jupiter’s coin-purse stack like stairs—minimal props, thick outlines.",
            "Jupiter’s telescope shows Venus a ‘lucky star’ that is just a sticker—comedy hope.",
        ),
        avoid=_a("glossy luxury overload", "runway excess", "readable brand logos"),
        base_mode="mixed",
    ),
    ("Jupiter", "Mars"): CatstyleTransitPairSeed(
        outer_planet="Jupiter",
        personal_planet="Mars",
        core_tension="Faith in the mission vs hot-headed push—go bigger vs hit now.",
        visual_metaphor="Mars charges with flame tuft; Jupiter opens a cartoon drawbridge too slowly—timing gag.",
        constructive_channel="Courage with perspective, ethical fight, coached boldness.",
        suggested_scene_angles=_s(
            "Mars foam-sword jabs Jupiter’s giant foam shield labeled blank.",
            "Jupiter points to horizon; Mars already halfway up a tiny ladder—impulse comedy.",
            "Jupiter offers pep-talk megaphone; Mars steam-ears cool into heart puffs.",
            "Mars tries sprint; Jupiter’s cape becomes finish line ribbon—playful restraint.",
        ),
        avoid=_a("real weapons", "blood", "toxic machismo"),
        base_mode="mixed",
    ),
    ("Saturn", "Sun"): CatstyleTransitPairSeed(
        outer_planet="Saturn",
        personal_planet="Sun",
        core_tension="Authority and limits dim the spotlight—ego meets schedule.",
        visual_metaphor="Saturn lowers a giant hourglass in front of Sun’s corona like a stage shutter.",
        constructive_channel="Mature visibility, earned pride, sustainable leadership.",
        suggested_scene_angles=_s(
            "Sun poses; Saturn taps watch face—Sun’s rays shorten into tidy tick marks.",
            "Saturn hands Sun a tiny hard hat for their halo—structure serves shine.",
            "Sun’s director chair blocked by Saturn’s two-block stack—minimal prop gag.",
            "Saturn measures Sun’s mane with ruler; Sun puffs anyway—comic pride.",
        ),
        avoid=_a("cruel humiliation", "grim authoritarian violence", "body shame"),
        base_mode="mixed",
    ),
    ("Saturn", "Moon"): CatstyleTransitPairSeed(
        outer_planet="Saturn",
        personal_planet="Moon",
        core_tension="Safety vs structure—feelings meet cold frames.",
        visual_metaphor="Saturn builds a doorframe around Moon’s blanket fort—Moon peeks through heart cutout.",
        constructive_channel="Emotional boundaries that still feel caring; predictable comfort.",
        suggested_scene_angles=_s(
            "Moon clutches pillow; Saturn files door edges until they fit softer curve.",
            "Saturn stacks blocks as stepping stones to Moon’s cloud—gentle access.",
            "Moon hides under blanket; Saturn offers single-window star cutout—agreed light.",
            "Saturn’s watch ticks; Moon sets pillow alarm to ‘snooze’ with paw—soft defiance.",
        ),
        avoid=_a("emotional coldness cruelty", "shaming sensitivity", "panic mockery"),
        base_mode="mixed",
    ),
    ("Saturn", "Mercury"): CatstyleTransitPairSeed(
        outer_planet="Saturn",
        personal_planet="Mercury",
        core_tension="Facts meet deadlines—wit collides with ‘not yet’.",
        visual_metaphor="Mercury’s notes slide under Saturn’s giant paperweight stamp labeled blank.",
        constructive_channel="Clear contracts for ideas; disciplined messaging.",
        suggested_scene_angles=_s(
            "Mercury scribbles air; Saturn slides inbox tray like wall—paper comedy.",
            "Saturn’s skeleton key locks Mercury’s overstuffed satchel—then unlocks one flap.",
            "Mercury balances on step-stool; Saturn steadies base—co-built clarity.",
            "Saturn taps metronome; Mercury syncs pen taps—deadpan duet.",
        ),
        avoid=_a("unreadable micro-text", "classroom humiliation", "smug elitism"),
        base_mode="mixed",
    ),
    ("Saturn", "Venus"): CatstyleTransitPairSeed(
        outer_planet="Saturn",
        personal_planet="Venus",
        core_tension="Pleasure under audit—beauty meets deadlines and contracts.",
        visual_metaphor="Saturn’s ring silhouette overlaps Venus’s rose like a stamped seal trap.",
        constructive_channel="Design studio teamwork—architecture sketch, watch layout, fashion collab.",
        suggested_scene_angles=_s(
            "Saturn in pinstripe checks wristwatch while Venus holds fabric bolt—boxed-in glam.",
            "Venus offers rose; Saturn slides blank contract across desk—meeting comedy.",
            "Their rings overlap as paperwork aura—absurd obligation silhouette.",
            "Saturn clipboard tallies joke ‘pleasure units’; Venus clutches one pearl—audit gag.",
        ),
        avoid=_a("harsh humiliation", "overcrowded bling", "grim violence"),
        base_mode="mixed",
    ),
    ("Saturn", "Mars"): CatstyleTransitPairSeed(
        outer_planet="Saturn",
        personal_planet="Mars",
        core_tension="Impulse meets brakes—anger meets discipline.",
        visual_metaphor="Mars charges with flame trail; Saturn calmly raises a watch-shaped stop sign.",
        constructive_channel="Disciplined action, training plan, controlled force—coach energy.",
        suggested_scene_angles=_s(
            "Mars foam-sword bounces off Saturn’s calendar wall like a training pad.",
            "Saturn measures Mars’s flame with ruler; Mars pouts but adjusts stance.",
            "Mars punches a deadline wall panel; it flips to training checklist—positive reframe.",
            "Saturn’s ring becomes hula-hoop track; Mars runs laps—structured burn.",
        ),
        avoid=_a("violent injury", "realistic aggression", "military realism"),
        base_mode="mixed",
    ),
    ("Uranus", "Sun"): CatstyleTransitPairSeed(
        outer_planet="Uranus",
        personal_planet="Sun",
        core_tension="Identity jolted awake—ego meets lightning rebrands.",
        visual_metaphor="Uranus zaps Sun’s corona into zig-zag outline—still cute, still readable.",
        constructive_channel="Authentic self-experiment; liberated visibility.",
        suggested_scene_angles=_s(
            "Sun poses; Uranus swaps podium for unicycle stool—surprise upgrade gag.",
            "Uranus opens portal hoop behind Sun’s chair; Sun’s mane stands comic dandelion.",
            "Sun tries spotlight; Uranus refracts it into rainbow prism shards—flat shapes only.",
            "Uranus hands Sun mismatched crown halves; Sun wears both—quirky king.",
        ),
        avoid=_a("cruel identity mockery", "shaming neurodiversity", "mean pranks"),
        base_mode="tension",
    ),
    ("Uranus", "Moon"): CatstyleTransitPairSeed(
        outer_planet="Uranus",
        personal_planet="Moon",
        core_tension="Comfort vs chaos—Moon wants pillow and blanket pled; Uranus wants novelty now.",
        visual_metaphor="Uranus bursts from electric portal hoop; Moon jolts awake on cloud couch clutching pillow and blanket pled.",
        constructive_channel="Shock with care—blanket parachute clipped safe, weird gadget solves mood.",
        suggested_scene_angles=_s(
            "Moon slumped with pillow + blanket pled; Uranus lands with rock-and-roll paw gesture—Moon theatrically offended.",
            "Lightning zig slices Moon’s fog cloud; Moon hugs blanket tighter; Uranus shrugs ‘oops’ sparkle.",
            "Emotional tide-wave silhouette meets electric bolt—silhouettes bonk as cartoons.",
            "Uranus pops confetti; Moon catches pieces in nightcap—startle then smile.",
        ),
        avoid=_a("panic attack mockery", "cruel pranks", "mean-spirited humiliation"),
        base_mode="tension",
    ),
    ("Uranus", "Mercury"): CatstyleTransitPairSeed(
        outer_planet="Uranus",
        personal_planet="Mercury",
        core_tension="Logic meets glitch—plans spark sideways.",
        visual_metaphor="Mercury’s checklist becomes a paper lightning bolt in Uranus’s portal hoop.",
        constructive_channel="Innovative thinking, clever pivots, fresh framing for facts.",
        suggested_scene_angles=_s(
            "Mercury tries to pin note; Uranus magnet-repels sticky stack—harmless chaos.",
            "Uranus rotates Mercury’s star-map card 90°; Mercury deadpan redraws axis.",
            "Mercury’s pencil sparks; Uranus applauds with foam finger—silly hype.",
            "Uranus replaces Mercury’s eraser with cube puzzle—one-move gag.",
        ),
        avoid=_a("unreadable micro-text", "smug elitism", "cruel pranks"),
        base_mode="mixed",
    ),
    ("Uranus", "Venus"): CatstyleTransitPairSeed(
        outer_planet="Uranus",
        personal_planet="Venus",
        core_tension="Beauty, value, and attachment get shocked by freedom and sudden taste shifts.",
        visual_metaphor="Uranus zaps Venus’s tidy handbag into a weird asymmetrical future-prop—still flat colors.",
        constructive_channel="Fresh style, liberated values, experimental beauty.",
        suggested_scene_angles=_s(
            "Venus holds a ‘perfect’ outfit on hanger; Uranus neon-paints one sleeve zig-zag.",
            "Venus’s rose grows electric petals; Venus side-eyes the voltage—comedy flirt with change.",
            "Uranus opens portal hoop under Venus’s comfort rug; rug lifts like magic carpet gag.",
            "Venus balances pearls; Uranus replaces one with rubber band ball—playful upgrade.",
        ),
        avoid=_a("generic hearts only", "overdecorated luxury", "readable brand logos"),
        base_mode="tension",
    ),
    ("Uranus", "Mars"): CatstyleTransitPairSeed(
        outer_planet="Uranus",
        personal_planet="Mars",
        core_tension="Direct strike meets dodge—Mars wants line, Uranus wants zig.",
        visual_metaphor="Mars charges straight; Uranus splits into cardboard cutout triptych—harmless dodge.",
        constructive_channel="Tactical creativity, adaptive fight, playful sparring.",
        suggested_scene_angles=_s(
            "Mars foam sword swishes; Uranus rides office chair away with spark trail.",
            "Uranus rewires Mars’s whistle to honk duck sound—Mars confused then laughs.",
            "Mars draws straight chalk line; Uranus wiggles it into wave—comic physics.",
            "Uranus offers mismatched sparring pads; Mars picks louder color—compromise gag.",
        ),
        avoid=_a("real weapons", "blood", "cruel humiliation"),
        base_mode="tension",
    ),
    ("Neptune", "Sun"): CatstyleTransitPairSeed(
        outer_planet="Neptune",
        personal_planet="Sun",
        core_tension="Clear ego meets dissolve—spotlight softens into fog.",
        visual_metaphor="Neptune’s mist washes Sun’s sharp silhouette into gentle glow edges.",
        constructive_channel="Compassionate visibility, humble charisma, soft focus kindness.",
        suggested_scene_angles=_s(
            "Sun tries lens flare pose; Neptune offers fog filter on a stick—comedy soft glam.",
            "Neptune sprays gentle mist; Sun’s rays become cotton-ball corona—readable.",
            "Sun stands on stage; Neptune rolls in cloud curtain early—premature gentle ending.",
            "Neptune hands blank bottle; Sun uses it as mic—symbolic not branded.",
        ),
        avoid=_a("vanishing self erasure cruelty", "drug cues", "unreadable glow clutter"),
        base_mode="mixed",
    ),
    ("Neptune", "Moon"): CatstyleTransitPairSeed(
        outer_planet="Neptune",
        personal_planet="Moon",
        core_tension="Feelings blur—memory and longing pool together.",
        visual_metaphor="Moon’s tide chart melts into Neptune’s wavy outline like a sticker peel.",
        constructive_channel="Gentle empathy, dream processing, compassionate fog.",
        suggested_scene_angles=_s(
            "Moon cradles felt star inside fog pocket; Neptune adds tiny fish silhouette beside it.",
            "Neptune offers shell-phone; Moon listens to ocean hiss—no text UI.",
            "Moon hides under blanket; Neptune becomes blanket-shaped cloud—soft camouflage.",
            "Neptune draws wave under Moon’s stool; Moon surfs two inches—absurd cute.",
        ),
        avoid=_a("panic mockery", "shaming sensitivity", "horror dissolve"),
        base_mode="mixed",
    ),
    ("Neptune", "Mercury"): CatstyleTransitPairSeed(
        outer_planet="Neptune",
        personal_planet="Mercury",
        core_tension="Analysis dissolves into fog—facts meet dreams.",
        visual_metaphor="Mercury’s checklist floats inside Neptune’s aquarium fog with tiny fish swimming through letters.",
        constructive_channel="Imagination plus language—poetry, symbolic thinking, inspired writing.",
        suggested_scene_angles=_s(
            "Mercury tries to read notes while fish swim through the letters—deadpan focus.",
            "Neptune fog turns Mercury’s clipboard into a dream map outline—no readable words.",
            "Mercury catches a slippery ‘thought-fish’ with pencil eraser end—silly slapstick.",
            "Mercury’s glasses fog; Neptune offers wipe cloth shaped like wave—gentle help.",
        ),
        avoid=_a("unreadable text", "overly mystical clutter", "micro-detail clutter"),
        base_mode="mixed",
    ),
    ("Neptune", "Venus"): CatstyleTransitPairSeed(
        outer_planet="Neptune",
        personal_planet="Venus",
        core_tension="Desire meets illusion—romance fog and soft edges.",
        visual_metaphor="Venus’s mirror reflects Neptune fish instead of face—gentle surreal gag.",
        constructive_channel="Compassionate desire, imaginative beauty, values with soul.",
        suggested_scene_angles=_s(
            "Venus offers rose; Neptune turns stem into wavy noodle—playful dissolve.",
            "Neptune sprays mist; Venus’s cheeks stay rose but outline wobbles—comic softness.",
            "Venus tries catwalk; Neptune rolls fog runway—low contrast sillhouette.",
            "Neptune hands shell; Venus listens for compliment wave—no audio UI.",
        ),
        avoid=_a("explicit sexualization", "fetish cues", "unreadable mirror text"),
        base_mode="mixed",
    ),
    ("Neptune", "Mars"): CatstyleTransitPairSeed(
        outer_planet="Neptune",
        personal_planet="Mars",
        core_tension="Direct strike vs dissolve—action meets fog.",
        visual_metaphor="Mars charges; Neptune floats inside fog wall; fish-bubble motif wobbles at cheek.",
        constructive_channel="Compassionate action, clarity after steam, training dummy in mist.",
        suggested_scene_angles=_s(
            "Mars foam sword meets fog; big comic steam cloud hides both then two peek out.",
            "Neptune blankly lets Mars shove pass through mist—hands ripple harmless.",
            "Mars fireball cartoon meets wave splash—steam heart puff punchline.",
            "Mars draws line; Neptune wiggles line into wave—comic physics.",
        ),
        avoid=_a("real weapons", "blood", "drug cues"),
        base_mode="tension",
    ),
    ("Pluto", "Sun"): CatstyleTransitPairSeed(
        outer_planet="Pluto",
        personal_planet="Sun",
        core_tension="Power and visibility pulled toward shadow—ego meets depth.",
        visual_metaphor="Pluto’s shadow ring eclipses part of Sun’s corona like a velvet curtain pull.",
        constructive_channel="Honest influence, integrity under pressure, humble strength.",
        suggested_scene_angles=_s(
            "Sun stands center; Pluto dims one spotlight wedge—shared stage metaphor.",
            "Pluto slides blank ‘rules’ card; Sun flips to ‘values’ card—deadpan stare-off.",
            "Sun’s tiny crown casts long shadow shaped like Pluto cloak—playful silhouette.",
            "Pluto offers single ember dot; Sun accepts as pupil highlight—minimal mystique.",
        ),
        avoid=_a("gore", "horror realism", "sexualization", "cult glorification"),
        base_mode="tension",
    ),
    ("Pluto", "Moon"): CatstyleTransitPairSeed(
        outer_planet="Pluto",
        personal_planet="Moon",
        core_tension="Emotional comfort pulled into shadow intensity—depth without possession.",
        visual_metaphor="Pluto’s shadow tide pulls Moon’s pillow and blanket into a slow dark orbit—still cartoon symbolic.",
        constructive_channel="Safe emotional truth, boundaries, depth without emotional possession.",
        suggested_scene_angles=_s(
            "Pluto spiral-eyes dim; Moon clutches pillow while shadow ring tugs the cloud closer—metaphor orbit.",
            "Moon’s cozy cloud blanket ripples like black tide; Moon side-eyes Pluto cauldron steam—funny not horror.",
            "Cauldron steam puffs into vague family-photo-shaped fog silhouette—symbolic and absurd.",
            "Moon hides under blanket pled; Pluto taps cauldron once; Moon peeks—consent beat.",
        ),
        avoid=_a("gore", "horror realism", "sexualization", "helpless victim framing without cartoon metaphor"),
        base_mode="tension",
    ),
    ("Pluto", "Mercury"): CatstyleTransitPairSeed(
        outer_planet="Pluto",
        personal_planet="Mercury",
        core_tension="Secrets vs syntax—truth wants silence, Mercury wants labels.",
        visual_metaphor="Mercury’s pencil snaps on Pluto’s shadow chalk line—ink becomes smoke wisps.",
        constructive_channel="Deep honesty in words, investigative care, taboo as metaphor only.",
        suggested_scene_angles=_s(
            "Mercury flips notepad; Pluto slides blank redaction bar prop—comedy censorship.",
            "Pluto offers magnifying glass; Mercury finds only spiral doodle—simple mystery.",
            "Mercury speed-talks; Pluto slow-blinks once—timing gag.",
            "Pluto’s cauldron bubbles spell-shaped steam with NO letters—unreadable.",
        ),
        avoid=_a("occult sigils with readable text", "gore", "explicit horror"),
        base_mode="tension",
    ),
    ("Pluto", "Venus"): CatstyleTransitPairSeed(
        outer_planet="Pluto",
        personal_planet="Venus",
        core_tension="Hypnotic pull vs overwhelmed desire—metaphorical spell, consent subtext via cartoon.",
        visual_metaphor="Pluto spiral eyes and cauldron; Venus half-submerged in purple potion looking overwhelmed not spa-happy.",
        constructive_channel="Boundary talk at cauldron rim—two spoons, dimmed spirals, mutual exhale.",
        suggested_scene_angles=_s(
            "Pluto stirs black cauldron; Venus overwhelmed in bubbling potion—absurd tension only.",
            "Shadow tendrils tug Venus orbit; Venus dazed—puppetry metaphor, no bondage imagery.",
            "Pluto locks spiral eyes; Venus unable to step back—mesmerized deadpan comedy.",
            "Shadow-string silhouettes only; Venus emotionally caught mid-step—metaphor strings.",
        ),
        avoid=_a("explicit horror", "gore", "fetish imagery", "joyful spa Venus glam"),
        base_mode="tension",
    ),
    ("Pluto", "Mars"): CatstyleTransitPairSeed(
        outer_planet="Pluto",
        personal_planet="Mars",
        core_tension="Force meets control—Mars heat vs Pluto depth pressure.",
        visual_metaphor="Mars flame tuft bends around Pluto’s flat shadow wall like wind around cliff.",
        constructive_channel="Courage with consent, power with ethics, channeled intensity.",
        suggested_scene_angles=_s(
            "Mars charges; Pluto slides cauldron lid as shield—clang gag, non-graphic.",
            "Pluto points spiral eyes; Mars steam ears shrink—comic intimidation then smirk.",
            "Mars foam sword taps Pluto cloak; cloak absorbs hit as shadow puddle—harmless.",
            "Pluto offers handshake; Mars hesitates then fist-bumps—cooldown beat.",
        ),
        avoid=_a("gore", "real weapons", "toxic domination glam"),
        base_mode="tension",
    ),
}


def _build_all_25() -> None:
    expected = 5 * 5
    if len(_TRANSIT_PAIR_SEEDS) != expected:
        raise RuntimeError(f"Expected {expected} transit seeds, got {len(_TRANSIT_PAIR_SEEDS)}")


_build_all_25()

TRANSIT_PAIR_SEEDS: Final[dict[tuple[str, str], CatstyleTransitPairSeed]] = _TRANSIT_PAIR_SEEDS


def orient_outer_personal(planet_a: str, planet_b: str) -> tuple[str, str] | None:
    """Return (outer, personal) if this is a social/outer-to-personal pair (order-insensitive), else None."""
    if planet_a in OUTER_PLANETS and planet_b in PERSONAL_PLANETS:
        return (planet_a, planet_b)
    if planet_b in OUTER_PLANETS and planet_a in PERSONAL_PLANETS:
        return (planet_b, planet_a)
    return None


def get_transit_pair_seed(outer_planet: str, personal_planet: str) -> CatstyleTransitPairSeed | None:
    key = (outer_planet, personal_planet)
    return TRANSIT_PAIR_SEEDS.get(key)


def list_transit_pair_seeds() -> list[CatstyleTransitPairSeed]:
    return [TRANSIT_PAIR_SEEDS[k] for k in sorted(TRANSIT_PAIR_SEEDS, key=lambda t: (t[0].lower(), t[1].lower()))]


def is_seeded_transit_pair(planet_a: str, planet_b: str) -> bool:
    o = orient_outer_personal(planet_a, planet_b)
    if o is None:
        return False
    return get_transit_pair_seed(o[0], o[1]) is not None
