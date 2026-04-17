from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import ContentPlan


class ContentPillarBalancer:
    """Tracks content pillar usage over recent content plans and suggests underused pillars.

    Enables the strategy planner to spread topics evenly across the brand's
    content pillars rather than defaulting to the same pillar every day.
    """

    def get_recent_pillar_usage(
        self,
        db: Session,
        brand_profile_id: str,
        *,
        days: int = 14,
    ) -> dict[str, int]:
        """Return a count of each content pillar used in recent content plans.

        Looks for ``content_pillar`` fields inside each plan's ``payload.items``.
        Returns an empty dict if no pillar data exists (e.g. all pre-Phase-10 plans).
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(ContentPlan)
            .where(
                ContentPlan.brand_profile_id == brand_profile_id,
                ContentPlan.created_at >= cutoff,
            )
            .order_by(ContentPlan.created_at.desc())
        )
        plans = list(db.execute(stmt).scalars().all())

        usage: Counter[str] = Counter()
        for plan in plans:
            payload = plan.payload or {}
            for item in payload.get("items", []):
                pillar = item.get("content_pillar")
                if pillar:
                    usage[pillar] += 1

        return dict(usage)

    def get_underused_pillar(
        self,
        available_pillars: list[str],
        recent_usage: dict[str, int],
    ) -> str | None:
        """Return the pillar from *available_pillars* with the lowest recent usage.

        Returns None if *available_pillars* is empty.
        """
        if not available_pillars:
            return None
        return min(available_pillars, key=lambda p: recent_usage.get(p, 0))

    def to_prompt_hint(
        self,
        recent_usage: dict[str, int],
        available_pillars: list[str],
    ) -> str:
        """Format pillar balance data as a hint for the strategist prompt."""
        if not available_pillars:
            return "No content pillars configured for this brand."

        lines = ["Content pillar usage over the past 14 days (balance these across slots):"]
        for pillar in available_pillars:
            count = recent_usage.get(pillar, 0)
            lines.append(f"  {pillar}: {count} recent use(s)")

        underused = self.get_underused_pillar(available_pillars, recent_usage)
        if underused:
            lines.append(f"Recommended: prioritise '{underused}' pillar (least used recently).")

        return "\n".join(lines)
