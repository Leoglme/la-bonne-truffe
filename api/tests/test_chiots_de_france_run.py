"""A Chiots de France run beside the other sources: its litter ads join the litters they already know."""

from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.litter_group import LitterGroup
from seeders.run_seeders import SeederRunner
from services.collection_runner import collection_runner
from services.matching.snapshot_builder import LitterSnapshotBuilder
from tests.centrale_canine_pages import collector_serving, load_recorded_pages
from tests.chiens_de_france_pages import chiens_de_france_collector_serving
from tests.chiots_de_france_pages import chiots_de_france_collector_serving
from tests.stored_listings import listing_of


def test_litter_ad_joins_the_litter_declared_and_advertised_puppy_by_puppy(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    collection_runner.run_html_source(db, ListingSource.CHIENS_DE_FRANCE, chiens_de_france_collector_serving())

    report = collection_runner.run_html_source(db, ListingSource.CHIOTS_DE_FRANCE, chiots_de_france_collector_serving())

    litter_ad = listing_of(db, "annonce-486970")
    declared_litter = listing_of(db, "4320820")
    assert report.source_run.status == "ok"
    assert (report.source_run.listings_seen, report.source_run.listings_new) == (2, 2)
    assert litter_ad.breeder_id == declared_litter.breeder_id
    assert litter_ad.litter_group_id == declared_litter.litter_group_id
    assert listing_of(db, "chiot-2199887").litter_group_id == declared_litter.litter_group_id
    assert report.grouping.new_group_ids == [listing_of(db, "annonce-487726").litter_group_id]


def test_declared_sexes_win_over_the_puppies_still_offered_even_when_the_ad_came_first(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_html_source(db, ListingSource.CHIOTS_DE_FRANCE, chiots_de_france_collector_serving())
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    group = db.get(LitterGroup, listing_of(db, "4320820").litter_group_id)
    assert group is not None
    snapshot = LitterSnapshotBuilder.build(db, group)

    assert listing_of(db, "annonce-486970").litter_group_id == group.id
    assert snapshot is not None
    assert (snapshot.male_count, snapshot.female_count) == (3, 1)
    assert snapshot.price_cents == 140000
