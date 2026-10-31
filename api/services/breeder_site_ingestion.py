"""Stores what the sites of the breeders on Chiens de France bring: listings, reproducers, facts on the breeding."""

from datetime import datetime

from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.breeder import Breeder
from services.breeder_search_text import BreederSearchText
from services.collectors.chiens_de_france_sites import SiteCollection, SiteCollectionPlan
from services.dog_ingestion import DogIngestionService
from services.listing_ingestion import IngestionSummary, listing_ingestion_service


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
            breeder.search_text = BreederSearchText.build(breeder)
        db.commit()
        return summary


breeder_site_ingestion_service = BreederSiteIngestionService()
