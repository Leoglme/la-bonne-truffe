"""without_accents: the accented letters lose their accents, the rest of the text stays as it is."""

from core.text import without_accents


def test_accented_letters_become_plain_letters_and_the_case_stays() -> None:
    assert without_accents("Élevage du Mâle à Plouézec") == "Elevage du Male a Plouezec"
