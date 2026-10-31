"""Stores what the Centrale Canine site of a breeding shows: its cover photo and its gallery, dated."""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from models.breeder import Breeder
from services.collectors.scc_sites import RawSccSite


@dataclass
class SccSiteIngestionSummary:
    """What a run of the sites changed in the database."""

    seen_count: int = 0
    updated_breeder_ids: list[int] = field(default_factory=list)


class SccSiteIngestionService:
    """Writes the photos of each site on its breeder, and dates the reading so that the site rests a month."""

    def ingest(self, db: Session, sites: list[RawSccSite], now: datetime) -> SccSiteIngestionSummary:
        """
        Store a run: each site read refreshes the photos of its breeder; a site gone keeps the photos known
        and is dated like the others, so that it is not asked again before a month.

        Args:
            db: Database session; committed at the end.
            sites: The sites read by the collector.
            now: Run time, naive UTC.

        Returns:
            The summary of the run.
        """
        summary = SccSiteIngestionSummary()
        for site in sites:
            breeder = db.get(Breeder, site.breeder_id)
            if breeder is None:
                continue
            summary.seen_count += 1
            breeder.scc_site_seen_at = now
            if site.is_missing:
                continue
            photos = list(site.photo_urls)
            has_changed = breeder.scc_site_cover_url != site.cover_photo_url or list(breeder.scc_site_photos) != photos
            breeder.scc_site_cover_url = site.cover_photo_url
            breeder.scc_site_photos = photos
            if has_changed:
                summary.updated_breeder_ids.append(breeder.id)
        db.commit()
        return summary


scc_site_ingestion_service = SccSiteIngestionService()
