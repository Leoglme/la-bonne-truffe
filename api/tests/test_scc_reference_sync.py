"""SccReferenceSync: identifiers read from the filters of a real litters page, never guessed."""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from models.breed import Breed
from models.department import Department
from seeders.run_seeders import SeederRunner
from services.collectors.centrale_canine import CentraleCanineCollector
from services.scc_reference_sync import scc_reference_sync

PAGE = json.loads(
    (Path(__file__).parent / "fixtures" / "centrale_canine" / "litters_35_page_0.json").read_text(encoding="utf-8")
)
FILTERS = CentraleCanineCollector.page_filters(PAGE)


def test_parse_options_reads_the_three_filters() -> None:
    options = scc_reference_sync.parse_options(FILTERS)

    assert len(options.departments) == 74
    assert ("t_41", "35 - Ile-et-Vilaine") in {(option.value, option.label) for option in options.departments}
    assert [option.value for option in options.varieties] == ["158", "159", "317"]
    assert [option.value for option in options.birth_statuses] == ["yes", "no"]


def test_sync_stores_department_identifiers_and_knows_the_seeded_varieties(db: Session) -> None:
    SeederRunner.run(db)
    cocker = db.query(Breed).one()
    finistere = db.get(Department, "29")
    assert finistere is not None
    finistere.scc_term_id = None
    db.commit()

    result = scc_reference_sync.sync(db, cocker, FILTERS)

    assert result.department_term_ids_set == {"29": "t_35"}
    assert result.unknown_varieties == []
    hautes_alpes = db.get(Department, "05")
    assert hautes_alpes is not None and hautes_alpes.scc_term_id is None


def test_sync_reports_a_variety_the_seeders_do_not_know(db: Session) -> None:
    SeederRunner.run(db)
    cocker = db.query(Breed).one()
    filters_with_a_new_variety = {**FILTERS, "variety": {**FILTERS["variety"], "999": "nouvelle variété"}}

    result = scc_reference_sync.sync(db, cocker, filters_with_a_new_variety)

    assert [(option.value, option.label) for option in result.unknown_varieties] == [("999", "nouvelle variété")]
