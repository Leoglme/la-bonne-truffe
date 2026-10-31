"""The text the breeder search looks into, and what finds a breeder in it."""

from models.breeder import Breeder
from services.breeder_search_text import BreederSearchText


def breeder_of_test() -> Breeder:
    """A breeder with an affix in several words, a town, a SIREN, a phone and a link."""
    return Breeder(
        affix="Du Clos de l'Élevage A",
        display_name="Éleveuse de Test A",
        city="Saint-Aubin-du-Cormier",
        zip_code="35140",
        siren="000000001",
        phone_e164="+33600000001",
        chiens_de_france_site_url="https://elevage-a.chiens-de-france.com",
        links=[{"label": "Facebook", "url": "https://www.facebook.com/elevage.a"}],
    )


def test_the_search_text_holds_each_value_with_and_without_spaces() -> None:
    text = BreederSearchText.build(breeder_of_test())

    assert "du clos de l elevage a" in text
    assert "duclosdelelevagea" in text
    assert "saint aubin du cormier" in text
    assert "0600000001" in text
    assert "facebook.com" not in text
    assert "facebook com" in text


def test_a_query_finds_a_breeder_whatever_the_accents_the_spaces_and_the_case() -> None:
    text = BreederSearchText.build(breeder_of_test())

    assert BreederSearchText.matches(text, "du clos")
    assert BreederSearchText.matches(text, "DUCLOSDELELEVAGEA")
    assert BreederSearchText.matches(text, "Saint-Aubin élevage")
    assert BreederSearchText.matches(text, "35140")
    assert BreederSearchText.matches(text, "06 00 00 00 01")
    assert BreederSearchText.matches(text, "eleveuse")
    assert not BreederSearchText.matches(text, "kerlann")
    assert not BreederSearchText.matches(text, "   ")
    assert not BreederSearchText.matches(None, "du clos")


def test_the_whole_phrase_is_told_apart_from_its_words() -> None:
    text = BreederSearchText.build(breeder_of_test())

    assert BreederSearchText.holds_phrase(text, "Du Clos de l'Élevage A")
    assert BreederSearchText.holds_phrase(text, "06 00 00 00 01")
    assert BreederSearchText.holds_phrase(text, "DuClosDeLElevageA")
    assert not BreederSearchText.holds_phrase(text, "élevage saint-aubin")
    assert not BreederSearchText.holds_phrase(text, "")
    assert not BreederSearchText.holds_phrase(None, "du clos")
