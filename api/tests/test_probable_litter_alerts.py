"""A followed breeder whose mother is likely to have a litter within a month is told so, once (docs/04,
« breeder_probable_litter »)."""

from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_source import ListingSource
from enums.notification_kind import NotificationKind
from models.breeder import Breeder
from models.breeder_follow import BreederFollow
from models.dog import Dog
from models.notification import Notification
from models.user import User
from seeders.run_seeders import SeederRunner
from services.breeder_alert_service import breeder_alert_service
from services.collectors.raw_listing import ColorReading
from services.notification_texts import NotificationTexts
from services.push_service import PushResult, PushService

MORNING = datetime(2026, 11, 15, 9, 10)


@pytest.fixture
def follow(db: Session, monkeypatch: pytest.MonkeyPatch) -> BreederFollow:
    """
    The seeds, a breeding whose gold mother had her last litter a year ago with a gold father, followed by the user;
    pushes delivered without network.
    """
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    breeder = Breeder(affix="Du Clos de Test", department_code="35")
    breeder.chiens_de_france_litters = [
        {"birth_date": "2025-11-19", "sire_name": "Valentino du Clos de Test", "dam_name": "Selune du Clos de Test"},
    ]
    db.add(breeder)
    db.flush()
    for full_name, sex in (("Selune du Clos de Test", DogSex.FEMALE), ("Valentino du Clos de Test", DogSex.MALE)):
        db.add(
            Dog(
                breeder_id=breeder.id,
                source=ListingSource.CHIENS_DE_FRANCE,
                external_id=full_name,
                role=DogRole.REPRODUCER,
                full_name=full_name,
                name=full_name.split()[0],
                sex=sex,
                color=CoatColor.GOLD,
            )
        )
    breeder_follow = BreederFollow(user_id=db.query(User).one().id, breeder_id=breeder.id)
    db.add(breeder_follow)
    db.commit()
    return breeder_follow


def test_a_probable_litter_of_a_followed_breeder_is_pushed_once(db: Session, follow: BreederFollow) -> None:
    first_count = breeder_alert_service.send_probable_litter_alerts(db, MORNING)
    second_count = breeder_alert_service.send_probable_litter_alerts(db, datetime(2026, 11, 16, 9, 10))

    pushes = db.query(Notification).filter(Notification.kind == NotificationKind.BREEDER_PROBABLE_LITTER).all()
    assert (first_count, second_count) == (1, 0)
    assert [(push.title, push.url) for push in pushes] == [
        ("Portée probable · Du Clos de Test", f"/eleveurs/{follow.breeder_id}")
    ]
    assert pushes[0].body == (
        "Selune a eu sa dernière portée le 19 novembre 2025. Une nouvelle portée gold est probable vers novembre : "
        "appelle pour te placer sur sa liste d’attente."
    )


def test_a_probable_litter_is_not_pushed_more_than_a_month_ahead_nor_without_the_alert_of_new_litters(
    db: Session, follow: BreederFollow
) -> None:
    too_early = breeder_alert_service.send_probable_litter_alerts(db, datetime(2026, 10, 1, 9, 10))
    follow.notify_new_mating = False
    db.commit()
    turned_off = breeder_alert_service.send_probable_litter_alerts(db, MORNING)

    assert (too_early, turned_off) == (0, 0)


def test_a_probable_litter_of_an_ignored_colour_is_recorded_without_a_push(db: Session, follow: BreederFollow) -> None:
    for dog in db.query(Dog):
        dog.color = CoatColor.BLEU_ROUAN
    db.commit()

    sent_count = breeder_alert_service.send_probable_litter_alerts(db, MORNING)

    assert sent_count == 0
    assert db.query(Notification).count() == 0


def test_the_body_leaves_out_an_unsure_colour_and_the_year_of_this_year() -> None:
    body = NotificationTexts.probable_litter(
        "Prune",
        date(2026, 1, 10),
        date(2027, 1, 10),
        (ColorReading(CoatColor.GOLD, ColorConfidence.AMBIGUOUS),),
        date(2026, 12, 20),
    )

    assert body == (
        "Prune a eu sa dernière portée le 10 janvier. Une nouvelle portée est probable vers janvier 2027 : appelle "
        "pour te placer sur sa liste d’attente."
    )
