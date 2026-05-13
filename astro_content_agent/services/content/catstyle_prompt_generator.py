"""Generate Catstyle v0 image prompt packs (text only; no image API calls)."""
from __future__ import annotations

from astro_content_agent.content.catstyle.aspect_library_v0 import ASPECT_CAT_INTERACTIONS, get_aspect_interaction
from astro_content_agent.content.catstyle.character_skins_v0 import get_character_skin
from astro_content_agent.content.catstyle.hero_shots_v1 import (
    format_hero_shot_prompt_block,
    shot_roles_for_variant_indices,
)
from astro_content_agent.content.catstyle.approved_reference_registry import (
    resolve_approved_reference,
)
from astro_content_agent.content.catstyle.models import (
    CatstylePromptPack,
    CatstylePromptRequest,
    CatstyleRenderStyleProfile,
    PlanetCatCanon,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import (
    get_planet_canon,
    normalize_planet_name as canon_normalize_planet_name,
)
from astro_content_agent.content.catstyle.planet_canon import (
    build_planet_canon_prompt_fragment,
    get_planet_canon as get_planet_canon_v2,
)
from astro_content_agent.content.catstyle.planet_glyph_registry_v1 import (
    canonical_glyph_char,
    format_pair_flag_glyph_system_block,
)
from astro_content_agent.content.catstyle.planet_identity_markers_v1 import (
    format_identity_markers_prompt_block,
    get_planet_identity_marker_profile,
)
from astro_content_agent.content.catstyle.scene_templates_v1 import (
    format_scene_template_prompt_block,
    validate_explicit_scene_template,
)
from astro_content_agent.content.catstyle.render_style_profiles_v1 import (
    DEFAULT_RENDER_STYLE_PROFILE_KEY,
    format_render_style_prompt_block,
    format_render_style_prompt_block_for_flow,
    get_render_style_profile,
)
from astro_content_agent.content.catstyle.world_templates_v1 import (
    DEFAULT_WORLD_TEMPLATE_KEY,
    format_world_template_prompt_block,
    get_world_template,
)
from astro_content_agent.services.content.catstyle_art_direction import (
    apply_art_direction_to_prompt_pack,
    build_catstyle_art_direction_profile,
    resolve_art_energy,
)
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import (
    CatstyleTransitPairSeed,
    get_transit_pair_seed,
    orient_outer_personal,
)

_CATSTYLE_SUBJECT_GUARDS = (
    "Planet-cats keep rounded comic-body proportions with expressive theatrical faces and silhouette-first readability "
    "at thumbnail scale; follow each character's locked canon and identity-marker blocks below. "
    "No text in image, no logos, no brands."
)

_NEGATIVE_BASE_CHUNKS = [
    "text, words, letters, captions, watermarks, logos, trademarks, QR codes",
    "photorealistic, hyperreal skin, photoreal materials, HDR glossy",
    "3D CGI figurine finish, game splash render look, game-engine shading",
    "microtexture noise, tiny crack noise, excess particles clutter",
    "childish nursery style, kawaii, chibi, sticker mascot style",
    "flat vector icon, mobile-game icon look, simplistic educational cartoon",
    "cluttered architecture detail spam, busy background clutter, weak bland composition",
    "disconnected sticker posing, over-rendered fur strands, over-rendered material noise",
    "malformed planetary glyphs, pseudo-symbols, fake astrological letters, distorted zodiac marks, invented sigils",
    "floating white sticker symbols, detached glow glyphs not locked to cloth, symbols pasted over faces or torsos",
]

_FLOW_IMAGE_OPENING_V2 = (
    "Premium cinematic comic-poster illustration — poster-grade comic splash illustration — high-impact heroic "
    "co-discovery alliance splash featuring anthropomorphic planet-cats; hand-painted stylized 2D/2.5D comic feel "
    "(NOT photoreal, NOT 3D CGI, NOT game splash render), collectible-cover polish, monumental opportunity staging, "
    "layered foreground/midground/background depth, bright readable heroic poster lighting with luminous midtones, "
    "dramatic focal and rim-impact lighting, bold authoritative silhouettes, painterly cel-shaded polished comic "
    "rendering—prioritize premium alliance-discovery poster reads over cute mascot simplicity."
)

_FLOW_STYLE_HARDLOCK_V2 = (
    "Prioritize dramatic poster composition over cute simplicity—reject nursery-book softness, kawaii sticker "
    "flattening, and bland mascot idle posing. Stage as premium comic cover / alliance discovery splash: decisive "
    "focal hierarchy, meaningful environment depth behind the duo (never empty flats), dynamic joint motion or "
    "co-revealing gesture with pose authority, cinematic rim lighting sculpting forms—never floating mascots on void "
    "backdrops or emoji-flat icon staging. Texture rule: use only large and medium texture groups "
    "(no dense microtexture layering). Background rule: arena and zodiac floor stay epic but simplified and "
    "less detailed than characters. Lighting rule: dramatic but clean and Instagram-thumb readable—lift exposure for "
    "faces, portal, flags, and Earth cue; luminous golden opportunity portal as central key light with warm bounce "
    "across both muzzles; soft cool Mercury rim light and warm Jupiter generous fill; preserve deep cosmic void mood "
    "without murky underexposure, muddy crushed shadows, or black-crushed silhouettes; never horror/noir darkness."
)


def _image_prompt_lead(render_prof: CatstyleRenderStyleProfile) -> str:
    """Opening sentences: render-profile priority before canon/world/scene (must not contradict premium finish)."""
    return f"{render_prof.image_prompt_opening_line.strip()} {_CATSTYLE_SUBJECT_GUARDS}".strip()


def _image_prompt_opening_prefix(render_prof: CatstyleRenderStyleProfile, *, mode: str | None = None) -> str:
    """Opening lead plus optional v2 style-hardlock mandate (deterministic, highest priority before Aspect line)."""
    m = (mode or "").strip().lower()
    if m == "flow" and render_prof.key == "premium_comic_poster_v2":
        base = f"{_FLOW_IMAGE_OPENING_V2} {_CATSTYLE_SUBJECT_GUARDS}".strip()
        return f"{base} [STYLE HARDLOCK v2 - premium poster mandate] {_FLOW_STYLE_HARDLOCK_V2}".strip()
    base = _image_prompt_lead(render_prof)
    hb = render_prof.style_hardlock_block
    if hb and str(hb).strip():
        return f"{base} [STYLE HARDLOCK v2 - premium poster mandate] {hb.strip()}".strip()
    return base


def _aspect_choreography_block(aspect_type: str, mode: str | None = None) -> str:
    """Deterministic aspect choreography: hard aspects clash; soft aspects cooperate (Catstyle v1)."""
    k = (aspect_type or "").strip().lower()
    mapping: dict[str, str] = {
        "square": (
            "[ASPECT CHOREOGRAPHY v1 - square] Active angular conflict on the zodiac arena: friction, strike/counterstrike, "
            "tense collision beats; keep conflict readable at poster scale but each planet expresses force through its own "
            "planetary physics—never generic MMA."
        ),
        "opposition": (
            "[ASPECT CHOREOGRAPHY v1 - opposition] Face-off polarity on the arena rim: mirrored duel tension, push-pull, "
            "two poles leaning into each other with reversible momentum."
        ),
        "trine": (
            "[ASPECT CHOREOGRAPHY v1 - trine] Smooth cooperative flow: dance-like harmony, synchronized movement, "
            "shared rhythm choreography."
        ),
        "sextile": (
            "[ASPECT CHOREOGRAPHY v1 - sextile] Playful cooperation: light coordinated exchange, quick friendly assists, "
            "sparkling back-and-forth without harsh clash."
        ),
        "conjunction": (
            "[ASPECT CHOREOGRAPHY v1 - conjunction] Merged fused force: combined amplification, stacked silhouettes, "
            "single-forward surge choreography."
        ),
    }
    base = mapping.get(k, "")
    if not base:
        return ""
    if (mode or "").strip().lower() == "flow" and k in ("square", "opposition"):
        return (
            f"{base} [FLOW geometry cue v1] Staging must resolve toward alliance—co-build, shoulder-aligned discovery, "
            "shared lift—never prizefight collision as dominant read."
        )
    return base


def _aspect_choreography_animation_clause(aspect_type: str) -> str:
    """Short animation bias aligned with major-aspect choreography."""
    k = (aspect_type or "").strip().lower()
    mapping: dict[str, str] = {
        "square": "Choreography bias: angular friction, strike/counterstrike readability (planet-specific). ",
        "opposition": "Choreography bias: mirrored face-off, push-pull polarity. ",
        "trine": "Choreography bias: smooth synchronized flow and cooperative rhythm. ",
        "sextile": "Choreography bias: playful coordinated assists and light exchange. ",
        "conjunction": "Choreography bias: fused amplification and merged-forward motion. ",
    }
    return mapping.get(k, "")


def _planet_pair_action_language(pa: str, pb: str) -> str:
    """Planet-specific allowed action lexicon (Moon/Saturn explicit for choreography v1)."""
    pair = {pa.strip().lower(), pb.strip().lower()}
    chunks: list[str] = []
    if "moon" in pair:
        chunks.append(
            "[PLANETARY ACTION LEXICON v1 - Moon] Prefer: pillow strike, moonlight wave, protective defensive motion, "
            "tidal push, emotional flinch/retreat/burst—soft but active movement."
        )
    if "saturn" in pair:
        chunks.append(
            "[PLANETARY ACTION LEXICON v1 - Saturn] Prefer: stone block, freeze/frost field, gravity press, chain bind, "
            "gate slam, ruler strike as measuring/architect line (not a blade swing), wall summon, stop gesture, time lock, "
            "heavy downward force. Saturn may fight hard through barriers/time/weight—never as fiery reckless Mars: "
            "no flames, no fire aura, no ninja/fighter styling, no martial-arts choreography, no reckless attack pose, "
            "no Mars-like aggression, no nunchucks/martial weapons."
        )
    return " ".join(chunks).strip()


def _catstyle_flow_mode_visual_lock(req: CatstylePromptRequest) -> str:
    if (req.mode or "").strip().lower() != "flow":
        return ""
    return (
        "[CATSTYLE FLOW MODE v1 — alliance epic, not combat poster] Preserve premium cinematic comic-poster illustration "
        "quality, rich cel-shaded modeling, dramatic clean light, and layered depth—never flatten. Narrative read: "
        "discovery, opportunity, guided expansion, portal-opening, co-created momentum—both planet-cats share a visible "
        "objective (star chart, horizon band, open atlas, map key activation, threshold doorway) and face or advance "
        "that objective together more than a confrontational stare-down. Prefer joined motion, coordinated reach, "
        "shoulder-aligned co-reading, tandem gesture toward one shared lure. Hard ban on heroic duel/tournament clash/"
        "MMA collision framing, savage brawl staging, squared-off warrior symmetry, shoved-together combat collision, "
        "or spectacle that reads as prizefight. **Flag glyphs:** honor **[CATSTYLE PAIR FLAG GLYPH SYSTEM v1]** from the pair block—"
        "each planet's canonical mark is **painted into its own banner cloth** (heraldic gold / embroidery, cloth-locked, not floating stickers). "
        "Books and maps use spare constellation geometry only—no spammed faux-glyph texture. "
        "Flow readability (mobile / Instagram): bright readable heroic poster lighting with polished comic-cover clarity—"
        "keep dark cosmic arena atmosphere but favor luminous midtones so faces, portal aperture, faction flags, and "
        "distant Earth cue stay legible on small screens; center a luminous golden opportunity portal as primary key "
        "light with warm reflected fill washing both characters' faces; add complementary rim and fill keyed to each "
        "planet-cat's palette so both read as dimensional hero bodies beside their banners; silhouettes and expressions stay crisp—avoid "
        "underexposed murk, muddy shadow blobs, characters disappearing into black crush, or noir horror gloom."
    )


def _mercury_jupiter_flow_planetary_being_lock(req: CatstylePromptRequest, pa: str, pb: str) -> str:
    if (req.mode or "").strip().lower() != "flow":
        return ""
    pair = {pa.strip().lower(), pb.strip().lower()}
    if pair != {"mercury", "jupiter"}:
        return ""
    return (
        "[MERCURY–JUPITER FLOW CAST v1 — planetary bodies first] Mercury reads as the smaller rocky gray-blue scholarly "
        "planet-cat: tight rocky inner-planet silhouette, clever bright eyes, nimble proportions—recognizable as Mercury "
        "before costume trims. Jupiter reads as the large banded wise expansive gas-giant planet-cat: volumetric sphere "
        "body, calm generous stance, flowing bands and soft auroral tone—recognizable as Jupiter before costume "
        "accessories. Costuming only amplifies planet identity; never replace sphere-body read with generic domestic-cat "
        "anatomy. "
        "Pair-flag heraldic detail is governed globally by **[CATSTYLE PAIR FLAG GLYPH SYSTEM v1]** (see choreography block)."
    )


def _mars_heavy_scene_style_decouple_block(req: CatstylePromptRequest, pa: str, pb: str) -> str:
    """Mars-named scene or Mars-heavy reference finisher on a non-Mars pair: anchor finish only—not Mars combat behavior."""
    if "mars" in {pa.strip().lower(), pb.strip().lower()}:
        return ""
    raw = (req.scene_template_key or "").strip().lower()
    mars_named_scene = bool(raw.startswith("mars_"))
    if not mars_named_scene and not req.mars_heavy_style_reference_finisher:
        return ""
    return (
        "[MARS-HEAVY STYLE REFERENCE DECOUPLING v1] This Mars-forward scene template or Mars-heavy reference may anchor "
        "finish quality only for these non-Mars planet-cats: inherit polish, line weight, lighting rhythm, and poster composition "
        "ONLY—do NOT import Mars choreography, sparks/flames, brawling, explosive kicks, savage duel posing, or combat staging onto "
        "these characters."
    )


def _arena_composition_boost_block(req: CatstylePromptRequest) -> str:
    """Composition boost for readable grand arena scale without shrinking subject readability."""
    asp = (req.aspect_type or "").strip().lower()
    world_k = (req.world_template_key or "").strip().lower()
    is_hard = asp in {"square", "opposition"}
    is_hero = req.shot_mode == "hero_pair"
    is_arena_world = world_k == "cosmic_zodiac_arena"
    if not (is_hard or is_hero or is_arena_world):
        return (
            "[ARENA COMPOSITION BOOST v1] Use medium-wide dramatic framing with environmental breathing room: keep both planet-cats "
            "prominent with readable faces, gestures, and clean silhouette separation while preserving visible arena geography around them."
        )
    return (
        "[ARENA COMPOSITION BOOST v1] Target medium-wide dramatic arena framing (not tight close-up, not tiny distant characters): "
        "both planet-cats remain prominent with strong facial readability, gesture readability, and clean silhouette separation. "
        "Keep visible cosmic zodiac coliseum structure: readable arena floor plane, curved coliseum wall, zodiac symbols around the ring, "
        "arches/stadium tiers/layered architecture depth, and grand scale cues. "
        "Give environmental breathing room around subjects so architecture reads as epic context. "
        "Framing negatives: avoid overly tight crop on the two characters, avoid background collapsing into vague darkness, "
        "avoid zodiac arena disappearing, avoid unreadable environment, avoid cropping away coliseum architecture."
    )


def _epic_arena_showdown_block(req: CatstylePromptRequest, pa: str, pb: str) -> str:
    """Optional deterministic composition profile for epic arena spectacle with readable hero action."""
    if (req.shot_mode or "").strip().lower() != "epic_arena_showdown":
        return ""
    pair = {pa.strip().lower(), pb.strip().lower()}
    asp_l = (req.aspect_type or "").strip().lower()
    mode_l = (req.mode or "").strip().lower()
    glyph_lock = ""
    moon_saturn_approved_anchor = ""
    moon_saturn_hard_epic_action = ""
    if pair == {"moon", "saturn"}:
        glyph_lock = (
            "[MOON–SATURN EMBLEM DISCIPLINE v1 — painted banner heraldry] Opposite-side faction banners each carry **one large canonical Moon (\u263d / ☽) or Saturn (\u2644 / ♄) glyph painted into the cloth** as integrated **flat heraldic gold / embroidery**—centered, perspective-correct, following folds and light—**not** floating stickers, **not** pasted over faces. "
            "Moon side reads lunar via pillow/silver/cool pearlescent palette and crescent **ear** staging; Saturn side reads via pinstripe/time-structure Boss cues, hat/watch plaques, stone/chain restraint—"
            "optional simple **ringed-sphere silhouette** as abstract graphic only (not a distorted substitute for the ♄ mark). "
            "Smaller accessory stamps stay secondary to the **banner cloth** identity. "
            " Moon/Saturn epic arena scale HARD LOCK (mandatory—monumental recession, not tight hero crop): pull the camera back further than baseline epic mode; "
            "characters must occupy slightly less of the overall frame while faces and silhouettes remain clearly readable—reduce character dominance versus architecture slightly; "
            "show substantially more readable arena floor plane plus more upper coliseum tiers, arches, and sky-opening; "
            "coliseum walls must recede clearly into the distance with stadium perspective—the arena must read monumental, elevated, expansive; "
            "bias extra recession versus default epic framing so upper arches read farther away and more elevated, emphasize arena curvature and sky-opening, "
            "and let environment breathe behind subjects instead of hugging their silhouettes like shallow wallpaper; "
            "avoid compositions where arena walls feel pasted or attached flat immediately behind the characters like shallow backdrop wallpaper. "
            "Benchmark alignment note (approved Jupiter/Mars epic arena scale as distant composition reference target): preserve heroic readability without tightening into portrait dominance. "
        )
        if asp_l == "square" and mode_l == "tension":
            resolved_ms = resolve_approved_reference(
                req.planet_a, req.planet_b, req.aspect_type, req.mode
            )
            if resolved_ms is not None:
                moon_saturn_approved_anchor = (
                    "[CATSTYLE APPROVED REFERENCE ANCHOR v1 - Moon/Saturn square+tension] Preferred visual anchor for this generation context: "
                    "bias composition, lighting mood, and identity readability toward the project's approved Moon/Saturn square+tension reference image "
                    f"(registry_key={resolved_ms.registry_key})—preserve its successful visual language: Moon identity, Saturn identity, taut chain restraint, "
                    "stone pillar/barrier pressure, dark epic restrained clash mood; treat as compositional guidance rather than rigid pixel-copy. "
                )
        if asp_l in ("square", "opposition"):
            moon_saturn_hard_epic_action = (
                "[MOON-SATURN EPIC ARENA ACTION STAGING v5 - balanced lock] Anti-static action blocking: avoid static face-to-face standing poses and flat symmetrical standoffs. "
                "Keep premium comic-poster force: premium cinematic comic-poster illustration, poster-grade heroic battle splash, polished 2D/2.5D comic rendering, collectible-cover polish, "
                "dramatic rim-impact lighting, crisp line clarity, rich cel-shaded modeling, and layered foreground/midground/background depth. "
                "Visual drift negatives: no nursery art, no storybook look, no soft watercolor wash, no washed-out painterly blur, no flat mascot read. "
                "Color/readability: keep dark-but-vivid contrast with clean edge separation; forbid muddy darkness and unreadable murk. "
                "Night-atmosphere brightness lift (no daylight washout): preserve dramatic deep-blue cosmic night mood but raise overall exposure slightly—richer midtones and luminous contrast—"
                "so subjects stay clearly readable; balance warm subtle arena-floor glow against cool silver-blue lunar rim/key sculpt on Moon, pillow edges, and silver aura cues; "
                "keep starfield depth readable; forbid muddy darkness, crushed shadow blobs, gray-brown exposure collapse, and underexposed unreadable characters. "
                "Arena scale continuity: preserve monumental cosmic zodiac coliseum read with receding walls, visible upper arches, readable floor ring perspective, and two readable Moon/Saturn side banners; "
                "push coliseum recession a touch farther than typical epic framing so upper tiers and arches feel more distant and elevated, show a bit more upper-arch silhouette and arena curvature for expansive mythic depth, "
                "and preserve breathing room between figures and background masonry—never shrink-wrap architecture tight behind shoulders. "
                "Active clash continuity: keep readable mid-action confrontation with visible tension between restraint and resistance, preserving diagonal confrontation energy without forcing body-on-body brawling. "
                "Benchmark bias (approved Jupiter/Mars epic arena energy): stronger motion and stronger diagonal confrontation, less passive symmetry, higher heroic readability at poster distance. "
                "Chain tension clarity (Saturnian restraint): Saturn may use chain/control as Saturnian restraint with clear taut read; chain should read functional and load-bearing, not decorative slack, not jewelry drape, "
                "not weaponized nunchuck behavior, and never Mars-like aggression transfer. "
                "Moon action clarity (soft-force counter): Moon may hold, brace, swing, or strike with pillow energy in readable defensive/offensive motion; avoid forcing one rigid hit frame, "
                "but keep intention clear enough that Moon is not passive prop-holding. "
                "Moon motion style: Moon may pull against chain tension while giving a soft-force counter-response, preserving emotional urgency, silver-blue motion cues, and brave-but-vulnerable readability. "
                "Composition depth continuity: avoid flat side-by-side staging; maintain overlapping depth cues, slightly offset character depth planes, and readable arena floor perspective for cinematic space. "
                "Saturn control clarity: Saturn remains cold, heavy, restrictive, and controlling through barrier, gravity, and time-pressure symbolism; never passive Saturn, never flame/fighter/ninja styling, never reckless Mars energy. "
                "Saturn banner continuity: **♄ painted into Saturn's faction banner cloth** as integrated heraldic emblem—centered, cloth-locked, large enough to read at thumbnail scale. "
                "Moon banner continuity: **☽ painted into Moon's faction banner cloth** the same way—lunar read also reinforced by pillow/silver costume cues, not by floating detached symbols. "
                "Earth cue stability: exactly one Earth-like sphere above and behind arena; avoid duplicate Earth-like globes. "
                "Poster continuity reinforcement: preserve movie-one-sheet readability with decisive focal hierarchy, clear silhouette breakup, and controlled detail density (characters highest, architecture medium, sky lowest). "
                "Lighting/readability reinforcement: preserve dramatic key-to-rim sculpting on faces, paws, pillow, chain, and Saturn hat/shoulders; keep contrast punch without muddy low-mid compression. "
                "Premium finish reinforcement: maintain collectible-cover polish with confident contour authority, deliberate silhouette carve-outs, readable overlap, and clean depth progression from foreground duel bodies to midground architecture to far cosmic void. "
                "Hero-poster print discipline: preserve clear face readability and pose intent at thumbnail scale while retaining premium battle-poster gravitas; avoid flattened sticker-tableau staging and avoid soft illustrative vignette drift. "
                "Environment-as-co-star reinforcement: keep zodiac floor ring perspective readable, coliseum wall recession legible, and upper-arch crown forms visible so arena scale feels monumental, elevated, and mythic instead of shallow wallpaper. "
                "Color separation reinforcement: preserve disciplined dark-but-vivid palette with readable silver-blue Moon energy and readable graphite/stone Saturn mass; keep controlled warm accents for contrast readability, never fire-bloom mimicry. "
                "Action readability reinforcement: prioritize first-glance cause/effect readability where Moon's soft-force motion and Saturn's structural restraint are both readable in one frame, with chain tension and pillow intent legible without over-forcing exact impact choreography. "
                "Cinematic depth reinforcement: maintain overlapping depth planes, clear foreground/midground/background spacing, and spatial offset between subjects so the scene reads as poster-cinematic rather than flat side profile. "
                "Monumental arena reinforcement: include clear arena floor sweep, receding stadium tiers, and side architecture supports that frame conflict with ceremonial gravity; avoid clipping architecture into shoulder-level backdrop fragments. "
                "Faction readability reinforcement: Moon/Saturn side emblems should remain large and legible enough to support narrative opposition while staying symbolic (no rendered words), and must not be reduced to tiny unreadable accents. "
                "Detail density discipline: keep character focal regions (faces, paws, pillow edge, chain grip points, Saturn hat silhouette) as highest-detail anchors; keep architecture medium detail; keep sky and far-space accents restrained to avoid muddy clutter. "
                "Contrast hygiene: protect edge separation between characters and arena walls; avoid overcompressed low mids, avoid murky blacks swallowing forms, avoid gray-brown wash that erodes comic-poster identity. "
                "Premium Catstyle identity lock: preserve poster-grade heroic comic splash language, polished 2D/2.5D rendering cues, crisp line clarity, rich cel-shaded modeling, dramatic rim-impact lighting, and high-contrast readability as non-negotiable style anchors. "
                "Anti-storybook drift reinforcement: reject nursery bedtime softness, reject fairytale watercolor haze, reject soft pastel storybook treatment, reject flat mascot simplification, reject toy-like cute flattening that weakens conflict readability. "
                "Negatives: weak action, loose decorative chain, unclear restraint, passive Saturn, duplicated Earth-like sky spheres, shallow pasted backdrop arena, tight portrait crop creep, "
                "environment reduced to backdrop afterthought, washed-out painterly blur, flat mascot simplification."
            )
    ga = canonical_glyph_char(pa)
    gb = canonical_glyph_char(pb)
    sa = f"{pa} ({ga})" if ga else pa
    sb = f"{pb} ({gb})" if gb else pb
    return (
        "[SHOT/COMPOSITION PROFILE v4 - epic_arena_showdown] Mythic showdown poster framing in a ceremonial cosmic arena: "
        "heroic medium-wide to wide cinematic composition where the environment is a co-star and not background afterthought. "
        "Camera/framing correction: pull the camera back slightly into wider poster framing; characters occupy slightly less of the frame while "
        "faces/poses remain readable; preserve negative space and breathing room around central action. "
        "Keep both planet-cats central and readable (clear faces, readable poses, clean silhouette separation, strong aspect interaction), "
        "while expanding environmental breathing room and monumental ceremonial scale. "
        "Arena scale correction: coliseum recedes into the distance, arena walls rise behind the characters, upper arches feel towering and monumental, "
        "with more visible arena floor and more upper architecture so environment feels elevated rather than attached directly behind characters. "
        "Environment targets: clearly readable zodiac floor ring, layered coliseum walls, more visible upper arches, deep stadium tiers/perspective, "
        "additional side architectural structures, visible zodiac symbols, stronger monumental arena feeling, "
        f"and two large readable faction banners on opposite arena sides tied to {sa} and {sb} planetary identities "
        "(each banner shows **one large canonical planetary glyph painted into the flag cloth** as integrated heraldic gold—no readable words, no floating sticker symbols over characters). "
        "Background scale cue: include a clearly readable distant Earth or Earth-like blue-green planet with visible cloud and/or continent pattern "
        "as the human-world impact cue (audience world affected by this aspect), smaller than characters but visually legible, clearly above and behind the arena. "
        "Anti-confusion rule: do not replace the Earth impact cue with Moon/Jupiter/Mars/Saturn/or either character planet; "
        "planet identity belongs on characters, banners, props, reserved emblem zones, and arena symbols unless explicitly overridden. "
        "For Moon aspects specifically, keep Moon identity on the Moon character (crescent ear staging, pillow/blanket language, silver aura, moonlight wave) "
        "and avoid ambiguous moon-like background orb or large Moon sky-body as the main celestial cue when Earth impact cue is requested. "
        f"{glyph_lock}"
        f"{moon_saturn_approved_anchor}"
        f"{moon_saturn_hard_epic_action}"
        "Framing negatives: avoid tight crop and character-dominant framing, vague background darkness, disappearing coliseum, unreadable arena walls, tiny/barely readable Earth cue, "
        "only one visible side banner, over-cropped arena architecture, or environment reduced to a backdrop afterthought."
    )


_IMAGE_PROMPT_SAFE_MAX_CHARS = 31_600


def _compact_prompt_to_budget(prompt: str, safe_max: int = _IMAGE_PROMPT_SAFE_MAX_CHARS) -> str:
    """
    Deterministic prompt budget guard.

    Strategy: normalize whitespace, then if still over budget, drop duplicate sentences/clauses
    (case/space normalized) from left-to-right while preserving order of first occurrence.
    """
    raw = (prompt or "").strip()
    if not raw:
        return raw
    # Whitespace compaction first (cheap, deterministic) but preserve the full rich stack.
    s = " ".join(raw.split())
    if len(s) <= safe_max:
        return s
    # Surgical trim: keep the strongest front-loaded style/identity/action stack and trim tail only.
    cutoff = s.rfind(". ", 0, safe_max)
    if cutoff > int(safe_max * 0.98):
        return s[:cutoff].strip() + "."
    return s[:safe_max].rstrip()


def _animation_prompt_body(
    pa: str,
    pb: str,
    aspect_type: str,
    anim_skin: str,
    render_prof: CatstyleRenderStyleProfile,
    *,
    mode: str | None = None,
) -> str:
    """Loop prompt aligned with the same render finish as still frames (no legacy flat-cartoon lead-in)."""
    prefix = _image_prompt_opening_prefix(render_prof, mode=mode)
    choreo_anim = _aspect_choreography_animation_clause(aspect_type)
    return (
        f"{prefix} "
        f"Loopable 3–5s animation: {pa} and {pb} planet-cats, aspect {aspect_type}; {choreo_anim}"
        f"minimal squash-and-stretch "
        f"preserving silhouette reads; outlines stay crisp at loop resolution; environment honors locked world/scene "
        f"when applicable (otherwise restrained cosmic void is acceptable); readable comic timing.{anim_skin}"
    ).strip()

def normalize_planet_name(name: str) -> str:
    """Canonical planet title (delegates to planet canon v1)."""
    return canon_normalize_planet_name(name)


def _strip_optional_skin(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _strip_optional_str(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _join_world_scene_middle(world_block: str, scene_block: str) -> str:
    parts = [p.strip() for p in (world_block, scene_block) if p and str(p).strip()]
    if not parts:
        return ""
    return " ".join(parts) + " "


def _resolve_world_scene_blocks(
    req: CatstylePromptRequest, pa: str, pb: str
) -> tuple[str, str, dict | None, dict | None]:
    scene_energy = resolve_art_energy(req.editorial_profile, req.mode)
    raw_w = _strip_optional_str(req.world_template_key)
    wt = None
    if raw_w:
        wt = get_world_template(raw_w)
    elif req.premium_art_direction:
        wt = get_world_template(DEFAULT_WORLD_TEMPLATE_KEY)

    world_block = format_world_template_prompt_block(wt, scene_energy=scene_energy) if wt else ""
    world_prof = wt.model_dump(mode="json") if wt else None

    raw_s = _strip_optional_str(req.scene_template_key)
    scene_block = ""
    scene_prof = None
    if raw_s:
        st = validate_explicit_scene_template(raw_s, pa, pb, req.aspect_type)
        scene_block = format_scene_template_prompt_block(st)
        scene_prof = st.model_dump(mode="json")

    return world_block, scene_block, world_prof, scene_prof


def _attach_template_profiles(
    pack: CatstylePromptPack,
    *,
    world_template_profile: dict | None,
    scene_template_profile: dict | None,
    render_style_profile: dict | None,
) -> CatstylePromptPack:
    data = pack.model_dump(mode="json")
    data["world_template_profile"] = world_template_profile
    data["scene_template_profile"] = scene_template_profile
    data["render_style_profile"] = render_style_profile
    return CatstylePromptPack.model_validate(data)


def _dedupe_negative_phrases(phrases: list[str]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for phrase in phrases:
        raw = phrase.strip()
        if not raw:
            continue
        norm = " ".join(raw.lower().split())
        if norm in seen:
            continue
        seen.add(norm)
        ordered.append(raw)
    return ", ".join(ordered)


def _merge_negative_prompt(base_comma_chunks: list[str], extra_phrases: list[str]) -> str:
    pieces: list[str] = []
    for chunk in base_comma_chunks:
        for part in chunk.split(","):
            t = part.strip()
            if t:
                pieces.append(t)
    for phrase in extra_phrases:
        t = phrase.strip()
        if t:
            pieces.append(t)
    return _dedupe_negative_phrases(pieces)


def _resolve_render_style(req: CatstylePromptRequest):
    raw = (req.render_style_profile_key or "").strip()
    key = raw or DEFAULT_RENDER_STYLE_PROFILE_KEY
    profile = get_render_style_profile(key)
    if (req.mode or "").strip().lower() == "flow":
        render_middle = format_render_style_prompt_block_for_flow(profile).strip() + " "
    else:
        render_middle = format_render_style_prompt_block(profile).strip() + " "
    return profile, profile.model_dump(mode="json"), render_middle


def _validate_skins_for_pair(pa: str, pb: str, skin_a: str | None, skin_b: str | None) -> None:
    if skin_a:
        get_character_skin(pa, skin_a)
    if skin_b:
        get_character_skin(pb, skin_b)


def _planet_cat_line(planet: str, canon: PlanetCatCanon, skin_key: str | None) -> str:
    sk_raw = _strip_optional_skin(skin_key)
    marker = get_planet_identity_marker_profile(planet)
    marker_block = format_identity_markers_prompt_block(planet, marker, has_skin=bool(sk_raw))
    canon_v2 = get_planet_canon_v2(planet)
    canon_v2_block = build_planet_canon_prompt_fragment(planet)
    must_have = " | ".join(canon_v2.must_have)
    must_not = " | ".join(canon_v2.must_not_have)
    base = (
        f"{planet} planet-cat [CANON v1 base]: {canon.short_prompt_line} "
        f"This block is the immutable planet identity — keep recognizable across every scene and skin. "
        f"Archetype: {canon.role_archetype} "
        f"Silhouette: {canon.silhouette_notes} "
        f"Shape language: {canon.core_shape_language} "
        f"Palette: {canon.core_palette} "
        f"Face: {canon.facial_expression_language} "
        f"Body: {canon.body_language} "
        f"Signature props: {canon.signature_props} "
        f"Signature details: {canon.signature_details} "
        f"Emotional tone: {canon.emotional_tone} "
        f"Motion style: {canon.motion_style} "
        f"Visual priorities: {canon.visual_do} "
        f"Visual avoid: {canon.visual_avoid} "
        f"Recognizability rule: {canon.recognizability_rule} "
        f"{canon_v2_block} "
        f"{planet} must-have traits lock: {must_have} "
        f"{planet} must-not traits lock: {must_not}"
    )
    base_with_markers = f"{base} {marker_block}"
    if not sk_raw:
        return base_with_markers
    sk = get_character_skin(planet, sk_raw)
    overlay = (
        f" Archetype skin **{sk.display_name}** (OPTIONAL COSTUME OVERLAY ONLY — preserve the full [CANON v1 base] "
        f"and [IDENTITY MARKERS v1] sections above: same planet, base silhouette, emblem-zone placement cues, "
        f"signature props/details, and recognizability rule must remain readable; "
        f"skin enhances costume/scene hooks, never replaces the planet-cat core): "
        f"costume: {sk.costume_elements}. Props: {sk.prop_elements}. Body language: {sk.body_language}. "
        f"Scene hooks: {sk.scene_hooks}. Skin signature details: {sk.signature_details}. "
        f"Avoid for this skin: {sk.avoid_elements}."
    )
    return base_with_markers + overlay


def _moon_saturn_visual_correction_block(pa: str, pb: str, aspect_type: str, mode: str) -> str:
    """Moon square Saturn: arena-readable clash where Moon stays soft-force and Saturn stays structural—not Mars combat."""
    pair = {pa.lower(), pb.lower()}
    if pair != {"moon", "saturn"}:
        return ""
    if (aspect_type or "").strip().lower() != "square":
        return ""
    if (mode or "").strip().lower() != "tension":
        return ""
    return (
        "[MOON-SATURN VISUAL CORRECTION PATCH v1 - mandatory identity guard] "
        "Dynamic zodiac-arena conflict is OK here: this is softness versus structure, not a generic action-hero brawl or soft cat versus fire ninja. "
        "Moon attacks/defends with pillow strikes, moonlight waves, tidal pushes, protective defensive motion, emotional "
        "flinch/retreat/burst—soft but active force; Moon stays rounded, vulnerable, comfort-seeking, silver-lit, clutching pillow/blanket/soft cloth; "
        "may glance toward a small glowing cozy doorway/window as memory of past comfort. "
        "Saturn counters with stone blocks, freeze/frost fields, gravity presses, chain binds, gate slams, wall summons, stop gesture, "
        "time-lock, ruler-as-measure strike, heavy downward structural force—cold stone-and-iron judge/architect/guardian energy; upright, severe, emotionally reserved. "
        "Scene metaphor: a heavy stone gate of time and responsibility blocks the way back to comfort while Moon presses with soft waves. "
        "Checkpoint imagery: stone gate/wall/tower, chain, clock boundary line; Saturn props like ruler, key, hourglass, blank watch, architectural plan. "
        "Composition target: premium cinematic comic poster, strong silhouettes, dramatic arena-readable pressure via symbolism (not MMA). "
        "Palette target: cold stone-and-silver dominant palette with controlled warm memory glow only in background comfort cue. "
        "Saturn critical negatives: do NOT depict Saturn with flames, fire aura, martial weapons, ninja/fighter styling, "
        "reckless attack pose, reckless speed, or Mars-like aggression; do NOT let Saturn inherit Mars visual traits. "
        "Whole-scene hard negatives: no martial-arts duel choreography, no body-on-body brawl, no nunchucks; "
        "not cute nursery, not flat mascot, not 3D CGI figurine, not game render look. "
        "Read: Moon softer/more emotionally defensive, Saturn still/imposing/limiting through mass and time; vulnerability vs discipline."
    )


def _pair_flag_glyph_system_block(pa: str, pb: str) -> str:
    """System-wide cloth-integrated banner glyphs for the active planet pair (all modes)."""
    return format_pair_flag_glyph_system_block(pa, pb).strip()


def _prompt_choreography_middleware(
    req: CatstylePromptRequest, pa: str, pb: str, pair_guard: str
) -> str:
    """Aspect choreography + optional planet lexicon + Mars scene decouple; Moon/Saturn square adds dedicated guard."""
    blocks: list[str] = []
    if (req.mode or "").strip().lower() == "flow":
        blocks.append(_catstyle_flow_mode_visual_lock(req))
        blocks.append(_mercury_jupiter_flow_planetary_being_lock(req, pa, pb))
    blocks.append(_pair_flag_glyph_system_block(pa, pb))
    blocks.extend(
        [
            _aspect_choreography_block(req.aspect_type, req.mode),
            _planet_pair_action_language(pa, pb),
            _arena_composition_boost_block(req),
            _epic_arena_showdown_block(req, pa, pb),
            _mars_heavy_scene_style_decouple_block(req, pa, pb),
            pair_guard,
        ]
    )
    return " ".join(b for b in blocks if b).strip()


def _skin_animation_suffix(pa: str, pb: str, skin_a: str | None, skin_b: str | None) -> str:
    parts: list[str] = []
    if skin_a:
        sk = get_character_skin(pa, skin_a)
        parts.append(f"{pa} in {sk.display_name} skin")
    if skin_b:
        sk = get_character_skin(pb, skin_b)
        parts.append(f"{pb} in {sk.display_name} skin")
    if not parts:
        return ""
    return " Archetype overlays: " + "; ".join(parts) + "."


def _skin_carousel_suffix(skin_a: str | None, skin_b: str | None) -> str:
    if not skin_a and not skin_b:
        return ""
    return " Honor optional archetype skins on labeled planet-cats where specified (still Catstyle round bodies)."


def _supported_pairs_hint() -> str:
    deep = [" + ".join(sorted(k, key=str.lower)) for k in ASPECT_CAT_INTERACTIONS]
    return "Deep aspect library: " + "; ".join(sorted(deep)) + ". Plus 25 social/outer-to-personal transit seeds (transit_pair_seed_v0)."


def _pack_from_deep(
    pa: str,
    pb: str,
    req: CatstylePromptRequest,
    *,
    canon_a: PlanetCatCanon,
    canon_b: PlanetCatCanon,
    aspect_ix,
    skin_a: str | None,
    skin_b: str | None,
    render_prof: CatstyleRenderStyleProfile,
    template_middle: str = "",
    render_middle: str = "",
    render_negative_additions: list[str] | None = None,
) -> CatstylePromptPack:
    tension_scenes = list(aspect_ix.scene_ideas)
    comp_scenes = list(aspect_ix.compensation_scene_ideas)
    n = req.variants_count
    shot_roles = shot_roles_for_variant_indices(n, req.shot_mode)
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
    pair_guard = _moon_saturn_visual_correction_block(pa, pb, req.aspect_type, req.mode)
    choreo_block = _prompt_choreography_middleware(req, pa, pb, pair_guard)
    anim_skin = _skin_animation_suffix(pa, pb, skin_a, skin_b)

    image_prompts: list[str] = []
    for i in range(n):
        if req.mode == "tension":
            base_scene = tension_scenes[i % len(tension_scenes)]
        elif req.mode in ("compensation", "flow"):
            base_scene = comp_scenes[i % len(comp_scenes)]
            if i >= len(comp_scenes):
                base_scene = f"{base_scene} Constructive channel: {aspect_ix.constructive_channel}"
        else:
            pool = tension_scenes + comp_scenes
            base_scene = pool[i % len(pool)]

        shot_blk = format_hero_shot_prompt_block(
            shot_roles[i], flow_mode=(req.mode or "").strip().lower() == "flow"
        )
        shot_middle = (shot_blk + " ") if shot_blk else ""

        prompt = (
            f"{_image_prompt_opening_prefix(render_prof, mode=req.mode)} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"{choreo_block} "
            f"{template_middle}"
            f"{render_middle}"
            f"{shot_middle}"
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {aspect_ix.core_tension} "
            f"Constructive undertone available: {aspect_ix.constructive_channel}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = _animation_prompt_body(pa, pb, req.aspect_type, anim_skin, render_prof, mode=req.mode)

    rn = list(render_negative_additions or [])
    negative_prompt = _merge_negative_prompt(_NEGATIVE_BASE_CHUNKS, list(aspect_ix.avoid_list) + rn)

    carousel_idea = (
        f"Carousel outline (cover + {n} art slides): cover shows {pa}+{pb} round cats under stars with clear "
        f"{req.aspect_type} read; slides rotate through the variant scene beats without on-image text; "
        f"final slide leans into constructive channel: {aspect_ix.constructive_channel} "
        f"(props and poses only, catstyle rules unchanged).{_skin_carousel_suffix(skin_a, skin_b)}"
    ).strip()

    return CatstylePromptPack(
        image_prompts=image_prompts,
        animation_prompt=animation_prompt,
        negative_prompt=negative_prompt,
        carousel_idea=carousel_idea,
        image_prompt_shot_roles=shot_roles,
    )


def _pack_from_seed(
    pa: str,
    pb: str,
    req: CatstylePromptRequest,
    *,
    canon_a: PlanetCatCanon,
    canon_b: PlanetCatCanon,
    seed: CatstyleTransitPairSeed,
    skin_a: str | None,
    skin_b: str | None,
    render_prof: CatstyleRenderStyleProfile,
    template_middle: str = "",
    render_middle: str = "",
    render_negative_additions: list[str] | None = None,
) -> CatstylePromptPack:
    tension_scenes = list(seed.suggested_scene_angles)
    comp_scenes = [seed.constructive_channel, seed.visual_metaphor]
    n = req.variants_count
    shot_roles = shot_roles_for_variant_indices(n, req.shot_mode)
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
    pair_guard = _moon_saturn_visual_correction_block(pa, pb, req.aspect_type, req.mode)
    choreo_block = _prompt_choreography_middleware(req, pa, pb, pair_guard)
    anim_skin = _skin_animation_suffix(pa, pb, skin_a, skin_b)

    image_prompts: list[str] = []
    for i in range(n):
        if req.mode == "tension":
            base_scene = tension_scenes[i % len(tension_scenes)]
        elif req.mode in ("compensation", "flow"):
            base_scene = comp_scenes[i % len(comp_scenes)]
            if i >= len(comp_scenes):
                base_scene = f"{base_scene} Constructive channel: {seed.constructive_channel}"
        else:
            pool = tension_scenes + comp_scenes
            base_scene = pool[i % len(pool)]

        shot_blk = format_hero_shot_prompt_block(
            shot_roles[i], flow_mode=(req.mode or "").strip().lower() == "flow"
        )
        shot_middle = (shot_blk + " ") if shot_blk else ""

        prompt = (
            f"{_image_prompt_opening_prefix(render_prof, mode=req.mode)} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"{choreo_block} "
            f"{template_middle}"
            f"{render_middle}"
            f"{shot_middle}"
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {seed.core_tension} "
            f"Constructive undertone available: {seed.constructive_channel} "
            f"Visual metaphor: {seed.visual_metaphor}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = _animation_prompt_body(pa, pb, req.aspect_type, anim_skin, render_prof, mode=req.mode)

    rn = list(render_negative_additions or [])
    negative_prompt = _merge_negative_prompt(_NEGATIVE_BASE_CHUNKS, list(seed.avoid) + rn)

    carousel_idea = (
        f"Carousel outline (cover + {n} art slides): cover shows {pa}+{pb} round cats under stars with clear "
        f"{req.aspect_type} read; slides rotate through transit seed v0 scene angles without on-image text; "
        f"final slide leans into constructive channel: {seed.constructive_channel} "
        f"(props and poses only, catstyle rules unchanged).{_skin_carousel_suffix(skin_a, skin_b)}"
    ).strip()

    return CatstylePromptPack(
        image_prompts=image_prompts,
        animation_prompt=animation_prompt,
        negative_prompt=negative_prompt,
        carousel_idea=carousel_idea,
        image_prompt_shot_roles=shot_roles,
    )


def _pack_from_fallback(
    pa: str,
    pb: str,
    req: CatstylePromptRequest,
    *,
    canon_a: PlanetCatCanon,
    canon_b: PlanetCatCanon,
    outer: str,
    personal: str,
    skin_a: str | None,
    skin_b: str | None,
    render_prof: CatstyleRenderStyleProfile,
    template_middle: str = "",
    render_middle: str = "",
    render_negative_additions: list[str] | None = None,
) -> CatstylePromptPack:
    core = f"{outer} social rhythm meets {personal} everyday stakes—generic transit beat v0 (seed TBD)."
    constructive = f"Shared constructive beat: {outer} and {personal} negotiate one clear cartoon gesture."
    angles = [
        f"{outer} planet-cat looms with simple prop; {personal} planet-cat reacts with one readable emotion.",
        f"{personal} offers one minimal object; {outer} reframes it with one bold silhouette change.",
        "Tug-of-war over a single blank card—no readable text.",
        "Spotlight circle on floor; both cats negotiate rim with deadpan comedy.",
    ]
    tension_scenes = angles
    comp_scenes = [constructive, f"{outer} and {personal} co-build one tiny two-block tower."]
    avoid = ["gore", "real weapons", "readable text in frame", "photorealistic violence"]
    n = req.variants_count
    shot_roles = shot_roles_for_variant_indices(n, req.shot_mode)
    line_a = _planet_cat_line(pa, canon_a, skin_a)
    line_b = _planet_cat_line(pb, canon_b, skin_b)
    pair_guard = _moon_saturn_visual_correction_block(pa, pb, req.aspect_type, req.mode)
    choreo_block = _prompt_choreography_middleware(req, pa, pb, pair_guard)
    anim_skin = _skin_animation_suffix(pa, pb, skin_a, skin_b)

    image_prompts: list[str] = []
    for i in range(n):
        if req.mode == "tension":
            base_scene = tension_scenes[i % len(tension_scenes)]
        elif req.mode in ("compensation", "flow"):
            base_scene = comp_scenes[i % len(comp_scenes)]
            if i >= len(comp_scenes):
                base_scene = f"{base_scene} Constructive channel: {constructive}"
        else:
            pool = tension_scenes + comp_scenes
            base_scene = pool[i % len(pool)]

        shot_blk = format_hero_shot_prompt_block(
            shot_roles[i], flow_mode=(req.mode or "").strip().lower() == "flow"
        )
        shot_middle = (shot_blk + " ") if shot_blk else ""

        prompt = (
            f"{_image_prompt_opening_prefix(render_prof, mode=req.mode)} "
            f"Aspect type: {req.aspect_type}. "
            f"{line_a} "
            f"{line_b} "
            f"{choreo_block} "
            f"{template_middle}"
            f"{render_middle}"
            f"{shot_middle}"
            f"Scene beat: {base_scene} "
            f"Story tension (cartoon metaphor): {core} "
            f"Constructive undertone available: {constructive}"
        ).strip()
        image_prompts.append(prompt)

    animation_prompt = _animation_prompt_body(pa, pb, req.aspect_type, anim_skin, render_prof, mode=req.mode)

    rn = list(render_negative_additions or [])
    negative_prompt = _merge_negative_prompt(_NEGATIVE_BASE_CHUNKS, avoid + rn)

    carousel_idea = (
        f"Carousel outline (cover + {n} art slides): cover shows {pa}+{pb} round cats under stars with clear "
        f"{req.aspect_type} read; generic outer-to-personal fallback beats; "
        f"final slide leans into: {constructive} (props and poses only).{_skin_carousel_suffix(skin_a, skin_b)}"
    ).strip()

    return CatstylePromptPack(
        image_prompts=image_prompts,
        animation_prompt=animation_prompt,
        negative_prompt=negative_prompt,
        carousel_idea=carousel_idea,
        image_prompt_shot_roles=shot_roles,
    )


def generate_catstyle_prompt_pack(req: CatstylePromptRequest) -> CatstylePromptPack:
    """Build prompts from deep aspect library, transit pair seeds, or generic outer-to-personal fallback."""
    pa = normalize_planet_name(req.planet_a)
    pb = normalize_planet_name(req.planet_b)
    canon_a = get_planet_canon(pa)
    canon_b = get_planet_canon(pb)
    skin_a = _strip_optional_skin(req.skin_a)
    skin_b = _strip_optional_skin(req.skin_b)
    _validate_skins_for_pair(pa, pb, skin_a, skin_b)

    world_block, scene_block, world_prof, scene_prof = _resolve_world_scene_blocks(req, pa, pb)
    template_middle = _join_world_scene_middle(world_block, scene_block)

    render_prof, render_prof_dict, render_middle = _resolve_render_style(req)
    render_neg = list(render_prof.negative_prompt_additions)

    aspect_ix = get_aspect_interaction(pa, pb)
    if aspect_ix is not None:
        pack = _pack_from_deep(
            pa,
            pb,
            req,
            canon_a=canon_a,
            canon_b=canon_b,
            aspect_ix=aspect_ix,
            skin_a=skin_a,
            skin_b=skin_b,
            render_prof=render_prof,
            template_middle=template_middle,
            render_middle=render_middle,
            render_negative_additions=render_neg,
        )
    else:
        oriented = orient_outer_personal(pa, pb)
        if oriented is None:
            raise ValueError(
                f"No Catstyle content for {pa} + {pb}: not a social/outer-to-personal transit pair. {_supported_pairs_hint()}"
            )

        outer, personal = oriented
        seed = get_transit_pair_seed(outer, personal)
        if seed is not None:
            pack = _pack_from_seed(
                pa,
                pb,
                req,
                canon_a=canon_a,
                canon_b=canon_b,
                seed=seed,
                skin_a=skin_a,
                skin_b=skin_b,
                render_prof=render_prof,
                template_middle=template_middle,
                render_middle=render_middle,
                render_negative_additions=render_neg,
            )
        else:
            pack = _pack_from_fallback(
                pa,
                pb,
                req,
                canon_a=canon_a,
                canon_b=canon_b,
                outer=outer,
                personal=personal,
                skin_a=skin_a,
                skin_b=skin_b,
                render_prof=render_prof,
                template_middle=template_middle,
                render_middle=render_middle,
                render_negative_additions=render_neg,
            )

    # Prompt budget guard: compact any over-budget image prompts deterministically before returning.
    data = pack.model_dump(mode="json")
    prompts = [str(p) for p in (data.get("image_prompts") or [])]
    data["image_prompts"] = [_compact_prompt_to_budget(p) for p in prompts]
    pack = CatstylePromptPack.model_validate(data)

    pack = _attach_template_profiles(
        pack,
        world_template_profile=world_prof,
        scene_template_profile=scene_prof,
        render_style_profile=render_prof_dict,
    )
    pack = _finalize_pack_with_art_direction(pack, req, pa, pb, skin_a, skin_b)
    # Re-apply budget guard after premium art-direction append (can increase prompt length).
    data2 = pack.model_dump(mode="json")
    prompts2 = [str(p) for p in (data2.get("image_prompts") or [])]
    data2["image_prompts"] = [_compact_prompt_to_budget(p) for p in prompts2]
    return CatstylePromptPack.model_validate(data2)


def _finalize_pack_with_art_direction(
    pack: CatstylePromptPack,
    req: CatstylePromptRequest,
    pa: str,
    pb: str,
    skin_a: str | None,
    skin_b: str | None,
) -> CatstylePromptPack:
    if not req.premium_art_direction:
        return pack
    art_profile = build_catstyle_art_direction_profile(
        editorial_profile=req.editorial_profile,
        mode=req.mode,
        planet_a=pa,
        planet_b=pb,
        skin_a=skin_a,
        skin_b=skin_b,
    )
    return apply_art_direction_to_prompt_pack(pack, art_profile)


__all__ = [
    "generate_catstyle_prompt_pack",
    "normalize_planet_name",
]
