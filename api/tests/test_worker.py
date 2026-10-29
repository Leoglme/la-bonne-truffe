"""The collection worker: one hourly job per source this machine collects, the evening digests and the reminders."""

from enums.listing_source import ListingSource
from worker import CollectionWorker


def test_every_collected_source_has_its_hourly_job() -> None:
    scheduler = CollectionWorker(frozenset(ListingSource)).build_scheduler()

    assert {job.id for job in scheduler.get_jobs()} == {
        "collect_centrale_canine",
        "collect_chiens_de_france",
        "collect_chiots_de_france",
        "send_evening_digests",
        "send_follow_up_reminders",
    }


def test_a_skipped_source_has_no_job() -> None:
    worker = CollectionWorker(frozenset({ListingSource.CHIENS_DE_FRANCE, ListingSource.CHIOTS_DE_FRANCE}))

    assert {job.id for job in worker.build_scheduler().get_jobs()} == {
        "collect_chiens_de_france",
        "collect_chiots_de_france",
        "send_evening_digests",
        "send_follow_up_reminders",
    }
