"""BreederContactParser: names, affix key, phone, SIREN and postal code as the sources publish them."""

import pytest

from services.collectors.breeder_contact_parser import BreederContactParser


@pytest.mark.parametrize(
    ("published", "readable"),
    [
        ("SAINT-AUBIN-DU-CORMIER", "Saint-Aubin-du-Cormier"),
        ("DU CLOS DE L'ÉCOTAY", "Du Clos de l'Écotay"),
        ("L’ORÉE DES BOIS", "L’Orée des Bois"),
        ("DU CLOS DE L'ÉLEVAGE D", "Du Clos de l'Élevage D"),
        ("O'NEIL", "O'Neil"),
        ("DUBLIN'S ROSE", "Dublin's Rose"),
        ("DES JOYAUX DES KI'MILLACS", "Des Joyaux des Ki'millacs"),
        ("  LA   ROCHE-SUR-YON ", "La Roche-sur-Yon"),
        ("sarthe", "Sarthe"),
        ("Élevage de la Vallée", "Élevage de la Vallée"),
        ("   ", None),
        (None, None),
    ],
)
def test_readable_name_writes_upper_case_names_the_french_way(published: str | None, readable: str | None) -> None:
    assert BreederContactParser.readable_name(published) == readable


def test_affix_key_ignores_case_accents_and_articles() -> None:
    assert BreederContactParser.affix_key("DU CLOS DE L'ÉCOTAY") == "clos ecotay"
    assert BreederContactParser.affix_key("Clos Écotay") == "clos ecotay"
    assert BreederContactParser.affix_key("") is None


@pytest.mark.parametrize(
    ("published", "e164"),
    [
        ("0600000001", "+33600000001"),
        ("06 00 00 00 01", "+33600000001"),
        ("+33 6 00 00 00 01", "+33600000001"),
        ("600000001", None),
        ("", None),
    ],
)
def test_phone_is_written_in_e164_only_when_readable(published: str, e164: str | None) -> None:
    assert BreederContactParser.phone_e164(published) == e164


def test_siren_is_read_alone_or_from_a_siret() -> None:
    assert BreederContactParser.siren("000 000 001") == "000000001"
    assert BreederContactParser.siren("00000000100017") == "000000001"
    assert BreederContactParser.siren("0000001") is None


def test_postal_code_needs_five_digits() -> None:
    assert BreederContactParser.postal_code("35140") == "35140"
    assert BreederContactParser.postal_code("3514") is None


@pytest.mark.parametrize(
    ("breeding_name", "affix"),
    [
        ("Élevage du Clos de l'Écotay", "Du Clos de l'Écotay"),
        ("Elevage de test A", "De test A"),
        ("ÉLEVAGE DES JOYAUX", "DES JOYAUX"),
        ("Du Clos de l'Écotay", "Du Clos de l'Écotay"),
        ("Élevage", None),
        (None, None),
    ],
)
def test_affix_of_breeding_name_drops_the_word_elevage(breeding_name: str | None, affix: str | None) -> None:
    assert BreederContactParser.affix_of_breeding_name(breeding_name) == affix
