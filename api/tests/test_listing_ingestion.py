"""ListingIngestionService: the breeder of a listing from one run to the next."""

from dataclasses import replace

from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_source import ListingSource
from models.breed import Breed
from models.breeder import Breeder
from models.listing import Listing
from seeders.run_seeders import SeederRunner
from services.collectors.chiots_de_france import ChiotsDeFranceCollector, ListedLitterAd
from services.collectors.raw_listing import RawBreeder
from services.listing_ingestion import listing_ingestion_service
from tests.chiots_de_france_pages import recorded_page

PRIVATE_SELLER_AD = ListedLitterAd(
    "annonce-487726",
    "https://www.chiots-de-france.com/detail-annonce-cocker-spaniel-anglais_487726_5.html",
    "72",
    is_lof=True,
)


def test_breeder_known_only_by_its_ad_stays_the_same_from_one_run_to_the_next(db: Session) -> None:
    SeederRunner.run(db)
    breed = db.query(Breed).one()
    ad = ChiotsDeFranceCollector.parse_ad_page(recorded_page("ad_487726.html"), breed.id, PRIVATE_SELLER_AD)
    private_seller_ad = replace(ad, breeder=RawBreeder(source_id="elevage-f", zip_code="72000", city="Le Mans"))

    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [private_seller_ad], {"72"}, naive_utc_now())
    first_breeder_id = db.query(Listing).one().breeder_id
    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [private_seller_ad], {"72"}, naive_utc_now())

    assert first_breeder_id is not None
    assert db.query(Listing).one().breeder_id == first_breeder_id
    assert db.query(Breeder).count() == 1
