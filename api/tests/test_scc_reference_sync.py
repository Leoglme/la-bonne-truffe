"""SccReferenceSync: identifiers read from the filters of the breed page, never guessed."""

from pathlib import Path

from sqlalchemy.orm import Session

from models.breed import Breed
from models.breed_variety import BreedVariety
from models.department import Department
from seeders.run_seeders import SeederRunner
from services.scc_reference_sync import scc_reference_sync

BREED_PAGE = (Path(__file__).parent / "fixtures" / "centrale_canine" / "breed_page_selects.html").read_text(
    encoding="utf-8"
)


def test_parse_options_sorts_the_three_filters() -> None:
    options = scc_reference_sync.parse_options(BREED_PAGE)

    assert [option.value for option in options.departments] == ["t_TEST_22", "t_TEST_29", "t_41", "t_TEST_56"]
    assert [option.value for option in options.varieties] == ["317", "159", "TEST_AUTRES"]
    assert [option.label for option in options.birth_statuses] == ["Disponibles", "A naître", "Toutes"]


def test_sync_fills_only_missing_identifiers(db: Session) -> None:
    SeederRunner.run(db)
    cocker = db.query(Breed).one()

    result = scc_reference_sync.sync(db, cocker, BREED_PAGE)

    assert result.department_term_ids_set == {"22": "t_TEST_22", "29": "t_TEST_29", "56": "t_TEST_56"}
    assert result.variety_ids_set == {"autres couleurs": "TEST_AUTRES"}
    ille_et_vilaine = db.get(Department, "35")
    loire_atlantique = db.get(Department, "44")
    assert ille_et_vilaine is not None and ille_et_vilaine.scc_term_id == "t_41"
    assert loire_atlantique is not None and loire_atlantique.scc_term_id is None
    assert (
        db.query(BreedVariety).filter(BreedVariety.label == "autres couleurs").one().source_variety_id == "TEST_AUTRES"
    )
