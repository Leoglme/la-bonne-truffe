"""Where a litter is, and the site its page links, when its listings say less than its breeder."""

from enums.listing_source import ListingSource
from models.breeder import Breeder
from models.listing import Listing
from services.litter_query_service import LitterQueryService
from services.matching.snapshot_builder import LitterSnapshotBuilder

SITE_URL = "https://elevage-a.chiens-de-france.com"


def test_a_litter_only_its_breeders_site_shows_is_in_the_department_of_its_breeder() -> None:
    breeder = Breeder(affix="Du Clos de test A", department_code="56")
    site_ad = Listing(source=ListingSource.CHIENS_DE_FRANCE, is_active=True, department_code=None)
    declared_litter = Listing(source=ListingSource.CENTRALE_CANINE, is_active=True, department_code="35")

    assert LitterSnapshotBuilder.department_code_of([site_ad], breeder) == "56"
    assert LitterSnapshotBuilder.department_code_of([site_ad, declared_litter], breeder) == "35"
    assert LitterSnapshotBuilder.department_code_of([site_ad], None) is None


def test_the_page_of_a_litter_links_the_chiens_de_france_site_of_a_breeder_without_website() -> None:
    breeder = Breeder(id=1, affix="Du Clos de test A", chiens_de_france_site_url=SITE_URL)
    breeder_with_website = Breeder(id=2, website="https://www.elevage-a.test", chiens_de_france_site_url=SITE_URL)

    assert LitterQueryService._breeder(breeder, "cocker-spaniel-anglais").website == (
        f"{SITE_URL}/cocker-spaniel-anglais"
    )
    assert LitterQueryService._breeder(breeder_with_website, "cocker-spaniel-anglais").website == (
        "https://www.elevage-a.test"
    )
