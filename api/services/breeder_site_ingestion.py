"""Stores what the sites of the breeders on Chiens de France bring: listings, reproducers, facts on the breeding."""

import re
from datetime import datetime

from sqlalchemy.orm import Session

from core.text import without_accents
from enums.listing_source import ListingSource
from enums.social_link_origin import SocialLinkOrigin
from models.breeder import Breeder
from services.breeder_search_text import BreederSearchText
from services.breeder_social_links import BreederSocialLinks
from services.collectors.chiens_de_france_sites import SiteCollection, SiteCollectionPlan
from services.collectors.raw_dog import RawBreederSiteFacts, RawSiteDirectoryEntry
from services.collectors.social_link_parser import FACEBOOK_ACCOUNT, INSTAGRAM_ACCOUNT, YOUTUBE_ACCOUNT
from services.dog_ingestion import DogIngestionService
from services.listing_ingestion import IngestionSummary, listing_ingestion_service

NAME_WORD_PATTERN = re.compile(r"[a-z0-9]+")
NAME_WORDS_LEFT_OUT: frozenset[str] = frozenset(
    {"sarl", "earl", "eurl", "sas", "sasu", "scea", "gaec", "ei", "elevage", "chenil", "de", "du", "des", "d", "la"}
    | {"le", "les", "l", "et", "au", "aux"}
)


class BreederSiteIngestionService:
    """Ties what a breeder's site says to the breeder the plan read it for."""

    def ingest(
        self, db: Session, plan: SiteCollectionPlan, collection: SiteCollection, now: datetime
    ) -> IngestionSummary:
        """
        Store a run: the future litters and the puppies for sale as Chiens de France listings (the same ones the
        main site shows), the reproducers as dogs of the breeder, and the facts on the breeding.

        No listing is deactivated by this run: a litter gone from a site leaves by its other sources.

        Args:
            db: Database session; committed at the end.
            plan: The sites read, each with its breeder.
            collection: What the collector brought back.
            now: Run time, naive UTC.

        Returns:
            The summary of the run: the listings by id, the dogs by count.
        """
        breeder_ids_by_source_id = {site.breeder_source_id: site.breeder_id for site in plan.sites}
        summary = listing_ingestion_service.ingest(
            db, ListingSource.CHIENS_DE_FRANCE, collection.listings, set(), now, breeder_ids_by_source_id
        )
        for raw_dog in collection.dogs:
            dog, is_new = DogIngestionService.upsert(db, raw_dog, now)
            breeder_id = breeder_ids_by_source_id.get(raw_dog.breeder_source_id or "")
            if breeder_id is not None:
                dog.breeder_id = breeder_id
            if is_new:
                summary.new_breeder_or_dog_count += 1
        summary.seen_count += len(collection.dogs)
        for facts in collection.site_facts:
            breeder_id = breeder_ids_by_source_id.get(facts.breeder_source_id)
            breeder = db.get(Breeder, breeder_id) if breeder_id is not None else None
            if breeder is None:
                continue
            breeder.chiens_de_france_site_url = facts.site_url
            breeder.cover_photo_url = facts.cover_photo_url or breeder.cover_photo_url
            if facts.breeding_females_count is not None:
                breeder.breeding_females_count = facts.breeding_females_count
            if facts.litters_last_year_count is not None:
                breeder.litters_last_year_count = facts.litters_last_year_count
            if facts.registered_on is not None:
                breeder.chiens_de_france_registered_on = facts.registered_on
            self._apply_reading(breeder, facts, now)
            breeder.search_text = BreederSearchText.build(breeder)
        db.commit()
        return summary

    def link_directory_sites(self, db: Session, entries: list[RawSiteDirectoryEntry]) -> list[int]:
        """
        Give a breeder the site a regional list of Chiens de France names for it: same postal code and the same
        name once legal forms and articles are left out (« Sarl La Ferme Des Saules » is « La Ferme des Saules »).
        A site already known, or a name two breeders of the postal code could bear, links nothing.

        Args:
            db: Database session; committed when a breeder got its site.
            entries: The breeder sites the lists gave.

        Returns:
            The breeders that got a site, in list order.
        """
        breeders = db.query(Breeder).order_by(Breeder.id).all()
        known_site_urls = {
            (breeder.chiens_de_france_site_url or "").rstrip("/")
            for breeder in breeders
            if breeder.chiens_de_france_site_url
        }
        linked_breeder_ids: list[int] = []
        for entry in entries:
            if entry.site_url in known_site_urls or entry.zip_code is None:
                continue
            entry_words = self._name_words(entry.name)
            candidates = [
                breeder
                for breeder in breeders
                if breeder.zip_code == entry.zip_code
                and breeder.chiens_de_france_site_url is None
                and any(
                    self._name_words(name) == entry_words
                    for name in (breeder.display_name, breeder.affix)
                    if name and entry_words
                )
            ]
            if len(candidates) != 1:
                continue
            breeder = candidates[0]
            breeder.chiens_de_france_site_url = entry.site_url
            breeder.search_text = BreederSearchText.build(breeder)
            known_site_urls.add(entry.site_url)
            linked_breeder_ids.append(breeder.id)
        if linked_breeder_ids:
            db.commit()
        return linked_breeder_ids

    @staticmethod
    def _apply_reading(breeder: Breeder, facts: RawBreederSiteFacts, now: datetime) -> None:
        """
        Keep what the reading of a site says beyond its listings: its social accounts, which only fill an empty
        place, the litters born this year when their page was read, and the time of the reading.

        Args:
            breeder: The breeder of the site.
            facts: What the site said.
            now: Run time, naive UTC.
        """
        for account, address in (
            (FACEBOOK_ACCOUNT, facts.facebook_url),
            (INSTAGRAM_ACCOUNT, facts.instagram_url),
            (YOUTUBE_ACCOUNT, facts.youtube_url),
        ):
            BreederSocialLinks.keep(breeder, account, address, SocialLinkOrigin.BREEDER_SITE)
        if facts.litters_born is not None:
            breeder.chiens_de_france_litters = [
                {
                    "birth_date": litter.birth_date.isoformat(),
                    "sire_name": litter.sire_name or "",
                    "dam_name": litter.dam_name or "",
                }
                for litter in facts.litters_born
            ]
        breeder.chiens_de_france_site_seen_at = now

    @staticmethod
    def _name_words(name: str) -> frozenset[str]:
        """
        The words that make a breeding name, legal forms and articles left out.

        Args:
            name: « Sarl La Ferme Des Saules », « Du Moulin des Saules ».

        Returns:
            The words, lower case and without accents (« ferme », « saules »).
        """
        words = NAME_WORD_PATTERN.findall(without_accents(name).lower())
        return frozenset(word for word in words if word not in NAME_WORDS_LEFT_OUT)


breeder_site_ingestion_service = BreederSiteIngestionService()
