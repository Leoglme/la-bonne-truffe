"""The French sentences of the notifications: colour, place, sexes, in one line (docs/04)."""

from datetime import date

from enums.listing_source import ListingSource
from enums.match_event_kind import MatchEventKind
from services.matching.criteria import LitterSnapshot
from services.matching.scoring import ScoreCalculator

NOTIFICATION_TITLE = "La Bonne Truffe"

FRENCH_MONTHS: tuple[str, ...] = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)

SOURCE_NAMES: dict[ListingSource, str] = {
    ListingSource.CENTRALE_CANINE: "La Centrale Canine",
    ListingSource.CHIENS_DE_FRANCE: "Chiens de France",
    ListingSource.CHIOTS_DE_FRANCE: "Chiots de France",
}


class NotificationTexts:
    """Writes the body of every notification. An unknown fact is left out, never invented."""

    @staticmethod
    def french_day(day: date) -> str:
        """
        A day written the French way.

        Args:
            day: The day.

        Returns:
            « 22 décembre ».
        """
        return f"{day.day} {FRENCH_MONTHS[day.month - 1]}"

    @classmethod
    def litter_event(cls, event: MatchEventKind, snapshot: LitterSnapshot) -> str:
        """
        Body of an immediate notification about one litter.

        Args:
            event: The event.
            snapshot: The litter.

        Returns:
            One sentence, for instance « Née le 27 octobre (Ille-et-Vilaine) : une portée gold, 2 mâles
            et 3 femelles. Dispo vers le 22 décembre. »
        """
        place = f" ({snapshot.department_name})" if snapshot.department_name else ""
        color = cls._color_phrase(snapshot)
        if snapshot.is_born:
            opening = {
                MatchEventKind.BORN: "Née",
                MatchEventKind.UPGRADED: "Passée en préférée, née",
            }.get(event, "Nouvelle portée, née")
            born_on = f" le {cls.french_day(snapshot.birth_date)}" if snapshot.birth_date else ""
            sexes = cls._sexes_phrase(snapshot)
            available = f" Dispo vers le {cls.french_day(snapshot.available_from)}." if snapshot.available_from else ""
            return f"{opening}{born_on}{place} : une portée {color}{sexes}.{available}"
        opening = "Passée en préférée, à naître" if event == MatchEventKind.UPGRADED else "À naître"
        expected = (
            f", naissance vers le {cls.french_day(snapshot.expected_birth_date)}"
            if snapshot.expected_birth_date
            else ""
        )
        return f"{opening}{place} : une portée {color} déclarée{expected}."

    @classmethod
    def evening_digest(cls, snapshots: list[LitterSnapshot]) -> str:
        """
        Body of the evening digest.

        Args:
            snapshots: The acceptable litters of the day, at least one.

        Returns:
            « Récap du soir : 2 portées acceptables, dont 1 noir et feu (Finistère). »
        """
        count = len(snapshots)
        summary = f"Récap du soir : {count} portée{'s' if count > 1 else ''} acceptable{'s' if count > 1 else ''}"
        first = snapshots[0]
        place = f" ({first.department_name})" if first.department_name else ""
        if count == 1:
            return f"{summary} : une portée {cls._color_phrase(first)}{place}."
        return f"{summary}, dont 1 {cls._color_phrase(first)}{place}."

    @staticmethod
    def source_down(source: ListingSource, failed_run_count: int, error_message: str | None) -> str:
        """
        Body of the alert sent when a source fails several runs in a row.

        Args:
            source: The failing source.
            failed_run_count: Consecutive failed runs.
            error_message: Last error.

        Returns:
            One sentence.
        """
        reason = f" Dernière erreur : {error_message}" if error_message else ""
        return f"{SOURCE_NAMES[source]} ne répond plus depuis {failed_run_count} relevés.{reason}"

    @staticmethod
    def _color_phrase(snapshot: LitterSnapshot) -> str:
        """
        The colour of a litter as written in a sentence.

        Args:
            snapshot: The litter.

        Returns:
            « gold », « noir ou noir et feu (à confirmer) » or « de couleur à confirmer ».
        """
        if not snapshot.colors:
            return "de couleur à confirmer"
        labels = " ou ".join(ScoreCalculator.color_label(reading.color) for reading in snapshot.colors)
        return labels if snapshot.has_certain_colors else f"{labels} (à confirmer)"

    @staticmethod
    def _sexes_phrase(snapshot: LitterSnapshot) -> str:
        """
        The sexes of a born litter, or nothing while unknown.

        Args:
            snapshot: The litter.

        Returns:
            « , 2 mâles et 3 femelles » or an empty string.
        """
        if snapshot.male_count is None or snapshot.female_count is None:
            return ""
        males = f"{snapshot.male_count} mâle{'s' if snapshot.male_count > 1 else ''}"
        females = f"{snapshot.female_count} femelle{'s' if snapshot.female_count > 1 else ''}"
        return f", {males} et {females}"
