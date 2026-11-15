"""The coat of a puppy read on its photo by the AI when its ad gives none, and what the litter then shows
(docs/04, « La robe lue sur la photo »)."""

import base64
import json
from datetime import date, datetime

import httpx
import pytest
from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.listing import Listing
from models.litter_group import LitterGroup
from seeders.run_seeders import SeederRunner
from services.collectors.polite_http_client import PoliteHttpClient
from services.matching.snapshot_builder import LitterSnapshotBuilder
from services.notification_texts import NotificationTexts
from services.puppy_photo_color_reader import (
    GroqVisionClient,
    PhotoColorReading,
    PuppyPhotoColorReader,
    VisionModelAnswerError,
)

READ_AT = datetime(2026, 11, 15, 9, 30)
PHOTO_HOST = "https://elevage-a.chiens-de-france.com"


@pytest.fixture
def litter(db: Session) -> LitterGroup:
    """The seeds and a born litter of a breeding of Ille-et-Vilaine, whose parents give gold or black and tan."""
    SeederRunner.run(db)
    breeder = Breeder(affix="Du Clos de Test", department_code="35")
    db.add(breeder)
    db.flush()
    group = LitterGroup(
        breed_id=db.query(Breed).one().id,
        breeder_id=breeder.id,
        birth_date=date(2026, 10, 8),
        expected_colors=[
            {"color": "gold", "confidence": "ambiguous", "reason": "Gold possible", "puppy_odds": 0.5},
            {"color": "noir_et_feu", "confidence": "ambiguous", "reason": "Gold possible"},
        ],
        first_seen_at=datetime(2026, 11, 1),
        last_seen_at=datetime(2026, 11, 1),
    )
    db.add(group)
    db.commit()
    return group


def add_puppy_ad(db: Session, group: LitterGroup, number: int, status: str, photos: list[str]) -> Listing:
    """
    Store the ad of one male puppy of the litter, as the site of its breeding shows it, without a colour.

    Args:
        db: Database session.
        group: Its litter.
        number: Its number on Chiens de France.
        status: Its status line (« Mâle disponible à la vente »).
        photos: Its photos.

    Returns:
        The listing, flushed.
    """
    listing = Listing(
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id=f"chiot-{number}",
        breed_id=group.breed_id,
        breeder_id=group.breeder_id,
        litter_group_id=group.id,
        kind=ListingKind.PUPPY_AD,
        lof_status=LofStatus.LOF,
        birth_date=group.birth_date,
        male_count=1,
        female_count=0,
        puppies_available=1 if "disponible" in status else 0,
        department_code="35",
        photos=photos,
        raw_json={"status": status},
        first_seen_at=datetime(2026, 11, 10, number % 60),
    )
    db.add(listing)
    db.flush()
    return listing


def groq_answering(colors_by_size: dict[int, str], requests: list[httpx.Request]) -> GroqVisionClient:
    """
    A Groq client whose model answers, for each photo, the colour its size in bytes stands for.

    Args:
        colors_by_size: Colour answered by size of the photo sent, or the status of a refusal (« 429 »).
        requests: Filled with every request sent.

    Returns:
        The client.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """Read the photo sent and answer as the model would."""
        requests.append(request)
        image_url = json.loads(request.content)["messages"][1]["content"][1]["image_url"]["url"]
        size = len(base64.b64decode(image_url.split(",", 1)[1]))
        color = colors_by_size[size]
        if color.isdigit():
            return httpx.Response(int(color))
        content = json.dumps({"subject": "one_puppy", "color": color, "confidence": "high"})
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    return GroqVisionClient("cle-de-test", "qwen-test", httpx.Client(transport=httpx.MockTransport(answer)))


def photos_serving(sizes_by_path: dict[str, int]) -> PoliteHttpClient:
    """
    A photo client that serves, for each path, a photo of a given size.

    Args:
        sizes_by_path: Size in bytes by path of the photo.

    Returns:
        The client, without pause.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """Serve the photo asked for, or a 404."""
        size = sizes_by_path.get(request.url.path)
        if size is None:
            return httpx.Response(404)
        return httpx.Response(200, content=b"x" * size, headers={"content-type": "image/jpeg"})

    return PoliteHttpClient(
        "Photos de test",
        "LaBonneTruffe/test",
        httpx.Client(transport=httpx.MockTransport(answer)),
        seconds_between_requests=0.0,
    )


def test_only_the_ads_of_one_puppy_without_colour_with_a_photo_of_their_own_wait_for_the_ai(
    db: Session, litter: LitterGroup
) -> None:
    waiting = add_puppy_ad(db, litter, 1, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p1.jpg"])
    add_puppy_ad(db, litter, 2, "Mâle disponible à la vente", [f"{PHOTO_HOST}/portee.jpg"])
    add_puppy_ad(db, litter, 3, "Mâle disponible à la vente", [f"{PHOTO_HOST}/portee.jpg"])
    colored = add_puppy_ad(db, litter, 4, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p4.jpg"])
    colored.colors = [{"color": "gold", "confidence": "certain"}]
    noted = add_puppy_ad(db, litter, 5, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p5.jpg"])
    noted.confirmed_color = CoatColor.GOLD
    already_read = add_puppy_ad(db, litter, 6, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p6.jpg"])
    already_read.color_suggested_at = READ_AT
    already_read.color_suggestion_photo_url = f"{PHOTO_HOST}/p6.jpg"
    new_photo = add_puppy_ad(db, litter, 7, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p7b.jpg"])
    new_photo.color_suggested_at = READ_AT
    new_photo.color_suggestion_photo_url = f"{PHOTO_HOST}/p7.jpg"
    db.commit()

    pending = PuppyPhotoColorReader.pending_listings(db)

    assert sorted(listing.id for listing, _photo in pending) == [waiting.id, new_photo.id]


def test_the_litter_of_two_gold_parents_does_not_wait_for_the_ai(db: Session, litter: LitterGroup) -> None:
    litter.expected_colors = [{"color": "gold", "confidence": "inferred", "reason": "Gold", "puppy_odds": 1.0}]
    add_puppy_ad(db, litter, 1, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p1.jpg"])
    db.commit()

    assert PuppyPhotoColorReader.pending_listings(db) == []


def test_the_colours_read_make_the_litter_the_colour_of_its_puppies_still_offered(
    db: Session, litter: LitterGroup
) -> None:
    add_puppy_ad(db, litter, 1, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p1.jpg"])
    add_puppy_ad(db, litter, 2, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p2.jpg"])
    add_puppy_ad(db, litter, 3, "Mâle en cours de réservation", [f"{PHOTO_HOST}/p3.jpg"])
    db.commit()
    requests: list[httpx.Request] = []
    reader = PuppyPhotoColorReader(
        groq_answering({11: "noir_et_feu", 22: "noir_et_feu", 33: "gold"}, requests),
        photos_serving({"/p1.jpg": 11, "/p2.jpg": 22, "/p3.jpg": 33}),
        sleep=lambda _seconds: None,
        photos_per_run=3,
    )

    read_count = reader.read_pending(db, READ_AT)

    snapshot = LitterSnapshotBuilder.build(db, litter)
    assert read_count == 3
    assert requests[0].headers["Authorization"] == "Bearer cle-de-test"
    assert [listing.suggested_color for listing in db.query(Listing).order_by(Listing.external_id)] == [
        CoatColor.NOIR_ET_FEU,
        CoatColor.NOIR_ET_FEU,
        CoatColor.GOLD,
    ]
    assert snapshot is not None
    assert [(reading.color, reading.confidence) for reading in snapshot.colors] == [
        (CoatColor.NOIR_ET_FEU, ColorConfidence.SUGGESTED)
    ]
    assert NotificationTexts._color_phrase(snapshot) == "noir et feu d’après les photos"


@pytest.mark.parametrize("refusal", ["429", "401", "503"])
def test_a_model_that_does_not_answer_stops_the_run_and_the_next_one_goes_on(
    db: Session, litter: LitterGroup, refusal: str
) -> None:
    add_puppy_ad(db, litter, 1, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p1.jpg"])
    add_puppy_ad(db, litter, 2, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p2.jpg"])
    add_puppy_ad(db, litter, 3, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p3.jpg"])
    db.commit()
    requests: list[httpx.Request] = []
    reader = PuppyPhotoColorReader(
        groq_answering({11: "gold", 22: refusal, 33: "gold"}, requests),
        photos_serving({"/p1.jpg": 33, "/p2.jpg": 22, "/p3.jpg": 11}),
        sleep=lambda _seconds: None,
        photos_per_run=3,
    )

    read_count = reader.read_pending(db, READ_AT)

    assert (read_count, len(requests)) == (1, 2)
    assert [listing.external_id for listing, _photo in PuppyPhotoColorReader.pending_listings(db)] == [
        "chiot-2",
        "chiot-1",
    ]


def test_a_photo_the_model_refuses_waits_for_the_next_run_and_the_others_are_read(
    db: Session, litter: LitterGroup
) -> None:
    add_puppy_ad(db, litter, 1, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p1.jpg"])
    add_puppy_ad(db, litter, 2, "Mâle disponible à la vente", [f"{PHOTO_HOST}/p2.jpg"])
    db.commit()
    reader = PuppyPhotoColorReader(
        groq_answering({11: "gold", 22: "400"}, []),
        photos_serving({"/p1.jpg": 11, "/p2.jpg": 22}),
        sleep=lambda _seconds: None,
        photos_per_run=2,
    )

    read_count = reader.read_pending(db, READ_AT)

    assert read_count == 1
    assert [listing.external_id for listing, _photo in PuppyPhotoColorReader.pending_listings(db)] == ["chiot-2"]


def test_a_photo_gone_is_noted_as_read_without_colour(db: Session, litter: LitterGroup) -> None:
    gone = add_puppy_ad(db, litter, 1, "Mâle disponible à la vente", [f"{PHOTO_HOST}/disparue.jpg"])
    db.commit()
    reader = PuppyPhotoColorReader(groq_answering({}, []), photos_serving({}), sleep=lambda _seconds: None)

    reader.read_pending(db, READ_AT)

    assert (gone.suggested_color, gone.color_suggested_at) == (None, READ_AT)


def test_a_colour_is_kept_only_for_one_puppy_seen_surely() -> None:
    one_puppy = GroqVisionClient.parse_answer(
        '```json\n{"dogs_seen": 1, "subject": "one_puppy", "nose": "black", "color": "gold", "confidence": "high"}\n```'
    )
    several_dogs = PhotoColorReading("several_dogs", CoatColor.GOLD, "high")
    unsure = PhotoColorReading("one_puppy", CoatColor.GOLD, "low")
    unknown = GroqVisionClient.parse_answer('{"subject": "one_puppy", "color": "rouge vif", "confidence": "high"}')

    assert one_puppy.accepted_color == CoatColor.GOLD
    assert (several_dogs.accepted_color, unsure.accepted_color, unknown.accepted_color) == (None, None, None)
    with pytest.raises(VisionModelAnswerError):
        GroqVisionClient.parse_answer("Je vois un chiot.")
