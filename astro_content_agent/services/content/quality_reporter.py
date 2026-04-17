from __future__ import annotations

from dataclasses import dataclass, field

from astro_content_agent.services.content.anti_repeat import AntiRepeatContext


@dataclass(frozen=True)
class HookQualityReport:
    """Quality assessment for a single hook string."""

    hook: str
    is_weak: bool
    is_repetitive: bool

    @property
    def verdict(self) -> str:
        """Human-readable verdict: 'OK', 'WEAK', 'REPETITIVE', or combined."""
        issues: list[str] = []
        if self.is_weak:
            issues.append("WEAK opener")
        if self.is_repetitive:
            issues.append("REPETITIVE (matches recent)")
        return " | ".join(issues) if issues else "OK"

    @property
    def passed(self) -> bool:
        return not self.is_weak and not self.is_repetitive


@dataclass(frozen=True)
class PostDraftReport:
    """Quality report for a generated post draft."""

    draft_id: str
    title: str
    hook: str
    caption: str
    cta: str
    voice_note: str | None
    hashtags: list[str]
    hook_quality: HookQualityReport


@dataclass(frozen=True)
class ReelDraftReport:
    """Quality report for a generated reel draft."""

    draft_id: str
    hook_0_3s: str
    hook: str
    reel_type: str
    script: str
    on_screen_text: list[str]
    cta: str
    hook_quality: HookQualityReport


class DraftQualityReporter:
    """Produces quality reports for generated drafts without any AI calls.

    Used by the local calibration script (``generate_sample_outputs.py``) and
    testable independently of the AI layer.
    """

    def assess_hook(self, hook: str, recent_hooks: list[str]) -> HookQualityReport:
        """Assess a single hook string against recent hook history."""
        ctx = AntiRepeatContext(recent_hooks=recent_hooks)
        return HookQualityReport(
            hook=hook,
            is_weak=ctx.is_hook_weak(hook),
            is_repetitive=ctx.is_hook_repetitive(hook),
        )

    def assess_post_draft(
        self,
        draft_id: str,
        payload: dict,
        recent_hooks: list[str] | None = None,
    ) -> PostDraftReport:
        """Build a quality report for a post draft payload dict."""
        hook = payload.get("hook", "")
        quality = self.assess_hook(hook, recent_hooks or [])
        return PostDraftReport(
            draft_id=draft_id,
            title=payload.get("title", ""),
            hook=hook,
            caption=payload.get("caption", ""),
            cta=payload.get("cta", ""),
            voice_note=payload.get("voice_note"),
            hashtags=payload.get("hashtags", []),
            hook_quality=quality,
        )

    def assess_reel_draft(
        self,
        draft_id: str,
        payload: dict,
        recent_hooks: list[str] | None = None,
    ) -> ReelDraftReport:
        """Build a quality report for a reel draft payload dict."""
        hook_0_3s = payload.get("hook_0_3s", "")
        hook = payload.get("hook", "")
        # Assess the scroll-stopper hook (hook_0_3s if available, else hook)
        quality = self.assess_hook(hook_0_3s or hook, recent_hooks or [])
        return ReelDraftReport(
            draft_id=draft_id,
            hook_0_3s=hook_0_3s,
            hook=hook,
            reel_type=payload.get("reel_type", ""),
            script=payload.get("script", ""),
            on_screen_text=payload.get("on_screen_text", []),
            cta=payload.get("cta", ""),
            hook_quality=quality,
        )

    def format_post_report(self, report: PostDraftReport) -> str:
        """Return a human-readable text block for a post report."""
        lines = [
            f"POST DRAFT  {report.draft_id}",
            f"  Title    : {report.title}",
            f"  Hook     : {report.hook}",
            f"  Hook QA  : {report.hook_quality.verdict}",
            f"  Caption  :\n    {report.caption[:300].replace(chr(10), chr(10) + '    ')}",
            f"  CTA      : {report.cta}",
            f"  Hashtags : {' '.join(report.hashtags[:8])}",
        ]
        if report.voice_note:
            lines.append(f"  Voice note: {report.voice_note}")
        return "\n".join(lines)

    def format_reel_report(self, report: ReelDraftReport) -> str:
        """Return a human-readable text block for a reel report."""
        ost = " / ".join(report.on_screen_text[:4])
        lines = [
            f"REEL DRAFT  {report.draft_id}",
            f"  Type     : {report.reel_type}",
            f"  Hook 0-3s: {report.hook_0_3s}",
            f"  Hook QA  : {report.hook_quality.verdict}",
            f"  Hook full: {report.hook}",
            f"  Script   :\n    {report.script[:300].replace(chr(10), chr(10) + '    ')}",
            f"  On-screen: {ost}",
            f"  CTA      : {report.cta}",
        ]
        return "\n".join(lines)
