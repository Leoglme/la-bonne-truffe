"""Reads the coat of a puppy on its photo with a Mistral vision model, when no source gives it (docs/04)."""

import base64
import json
import logging
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from core.config import settings
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.listing_kind import ListingKind
from models.dog import Dog
from models.listing import Listing
from models.litter_group import LitterGroup
from services.collectors.polite_http_client import PoliteHttpClient, SourcePageMissingError, SourceReadError
from services.matching.match_refresh import match_refresh_service

logger = logging.getLogger(__name__)

MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
QUOTA_STATUS_CODE = 429
# Ten readings a minute at most: the free plan's limit is shared by every app using the same account.
SECONDS_BETWEEN_READINGS = 6.0
PHOTOS_PER_RUN = 15
LARGEST_PHOTO_BYTES = 5_000_000
ANSWER_TOKENS = 200
ACCEPTED_SUBJECT = "one_puppy"
ACCEPTED_CONFIDENCES: frozenset[str] = frozenset({"high", "medium"})
CODE_FENCE = "```"
IMAGE_TYPES_BY_EXTENSION: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

SYSTEM_PROMPT = (
    "You read the coat colour of English Cocker Spaniel puppies on the photos of their ads. "
    "You answer with one JSON object and nothing else."
)
USER_PROMPT = """Look at this photo from an English Cocker Spaniel puppy ad.
1. "subject": "one_puppy" when it mainly shows one puppy (younger than about four months), "several_dogs" when it shows
several dogs, "adult_dog" when the dog is an adult, "no_dog" when there is no dog.
2. "color": the coat of that puppy, one of:
- "gold": solid red, golden, orange or fawn; a small white mark on the chest is fine
- "noir": solid black; a small white mark on the chest is fine
- "noir_et_feu": black with tan points (eyebrows, muzzle, chest, legs)
- "marron": solid brown, chocolate or liver
- "marron_et_feu": brown with tan points
- "bleu_rouan": black and white hairs mixed (blue roan)
- "orange_rouan": orange and white hairs mixed (orange roan)
- "marron_rouan": brown and white hairs mixed (liver roan)
- "tricolore": black or brown, white and tan, in patches
- "particolore": white with clear patches of one colour (black, orange, brown or lemon)
- "zibeline": sable
- "inconnue": you cannot tell
3. "confidence": "high", "medium" or "low".
Answer: {"subject": "...", "color": "...", "confidence": "..."}"""


class MistralQuotaError(RuntimeError):
    """Mistral refuses for now: the quota of the minute or of the day is spent."""


class MistralReadError(RuntimeError):
    """Mistral could not be reached, or answered something that is not a reading."""


@dataclass(frozen=True)
class PhotoColorReading:
    """What the model saw on a photo: what it shows, the coat, and how sure it is."""

    subject: str
    color: CoatColor
    confidence: str

    @property
    def accepted_color(self) -> CoatColor | None:
        """
        The coat kept from the reading: only for one puppy, read with a high or medium confidence.

        Returns:
            The colour, None when the photo shows several dogs or an adult, or the model is unsure.
        """
        if (
            self.subject != ACCEPTED_SUBJECT
            or self.confidence not in ACCEPTED_CONFIDENCES
            or self.color == CoatColor.INCONNUE
        ):
            return None
        return self.color


class MistralVisionClient:
    """Asks a Mistral vision model what coat the puppy of a photo has."""

    def __init__(self, api_key: str, model: str, http_client: httpx.Client | None = None) -> None:
        """
        Prepare the client.

        Args:
            api_key: Mistral key.
            model: Model that reads the photos.
            http_client: HTTP client, injected by the tests.
        """
        self.api_key = api_key
        self.model = model
        self.http_client = http_client or httpx.Client(timeout=60.0)

    def read_coat(self, image: bytes, content_type: str) -> PhotoColorReading:
        """
        Send a photo and read the answer.

        Args:
            image: The photo.
            content_type: Its type (« image/jpeg »).

        Returns:
            The reading.

        Raises:
            MistralQuotaError: When Mistral refuses for the quota (429).
            MistralReadError: On a network error, another refusal, or an answer that is not a reading.
        """
        image_url = f"data:{content_type};base64,{base64.b64encode(image).decode('ascii')}"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_PROMPT},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": ANSWER_TOKENS,
        }
        try:
            response = self.http_client.post(
                MISTRAL_CHAT_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            )
        except httpx.HTTPError as error:
            raise MistralReadError(f"Mistral injoignable : {error}") from error
        if response.status_code == QUOTA_STATUS_CODE:
            raise MistralQuotaError("Mistral : quota atteint")
        if response.status_code >= 400:
            raise MistralReadError(f"Mistral : réponse {response.status_code}")
        try:
            content = str(response.json()["choices"][0]["message"]["content"])
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise MistralReadError("Mistral : réponse sans texte") from error
        return self.parse_answer(content)

    @staticmethod
    def parse_answer(content: str) -> PhotoColorReading:
        """
        Read the JSON object the model answered, with or without a code fence around it.

        Args:
            content: The text of the answer.

        Returns:
            The reading; a colour outside the vocabulary is unknown.

        Raises:
            MistralReadError: When the text is not a JSON object.
        """
        text = content.strip().removeprefix(CODE_FENCE + "json").removeprefix(CODE_FENCE).removesuffix(CODE_FENCE)
        try:
            answer = json.loads(text)
        except ValueError as error:
            raise MistralReadError("Mistral : réponse illisible") from error
        if not isinstance(answer, dict):
            raise MistralReadError("Mistral : réponse illisible")
        color_value = str(answer.get("color", "")).strip().lower()
        color = CoatColor(color_value) if color_value in CoatColor._value2member_map_ else CoatColor.INCONNUE
        return PhotoColorReading(
            subject=str(answer.get("subject", "")).strip().lower(),
            color=color,
            confidence=str(answer.get("confidence", "")).strip().lower(),
        )


class PuppyPhotoColorReader:
    """Reads, a few at a time, the photos of the puppies whose ads give no colour, then matches their litters again."""

    def __init__(
        self,
        vision_client: MistralVisionClient | None = None,
        photo_client: PoliteHttpClient | None = None,
        sleep: Callable[[float], None] = time.sleep,
        photos_per_run: int = PHOTOS_PER_RUN,
    ) -> None:
        """
        Prepare the reader.

        Args:
            vision_client: The model, injected by the tests; otherwise Mistral with the key of the ``.env``.
            photo_client: Fetches the photos, injected by the tests; otherwise one request a second through ``curl``.
            sleep: Pause between two readings, injected by the tests.
            photos_per_run: Photos read at most by one run; the others wait for the next one.
        """
        self.vision_client = vision_client or (
            MistralVisionClient(settings.mistral_api_key, settings.mistral_vision_model)
            if settings.mistral_api_key
            else None
        )
        self.photo_client = photo_client or PoliteHttpClient("Photos des annonces", settings.honest_user_agent)
        self.sleep = sleep
        self.photos_per_run = photos_per_run

    def read_pending(self, db: Session, now: datetime) -> int:
        """
        Read the photos waiting, the newest ads first, and keep what the model saw; when a colour changed, match the
        litters again (a gold seen on the photos can push a litter to « préférée »). The run stops at the first
        refusal for the quota and resumes at the next one.

        Args:
            db: Database session; committed at the end.
            now: Run time, naive UTC.

        Returns:
            How many photos were read.
        """
        if self.vision_client is None:
            return 0
        read_count = 0
        has_color_changed = False
        for listing, photo_url in self.pending_listings(db)[: self.photos_per_run]:
            if read_count > 0:
                self.sleep(SECONDS_BETWEEN_READINGS)
            try:
                color = self._read_photo(photo_url)
            except SourcePageMissingError:
                color = None
            except SourceReadError as error:
                logger.warning("Puppy photo not read %s: %s", photo_url, error)
                continue
            except MistralQuotaError:
                logger.info("Puppy photos: Mistral quota reached, the next run goes on")
                break
            except MistralReadError as error:
                logger.warning("Puppy photo not read by Mistral %s: %s", photo_url, error)
                continue
            has_color_changed = has_color_changed or color != listing.suggested_color
            listing.suggested_color = color
            listing.color_suggested_at = now
            listing.color_suggestion_photo_url = photo_url
            read_count += 1
        db.commit()
        if has_color_changed:
            match_refresh_service.refresh(db, now)
        return read_count

    @classmethod
    def pending_listings(cls, db: Session) -> list[tuple[Listing, str]]:
        """
        The ads of one puppy still online whose source gives no colour, not noted by hand, with a photo of their own
        the model has not read yet: a photo several ads share shows the litter or a parent, not the puppy.

        Args:
            db: Database session.

        Returns:
            Each ad with the photo to read, the newest ads first.
        """
        puppy_ads = (
            db.query(Listing)
            .filter(Listing.kind == ListingKind.PUPPY_AD, Listing.is_active.is_(True))
            .order_by(Listing.first_seen_at.desc(), Listing.id.desc())
            .all()
        )
        photo_uses = Counter(photo for listing in puppy_ads for photo in dict.fromkeys(listing.photos))
        litters_told_otherwise = cls._litters_whose_colours_are_told_otherwise(db)
        pending: list[tuple[Listing, str]] = []
        for listing in puppy_ads:
            if (
                listing.colors
                or listing.confirmed_color is not None
                or not cls._is_one_puppy(listing)
                or listing.litter_group_id in litters_told_otherwise
            ):
                continue
            own_photo = next((photo for photo in listing.photos if photo_uses[photo] == 1), None)
            if own_photo is None:
                continue
            if listing.color_suggested_at is not None and listing.color_suggestion_photo_url == own_photo:
                continue
            pending.append((listing, own_photo))
        return pending

    @staticmethod
    def _litters_whose_colours_are_told_otherwise(db: Session) -> set[int]:
        """
        The litters whose puppies' colours the app knows without their photos: two parents that only give one
        colour, or puppies registered at the Centrale Canine with their colour.

        Args:
            db: Database session.

        Returns:
            Their ids.
        """
        told_by_parents = {
            group_id
            for group_id, expected_colors in db.query(LitterGroup.id, LitterGroup.expected_colors)
            if any(entry.get("confidence") == ColorConfidence.INFERRED.value for entry in expected_colors or [])
        }
        told_by_registered_puppies = {
            group_id
            for (group_id,) in db.query(Dog.litter_group_id).filter(
                Dog.role == DogRole.PUPPY, Dog.litter_group_id.is_not(None), Dog.color != CoatColor.INCONNUE
            )
            if group_id is not None
        }
        return told_by_parents | told_by_registered_puppies

    def _read_photo(self, photo_url: str) -> CoatColor | None:
        """
        Fetch a photo and ask the model about it.

        Args:
            photo_url: Address of the photo.

        Returns:
            The coat kept, None when the model could not tell or the photo is too large.

        Raises:
            SourcePageMissingError: When the photo is gone.
            SourceReadError: When the photo cannot be fetched for another reason.
            MistralQuotaError: When Mistral refuses for the quota.
            MistralReadError: When Mistral cannot answer.
        """
        response = self.photo_client.get(photo_url, accept="image/*")
        if len(response.content) > LARGEST_PHOTO_BYTES or self.vision_client is None:
            return None
        return self.vision_client.read_coat(response.content, self._image_type(response, photo_url)).accepted_color

    @staticmethod
    def _image_type(response: httpx.Response, photo_url: str) -> str:
        """
        The type of a photo: the one its server gives, else the one of its extension.

        Args:
            response: The response that brought it.
            photo_url: Its address.

        Returns:
            « image/jpeg » by default.
        """
        served_type = str(response.headers.get("content-type", "")).split(";")[0].strip().lower()
        if served_type.startswith("image/"):
            return served_type
        path = urlparse(photo_url).path.lower()
        return next(
            (image_type for extension, image_type in IMAGE_TYPES_BY_EXTENSION.items() if path.endswith(extension)),
            "image/jpeg",
        )

    @staticmethod
    def _is_one_puppy(listing: Listing) -> bool:
        """
        Whether an ad is about a single puppy, as those of Chiens de France and Cœur de Cocker are.

        Args:
            listing: A puppy ad.

        Returns:
            True for one male or one female.
        """
        return (listing.male_count or 0) + (listing.female_count or 0) == 1
