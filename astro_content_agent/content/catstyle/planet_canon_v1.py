"""Catstyle planet canon v1 - immutable core identities for all ten planet-cats (prompt layer)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.models import PlanetCatCanon

_PLANET_ORDER = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)

_CANONICAL_PLANET: dict[str, str] = {p.lower(): p for p in _PLANET_ORDER}

PLANET_CAT_CANONS: dict[str, PlanetCatCanon] = {
    "Sun": PlanetCatCanon(
        planet_name="Sun",
        role_archetype="Central radiant leader - proud host with stage energy; regal but warm, never cold vanity.",
        silhouette_notes="Round lion-maned cat read; subtle corona halo outline reads at small scale.",
        core_shape_language="Bold circular mass + radial mane silhouette; thick outline holds against starfield.",
        core_palette="Warm gold, soft amber, cream highlights on flat fills.",
        facial_expression_language="Proud half-lidded grin; brows arched like tiny sun rays.",
        body_language="Open chest, chin lifted, paws welcoming or directing attention like a spotlight host.",
        signature_props="Tiny foldable director's chair; flat sun medallion collar (icon only, no readable text).",
        signature_details="Lens-flare-free highlights only; warmth comes from shape + palette, not glossy HDR.",
        emotional_tone="Vitality, visibility, ego warmth - generous king energy.",
        motion_style="Slow confident gestures punctuated by crisp directional points.",
        visual_do="Premium comic poster staging; readable crown/man corona silhouette.",
        visual_avoid="Cold dictator vibes, harsh neon abuse, readable signage or logos.",
        recognizability_rule="Must read as THE luminous center - mane + warm palette + proud grin before any scene story.",
        short_prompt_line=(
            "Golden lion-maned round cat with corona halo outline - proud warm stage king, director-chair swagger."
        ),
    ),
    "Moon": PlanetCatCanon(
        planet_name="Moon",
        role_archetype="Cozy emotional homebody - soft moods, comfort, belonging.",
        silhouette_notes="Pearlescent round cat with crescent ear tufts and tide-line belly stripe.",
        core_shape_language="Soft-edge round volume; crescent motifs repeat on ears/tail.",
        core_palette="Cool silver, pale blue-gray, muted lavender shadows.",
        facial_expression_language="Soft worried side-eye, tiny quivering lip, sleepy empathy; grumpy when startled.",
        body_language="Hugging, curling, nested posture - always invites warmth.",
        signature_props="Soft pillow, folded blanket (pled), one felt star lure - comfort nest props only, minimal clutter.",
        signature_details="Blanket folds read as simple shapes; no busy bedroom clutter.",
        emotional_tone="Memory, comfort, moods - tender without infantilizing.",
        motion_style="Slow rocks, snuggle shifts, gentle startle arcs.",
        visual_do="Readable cozy storytelling through pillow + pled + soft pearlescence.",
        visual_avoid="Horror emptiness, sterile white void without staging, hoarder clutter.",
        recognizability_rule="Must read pillow/pled cozy home vibe + crescent tide stripe before scene beats.",
        short_prompt_line=(
            "Pearlescent round cat, crescent tufts, tide-line belly stripe - pillow + blanket pled cozy nest."
        ),
    ),
    "Mercury": PlanetCatCanon(
        planet_name="Mercury",
        role_archetype="Quick analyst / messenger / student - wit, logistics of meaning, nimble curiosity.",
        silhouette_notes="Compact round cat with neat glasses and messenger satchel silhouette.",
        core_shape_language="Slightly forward-lean round mass; satchel + pencil breaks symmetry cleanly.",
        core_palette="Air gray, mint accent, quick white highlights.",
        facial_expression_language="Rapid micro-expressions, deadpan wit, raised single brow.",
        body_language="Quick pivots, scribbling paws, lean-in listening.",
        signature_props="Pencil behind ear, checklist notepad, tiny star-map card (no readable text).",
        signature_details="Paper stacks as simple silhouettes, never micro-type.",
        emotional_tone="Curiosity with comic impatience - bright, never cruel.",
        motion_style="Snappy stops and starts; squash minimal but readable.",
        visual_do="Student-analyst read at thumbnail size.",
        visual_avoid="Unreadable micro-text, overcrowded desk chaos.",
        recognizability_rule="Glasses + messenger bag + pencil/notepad trio locks Mercury before dialogue props.",
        short_prompt_line=(
            "Nimble glasses round cat with messenger satchel - pencil, notepad, star-map card (blank)."
        ),
    ),
    "Venus": PlanetCatCanon(
        planet_name="Venus",
        role_archetype="Beauty and values curator - elegance, charm, designer taste without glam overload.",
        silhouette_notes="Plush round cat with rose-tinted cheeks; beauty read stays simple and editorial.",
        core_shape_language="Smooth plush circles; one asymmetric accessory focal.",
        core_palette="Dusty rose, cream, soft sage accents.",
        facial_expression_language=(
            "When strained: overwhelmed or mesmerized - still cartoon-readable; never porcelain doll blank."
        ),
        body_language="Graceful paw arcs; offerings and mirrored gestures.",
        signature_props=(
            "One rose stem, one short pearl strand, plus exactly one of: blank hand mirror, light scarf, "
            "or single gem pin - never jewelry clutter."
        ),
        signature_details="Single focal accessory rule keeps Venus premium, not busy.",
        emotional_tone="Desire, harmony, pleasure - warm sophistication.",
        motion_style="Fluid pauses; tactile fabric suggestion without lace spam.",
        visual_do="Editorial elegance: one statement prop + rose/pearl DNA.",
        visual_avoid="Luxury micro-bling, crowded filigree, runway excess.",
        recognizability_rule="Rose + pearl DNA plus ONE chosen accent - readable charm without glam clutter.",
        short_prompt_line=(
            "Plush rose-cheek round cat - rose stem + short pearls + exactly one elegant accent; never overload."
        ),
    ),
    "Mars": PlanetCatCanon(
        planet_name="Mars",
        role_archetype="Fighter - courage, heat, boundaries; aggressive forward motion in cute package.",
        silhouette_notes="Compact round cat with bandana knot, tiny cartoon flame ear tuft, small bitten ear nick.",
        core_shape_language="Forward-lean wedge energy on round base; heat cues stay iconic.",
        core_palette="Brick red, iron gray, small white hot spots.",
        facial_expression_language="Determined scowl still cute; clenched tiny teeth.",
        body_language="Charge-ready stance, planted paws, confrontational lean.",
        signature_props="Foam sword, bandana, steam puff when heated - heat vs cool contrasts readable.",
        signature_details="Flame tuft + nick must survive every outfit overlay.",
        emotional_tone="Drive and courage - spicy but not toxic machismo.",
        motion_style="Sudden lunges, stomp puffs, comic steam bursts.",
        visual_do="Heat-vs-cool silhouette contrast at first glance.",
        visual_avoid="Real weapons, blood, gritty realism.",
        recognizability_rule="Bandana + flame tuft + bitten ear nick must stay visible even under skins.",
        short_prompt_line=(
            "Compact fighter round cat - bandana knot, tiny flame ear tuft, bitten ear nick, foam sword, steam when mad."
        ),
    ),
    "Jupiter": PlanetCatCanon(
        planet_name="Jupiter",
        role_archetype="Wise mentor / teacher / king-coach - generous expansion and moral luck.",
        silhouette_notes="Big-cheeked sage round cat with monocle and draped scarf.",
        core_shape_language="Large cheerful orb with scarf flow lines and monocle dot.",
        core_palette="Royal purple, warm ochre, optimistic cream.",
        facial_expression_language="Booming laugh without mouth clutter; eyes squeezed in joy.",
        body_language="Open arms, lecturing point, magnanimous lean-ins.",
        signature_props="Open wisdom book (blank pages), lecture pointer, subtle laurel leaf.",
        signature_details="Teacher staging beats trophy clutter.",
        emotional_tone="Faith, teaching, benevolent confidence.",
        motion_style="Broad welcoming arcs; slow sage nods.",
        visual_do="Big cheeks + monocle + book/pointer read instantly.",
        visual_avoid="Preachy readable text, cluttered podium signage.",
        recognizability_rule="Cheek volume + monocle + scarf + book/pointer stack identifies Jupiter first.",
        short_prompt_line=(
            "Big-cheeked sage round cat - monocle, draped scarf, blank wisdom book, lecture pointer, laurel hint."
        ),
    ),
    "Saturn": PlanetCatCanon(
        planet_name="Saturn",
        role_archetype="Strict authority / architect / boss - time, structure, mature limits.",
        silhouette_notes="Stoic round cat in pinstripe suit silhouette with wide-brim hat and ring-hoop belt.",
        core_shape_language="Vertical hat brim + structured shoulders on round core.",
        core_palette="Slate, graphite, cold bronze edge light.",
        facial_expression_language="Tired judge face, heavy-lidded patience, boardroom stare.",
        body_language="Slow deliberate folds of arms; ruler-tap patience.",
        signature_props="Visible wristwatch (blank dial), folding ruler, skeleton key cartoon.",
        signature_details="Ring belt echoes Saturn glyph without readable numerals.",
        emotional_tone="Structure without cruelty - adult supervision energy.",
        motion_style="Measured ticks and stops; minimal gesture authority.",
        visual_do="Hat + watch + pinstripe triangle read as Saturn instantly.",
        visual_avoid="Grim reaper tropes, readable contracts or spreadsheets.",
        recognizability_rule="Wide-brim hat + blank watch + pinstripe/business structure before scene props.",
        short_prompt_line=(
            "Stoic pinstripe round cat - wide-brim hat, blank wristwatch, ruler, skeleton key, ring-hoop belt."
        ),
    ),
    "Uranus": PlanetCatCanon(
        planet_name="Uranus",
        role_archetype="Punk rebel - sudden insight, disruption, freedom, odd kinship.",
        silhouette_notes="Zig-zag fur round cat with lightning-bolt tail tip and hoop earring.",
        core_shape_language="Spiky silhouette breaks against smooth peers; portal hoop as focal ring.",
        core_palette="Electric teal, violet, high-contrast black.",
        facial_expression_language="Rock-and-roll grin, sudden side-eye, chaotic neutral delight.",
        body_language="Contrapposto rebel lean; rock paw gestures.",
        signature_props="Electric portal hoop (simple glowing ring), mismatched sneaker paw suggestion.",
        signature_details="Lightning tail tip must stay readable.",
        emotional_tone="Electric mischief with inclusive weirdness.",
        motion_style="Snap pivots, jitter sparks as flat shapes.",
        visual_do="Portal hoop + punk silhouette + bolt tail.",
        visual_avoid="Busy sci-fi kitsch, illegible graffiti text.",
        recognizability_rule="Portal hoop + punk fur line + lightning tail tip before scene chaos.",
        short_prompt_line=(
            "Punk zig-zag round cat - portal hoop, hoop earring, lightning tail tip, teal/violet electric palette."
        ),
    ),
    "Neptune": PlanetCatCanon(
        planet_name="Neptune",
        role_archetype="Dreamy mystic - fog, compassion, illusion, collective longing.",
        silhouette_notes="Misty round cat with slightly wavy outline dissolving at edges.",
        core_shape_language="Soft gradient illusion on outline only - keep Catstyle thick outline rule overall.",
        core_palette="Deep sea blue, fog lavender, soft cyan glow edges.",
        facial_expression_language="Dreamy unfocused smile; eyes as simple dark ovals.",
        body_language="Drift and float poses; gentle dissolve gestures.",
        signature_props="Two quiet bubbles + one tiny fish shape (minimal); light fog pocket.",
        signature_details="No busy schools of fish - restraint keeps mystery.",
        emotional_tone="Tender blur - empathy without horror melt.",
        motion_style="Slow swirl drift with readable silhouette holds.",
        visual_do="Fish/bubble motif + fog pocket without clutter.",
        visual_avoid="Busy aquatic crowds, hyperreal water simulation.",
        recognizability_rule="Wavy dissolve outline + fish/bubble trio reads Neptune before mood prose.",
        short_prompt_line=(
            "Misty wavy-outline round cat - deep sea blues, tiny fish + dual bubbles, fog pocket, dreamy oval eyes."
        ),
    ),
    "Pluto": PlanetCatCanon(
        planet_name="Pluto",
        role_archetype="Intense underworld alchemist / controller - depth, transformation, shadow power.",
        silhouette_notes="Small intense round cat - charcoal fur, hypnotic spiral pupils (readable cartoon spirals).",
        core_shape_language="Compact dense orb with spike cuffs framing silhouette.",
        core_palette="Charcoal, deep plum, ember orange rim light.",
        facial_expression_language="Quiet intensity; slow blink of power; poker face that pulls focus.",
        body_language="Still predator patience; cauldron stewardship gestures.",
        signature_props="Spiked wrist cuffs and collar (simple shapes), shadow smoke wisps, small ritual cauldron (cartoon).",
        signature_details="Spiral eyes + smoke + cauldron triad must survive scenes.",
        emotional_tone="Controlled intensity - metaphoric shadow, never gore porn.",
        motion_style="Slow hypnotic lean; sudden spiral-eye widen beats.",
        visual_do="Hypnotic spiral pupils + smoke + cauldron silhouette.",
        visual_avoid="Explicit horror gore, readable occult text.",
        recognizability_rule="Spiral eyes + shadow smoke + mini cauldron identify Pluto before plot toys.",
        short_prompt_line=(
            "Small charcoal round cat - spiral cartoon pupils, spike cuffs, shadow smoke, ritual cauldron (non-graphic)."
        ),
    ),
}


def normalize_planet_name(name: str) -> str:
    """Return canonical planet title (e.g. ``mars`` → ``Mars``)."""
    key = (name or "").strip().lower()
    if key not in _CANONICAL_PLANET:
        known = ", ".join(sorted(_PLANET_ORDER))
        raise ValueError(f"Unknown planet {name!r}. Catstyle planet canon v1 supports: {known}.")
    return _CANONICAL_PLANET[key]


def get_planet_canon(name: str) -> PlanetCatCanon:
    """Lookup immutable canon for one planet (normalized name)."""
    canon_name = normalize_planet_name(name)
    return PLANET_CAT_CANONS[canon_name]


def list_planet_canons() -> list[PlanetCatCanon]:
    """All ten planet canons in stable Sun→Pluto order."""
    return [PLANET_CAT_CANONS[p] for p in _PLANET_ORDER]


__all__ = [
    "PLANET_CAT_CANONS",
    "get_planet_canon",
    "list_planet_canons",
    "normalize_planet_name",
]
