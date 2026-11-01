"""Stores what the Centrale Canine site of a breeding shows: its photos and its links, dated."""

from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from enums.social_link_origin import SocialLinkOrigin
from models.breeder import Breeder
from services.breeder_search_text import BreederSearchText
from services.breeder_social_links import BreederSocialLinks
from services.collectors.html_source import BREEDER_SITE_HOST_SUFFIX
from services.collectors.scc_sites import RawSccSite
from services.collectors.social_link_parser import FACEBOOK_ACCOUNT, INSTAGRAM_ACCOUNT, YOUTUBE_ACCOUNT
from services.stored_value import known_or_current


@dataclass
class SccSiteIngestionSummary:
    """What a run of the sites changed in the database."""

    seen_count: int = 0
    updated_breeder_ids: list[int] = field(default_factory=list)


class SccSiteIngestionService:
    """Writes the photos and the links of each site on its breeder, and dates the reading so that the site rests."""

    def ingest(self, db: Session, sites: list[RawSccSite], now: datetime) -> SccSiteIngestionSummary:
        """
        Store a run: each site read refreshes the photos of its breeder and the links it declares (a social
        account the site no longer declares stays known); a site gone keeps what is known and is dated like
        the others, so that it is not asked again before a month.

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
            before = self._stored_values(breeder)
            breeder.scc_site_cover_url = site.cover_photo_url
            breeder.scc_site_photos = list(site.photo_urls)
            for account, address in (
                (FACEBOOK_ACCOUNT, site.links.facebook_url),
                (INSTAGRAM_ACCOUNT, site.links.instagram_url),
                (YOUTUBE_ACCOUNT, site.links.youtube_url),
            ):
                BreederSocialLinks.keep(breeder, account, address, SocialLinkOrigin.CENTRALE_CANINE)
            self._apply_other_site(breeder, site.links.other_site_url)
            breeder.search_text = BreederSearchText.build(breeder)
            if self._stored_values(breeder) != before:
                summary.updated_breeder_ids.append(breeder.id)
        db.commit()
        return summary

    @staticmethod
    def _apply_other_site(breeder: Breeder, other_site_url: str | None) -> None:
        """
        Keep the other site a breeding declares: hosted by Chiens de France, it is the site the daily runs read
        for its photos and its litters; elsewhere, it is the website of the breeding.

        Args:
            breeder: The breeder to update.
            other_site_url: « mon autre site », or None when the site declares none.
        """
        if other_site_url is None:
            return
        host = urlparse(other_site_url).netloc.lower()
        if host.endswith(BREEDER_SITE_HOST_SUFFIX):
            site_url = f"https://{host}"
            breeder.chiens_de_france_site_url = known_or_current(site_url, breeder.chiens_de_france_site_url)
            breeder.website = known_or_current(site_url, breeder.website)
            return
        breeder.website = known_or_current(other_site_url, breeder.website)

    @staticmethod
    def _stored_values(breeder: Breeder) -> tuple[object, ...]:
        """
        What a site run may change on a breeder, to tell whether it did.

        Args:
            breeder: The breeder.

        Returns:
            The values compared before and after the run.
        """
        return (
            breeder.scc_site_cover_url,
            list(breeder.scc_site_photos),
            breeder.facebook_url,
            breeder.instagram_url,
            breeder.youtube_url,
            breeder.website,
            breeder.chiens_de_france_site_url,
        )


scc_site_ingestion_service = SccSiteIngestionService()
