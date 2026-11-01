"""The collection worker: one hourly job per source this machine collects, the digests, the reminders, the silence watch, the nightly housekeeping."""

from enums.listing_source import ListingSource
from worker import CollectionWorker


def test_every_collected_source_has_its_hourly_job() -> None:
    scheduler = CollectionWorker(frozenset(ListingSource), relayed_sources=frozenset()).build_scheduler()

    assert {job.id for job in scheduler.get_jobs()} == {
        "collect_centrale_canine",
        "collect_scc_dogs",
        "collect_chiens_de_france",
        "collect_chiots_de_france",
        "collect_whoof",
        "collect_coeur_de_cocker",
        "collect_chiens_de_france_sites",
        "collect_scc_breeders",
        "collect_scc_sites",
        "send_evening_digests",
        "send_follow_up_reminders",
        "purge_old_listing_data",
    }


def test_the_breeder_sites_are_read_in_the_morning_and_in_the_evening() -> None:
    scheduler = CollectionWorker(frozenset(ListingSource), relayed_sources=frozenset()).build_scheduler()

    job = scheduler.get_job("collect_chiens_de_france_sites")

    assert job is not None
    assert str(job.trigger) == "cron[hour='6,18', minute='40']"


def test_a_skipped_source_has_no_job() -> None:
    worker = CollectionWorker(
        frozenset({ListingSource.CHIENS_DE_FRANCE, ListingSource.CHIOTS_DE_FRANCE}), relayed_sources=frozenset()
    )

    assert {job.id for job in worker.build_scheduler().get_jobs()} == {
        "collect_chiens_de_france",
        "collect_chiots_de_france",
        "send_evening_digests",
        "send_follow_up_reminders",
        "purge_old_listing_data",
    }


def test_a_source_relayed_by_the_desktop_app_is_watched_for_silence() -> None:
    worker = CollectionWorker(
        frozenset({ListingSource.CHIENS_DE_FRANCE}), relayed_sources=frozenset({ListingSource.CENTRALE_CANINE})
    )

    assert {job.id for job in worker.build_scheduler().get_jobs()} == {
        "collect_chiens_de_france",
        "send_evening_digests",
        "send_follow_up_reminders",
        "alert_silent_sources",
        "purge_old_listing_data",
    }
