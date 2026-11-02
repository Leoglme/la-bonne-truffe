"""The own websites of the breedings: the photo each puts forward, read once, and shown when no site gives a cover."""

from collections.abc import Callable
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from selectolax.lexbor import LexborHTMLParser
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from migrations import add_breeder_links_found_by_hand
from models.breeder import Breeder
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.breeder_link_service import BreederLinkService
from services.breeder_website_service import BreederWebsiteService
from services.collectors.polite_http_client import SourcePageMissingError, SourceReadError
from services.collectors.site_image_parser import SiteImageParser

WEBSITE_URL = "https://www.ferme-des-tests.fr/"
READ_AT = datetime(2026, 11, 2, 7, 25)
SHARED_PHOTO_PAGE = """
<html><head>
  <meta property="og:image" content="/wp-content/uploads/2024/05/logo-ferme.png">
  <meta name="twitter:image" content="/wp-content/uploads/2024/05/portee-mai.jpg">
</head><body><img src="/wp-content/uploads/2024/05/chiots.jpg"></body></html>
"""
PHOTOS_ONLY_PAGE = """
<html><body>
  <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
  <img src="/images/logo-elevage.jpg">
  <img src="/images/patte.png" width="512" height="512">
  <img src="/images/vignette.jpg" width="120" height="80">
  <img data-src="https://static.wixstatic.com/media/603aed_f7d1~mv2.jpg/v1/fill/w_147,h_135,al_c/chienne.jpg">
</body></html>
"""


@pytest.fixture
def seeded(db: Session) -> dict[str, str]:
    """Seed the reference data, the user and the starting profile; return the bearer header."""
    SeederRunner.run(db)
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def breeding(db: Session, **columns: object) -> Breeder:
    """A breeder of Liffré, in a department of the starting profile."""
    breeder = Breeder(display_name="La Ferme des Tests", zip_code="35340", city="Liffré", department_code="35")
    for name, value in columns.items():
        setattr(breeder, name, value)
    db.add(breeder)
    db.commit()
    return breeder


def pages_reader(pages: dict[str, str | Exception], reads: list[str] | None = None) -> Callable[[str], str]:
    """A page reader serving these pages by address, each address read noted in ``reads``; an exception given for
    an address is raised."""

    def read(address: str) -> str:
        """Serve the page of an address."""
        if reads is not None:
            reads.append(address)
        page = pages[address]
        if isinstance(page, Exception):
            raise page
        return page

    return read


def test_a_page_puts_forward_the_image_of_its_shares_unless_it_is_a_logo() -> None:
    photo = SiteImageParser.main_photo(LexborHTMLParser(SHARED_PHOTO_PAGE), WEBSITE_URL)

    assert photo == "https://www.ferme-des-tests.fr/wp-content/uploads/2024/05/portee-mai.jpg"


def test_without_a_shared_image_the_first_large_photo_is_kept_logos_icons_and_thumbnails_left_out() -> None:
    photo = SiteImageParser.main_photo(LexborHTMLParser(PHOTOS_ONLY_PAGE), WEBSITE_URL)
    drawing = SiteImageParser.main_photo(
        LexborHTMLParser('<img src="/images/patte.png" width="512"><img src="/images/logo.jpg">'), WEBSITE_URL
    )
    nothing = SiteImageParser.main_photo(LexborHTMLParser("<html><body><p>Bientôt</p></body></html>"), WEBSITE_URL)

    assert photo == "https://static.wixstatic.com/media/603aed_f7d1~mv2.jpg"
    assert drawing == "https://www.ferme-des-tests.fr/images/patte.png"
    assert nothing is None


def test_only_the_own_websites_are_read_for_a_photo() -> None:
    assert BreederWebsiteService.is_own_website(WEBSITE_URL)
    assert not BreederWebsiteService.is_own_website("https://elevage-a.chiens-de-france.com")
    assert not BreederWebsiteService.is_own_website("https://www.centrale-canine.fr/elevage-a")
    assert not BreederWebsiteService.is_own_website("https://www.facebook.com/ferme.des.tests")
    assert not BreederWebsiteService.is_own_website(None)


def test_the_websites_not_read_yet_are_read_once_a_page_that_does_not_answer_again(
    db: Session, seeded: dict[str, str]
) -> None:
    with_photo = breeding(db, website=WEBSITE_URL)
    gone = breeding(db, website="https://www.elevage-disparu.fr")
    not_answering = breeding(db, website="https://www.elevage-lent.fr")
    on_chiens_de_france = breeding(db, website="https://elevage-a.chiens-de-france.com")
    read_before = breeding(db, website="https://www.elevage-lu.fr", website_read_at=datetime(2026, 10, 1))
    reads: list[str] = []
    pages: dict[str, str | Exception] = {
        WEBSITE_URL: SHARED_PHOTO_PAGE,
        "https://www.elevage-disparu.fr": SourcePageMissingError("404"),
        "https://www.elevage-lent.fr": SourceReadError("timeout"),
    }
    service = BreederWebsiteService(page_reader=pages_reader(pages, reads))

    photographed = service.read_unread_websites(db, READ_AT)
    second_run = service.read_unread_websites(db, READ_AT)

    assert photographed == [with_photo.id]
    assert with_photo.website_photo_url == "https://www.ferme-des-tests.fr/wp-content/uploads/2024/05/portee-mai.jpg"
    assert (with_photo.website_read_at, gone.website_read_at, not_answering.website_read_at) == (READ_AT, READ_AT, None)
    assert (on_chiens_de_france.website_read_at, read_before.website_photo_url) == (None, None)
    assert second_run == []
    assert reads == [
        WEBSITE_URL,
        "https://www.elevage-disparu.fr",
        "https://www.elevage-lent.fr",
        "https://www.elevage-lent.fr",
    ]


def test_a_pasted_website_gives_its_photo_and_counts_as_read(db: Session, seeded: dict[str, str]) -> None:
    breeder = breeding(db)
    other_site = "https://www.club-des-cockers.fr/elevages/ferme"

    BreederLinkService(page_reader=pages_reader({WEBSITE_URL: SHARED_PHOTO_PAGE})).add(db, breeder.id, WEBSITE_URL)
    BreederLinkService(page_reader=pages_reader({other_site: PHOTOS_ONLY_PAGE})).add(db, breeder.id, other_site)

    db.expire_all()
    assert breeder.website == WEBSITE_URL
    assert breeder.website_photo_url == "https://www.ferme-des-tests.fr/wp-content/uploads/2024/05/portee-mai.jpg"
    assert breeder.website_read_at is not None


def test_another_pasted_site_gives_its_photo_while_the_breeding_has_none(db: Session, seeded: dict[str, str]) -> None:
    breeder = breeding(db, website="https://www.facebook.com/ferme.des.tests")
    other_site = "https://www.club-des-cockers.fr/elevages/ferme"

    BreederLinkService(page_reader=pages_reader({other_site: PHOTOS_ONLY_PAGE})).add(db, breeder.id, other_site)

    db.expire_all()
    assert breeder.website_photo_url == "https://static.wixstatic.com/media/603aed_f7d1~mv2.jpg"
    assert breeder.website_read_at is None


def test_the_photo_of_a_breeding_comes_from_its_sites_the_covers_first() -> None:
    website_only = Breeder(website_photo_url="https://www.ferme-des-tests.fr/portee.jpg", scc_site_photos=[])
    with_gallery = Breeder(
        scc_site_photos=["https://www.centrale-canine.fr/sites/default/files/media/galerie.jpg"],
        website_photo_url="https://www.ferme-des-tests.fr/portee.jpg",
    )
    with_cover = Breeder(
        cover_photo_url="https://elevage-a.chiens-de-france.com/media_cdf/photos/couverture.jpg",
        scc_site_cover_url="https://www.centrale-canine.fr/sites/default/files/couverture.jpg",
        scc_site_photos=[],
    )

    assert website_only.site_photo_url == "https://www.ferme-des-tests.fr/portee.jpg"
    assert with_gallery.site_photo_url == "https://www.centrale-canine.fr/sites/default/files/media/galerie.jpg"
    assert with_cover.site_photo_url == "https://elevage-a.chiens-de-france.com/media_cdf/photos/couverture.jpg"


def test_the_card_of_a_breeding_without_a_cover_shows_the_photo_of_its_website(
    client: TestClient, db: Session, seeded: dict[str, str]
) -> None:
    breeder = breeding(db, website=WEBSITE_URL, website_photo_url="https://www.ferme-des-tests.fr/portee.jpg")

    cards = client.get("/api/v1/breeders", headers=seeded).json()

    card = next(card for card in cards if card["id"] == breeder.id)
    assert card["photo_url"] == "https://www.ferme-des-tests.fr/portee.jpg"


def test_the_links_found_by_hand_fill_the_empty_places_of_their_breeders(db: Session, engine: Engine) -> None:
    du_lavoir = Breeder(display_name="Martin Claire", scc_breeder_id="500655")
    colline = Breeder(
        display_name="Durand Anne",
        scc_breeder_id="187925",
        facebook_url="https://www.facebook.com/colline.declaree",
        social_link_origins={"facebook": "centrale_canine"},
    )
    db.add_all([du_lavoir, colline])
    db.commit()

    add_breeder_links_found_by_hand.run_migration(engine)

    db.expire_all()
    assert (du_lavoir.chiens_de_france_site_url, du_lavoir.website) == (
        "https://dulavoir.chiens-de-france.com",
        "https://dulavoir.chiens-de-france.com",
    )
    assert (colline.website, colline.website_photo_url) == (
        "https://elevage-canin-lagarnache.fr/",
        "https://elevage-canin-lagarnache.fr/wp-content/uploads/2022/09/Cocker-chiot-1024x768.jpg",
    )
    assert colline.website_read_at is not None
    assert (colline.facebook_url, colline.social_link_origins) == (
        "https://www.facebook.com/colline.declaree",
        {"facebook": "centrale_canine"},
    )
