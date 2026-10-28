"""A Chiens de France run after a Centrale Canine run: its ads join the litters already known."""

from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.litter_group import LitterGroup
from seeders.run_seeders import SeederRunner
from services.collection_runner import collection_runner
from services.matching.snapshot_builder import LitterSnapshotBuilder
from tests.centrale_canine_pages import collector_serving, load_recorded_pages
from tests.chiens_de_france_pages import chiens_de_france_collector_serving
from tests.stored_listings import listing_of


def test_puppy_and_litter_to_come_join_the_centrale_canine_litters_of_their_breeder(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    report = collection_runner.run_html_source(db, ListingSource.CHIENS_DE_FRANCE, chiens_de_france_collector_serving())

    puppy = listing_of(db, "chiot-2199887")
    declared_litter = listing_of(db, "4320820")
    assert report.source_run.status == "ok"
    assert (report.source_run.listings_seen, report.source_run.listings_new) == (2, 2)
    assert report.grouping.new_group_ids == []
    assert puppy.breeder_id == declared_litter.breeder_id
    assert puppy.litter_group_id == declared_litter.litter_group_id
    assert listing_of(db, "saillie-494882").litter_group_id == listing_of(db, "4337070").litter_group_id


def test_joined_litter_keeps_its_declared_sexes_and_gains_the_price_of_the_ad(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    collection_runner.run_html_source(db, ListingSource.CHIENS_DE_FRANCE, chiens_de_france_collector_serving())

    group = db.get(LitterGroup, listing_of(db, "4320820").litter_group_id)
    assert group is not None
    snapshot = LitterSnapshotBuilder.build(db, group)

    assert snapshot is not None
    assert (snapshot.male_count, snapshot.female_count) == (3, 1)
    assert snapshot.price_cents == 140000
