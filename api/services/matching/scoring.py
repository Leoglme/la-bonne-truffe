"""Third step of docs/04: the 0 to 100 score, one readable reason per point earned."""

from dataclasses import dataclass
from datetime import date

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.color_preference_level import ColorPreferenceLevel
from enums.lof_status import LofStatus
from enums.sex_preference import SexPreference
from services.matching.criteria import LitterSnapshot, ProfileCriteria

MAXIMUM_SCORE = 100
FRESHNESS_WINDOW_DAYS = 14
MINIMUM_PROXIMITY_POINTS = 2
GOOD_PARENT_RATING = 4
SELECTED_BREEDING_GROUP = 1

COLOR_LABELS: dict[CoatColor, str] = {
    CoatColor.GOLD: "gold",
    CoatColor.NOIR: "noir",
    CoatColor.NOIR_ET_FEU: "noir et feu",
    CoatColor.MARRON: "marron",
    CoatColor.MARRON_ET_FEU: "marron et feu",
    CoatColor.BLEU_ROUAN: "bleu rouan",
    CoatColor.ORANGE_ROUAN: "orange rouan",
    CoatColor.MARRON_ROUAN: "marron rouan",
    CoatColor.TRICOLORE: "tricolore",
    CoatColor.PARTICOLORE: "particolore",
    CoatColor.ZIBELINE: "zibeline",
    CoatColor.INCONNUE: "inconnue",
}


@dataclass(frozen=True)
class ScoreReason:
    """One line of « Pourquoi ce score »."""

    text: str
    points: int


class ScoreCalculator:
    """Adds up colour, LOF, sexes, freshness, proximity and bonus points."""

    @classmethod
    def reasons_for(cls, snapshot: LitterSnapshot, criteria: ProfileCriteria, today: date) -> list[ScoreReason]:
        """
        Every reason that earns points, in the order of docs/04.

        Args:
            snapshot: The litter.
            criteria: The profile.
            today: Day of the evaluation, in French time.

        Returns:
            The reasons; the score is the sum of their points, capped at 100.
        """
        reasons = [
            cls._color_reason(snapshot, criteria),
            cls._lof_reason(snapshot),
            cls._sex_reason(snapshot, criteria),
            cls._freshness_reason(snapshot, today),
            cls._proximity_reason(snapshot, criteria),
            *cls._bonus_reasons(snapshot),
        ]
        return [reason for reason in reasons if reason is not None and reason.points > 0]

    @staticmethod
    def score_of(reasons: list[ScoreReason]) -> int:
        """
        Sum the points of the reasons, capped at 100.

        Args:
            reasons: The reasons.

        Returns:
            The score.
        """
        return min(MAXIMUM_SCORE, sum(reason.points for reason in reasons))

    @staticmethod
    def color_label(color: CoatColor) -> str:
        """
        French label of a colour, lowercase.

        Args:
            color: Canonical colour.

        Returns:
            The label (« noir et feu »).
        """
        return COLOR_LABELS[color]

    @classmethod
    def _color_reason(cls, snapshot: LitterSnapshot, criteria: ProfileCriteria) -> ScoreReason | None:
        """
        40 for a certain preferred colour, 20 for an acceptable one or a bundle holding a wanted colour,
        10 while unknown, 0 otherwise.
        """
        if not snapshot.colors:
            return ScoreReason("Couleur pas encore connue", 10)
        levels = {reading.color: criteria.level_of(reading.color) for reading in snapshot.colors}
        if snapshot.has_certain_colors:
            is_confirmed = any(reading.confidence == ColorConfidence.CONFIRMED for reading in snapshot.colors)
            for color, level in levels.items():
                if level == ColorPreferenceLevel.PREFERRED:
                    suffix = ", confirmée" if is_confirmed else ""
                    return ScoreReason(f"{cls.color_label(color).capitalize()}, ta couleur préférée{suffix}", 40)
            for color, level in levels.items():
                if level == ColorPreferenceLevel.ACCEPTABLE:
                    return ScoreReason(f"{cls.color_label(color).capitalize()}, une couleur acceptable", 20)
            return None
        wanted = [color for color, level in levels.items() if level != ColorPreferenceLevel.IGNORED]
        if not wanted:
            return None
        possible = " ou ".join(cls.color_label(color) for color in levels)
        return ScoreReason(f"Couleur à confirmer : {possible}", 20)

    @staticmethod
    def _lof_reason(snapshot: LitterSnapshot) -> ScoreReason | None:
        """20 for a LOF litter, 10 while unknown, 0 for a non-LOF one."""
        if snapshot.lof_status == LofStatus.LOF:
            return ScoreReason("Portée LOF", 20)
        if snapshot.lof_status == LofStatus.UNKNOWN:
            return ScoreReason("LOF à confirmer", 10)
        return None

    @staticmethod
    def _sex_reason(snapshot: LitterSnapshot, criteria: ProfileCriteria) -> ScoreReason | None:
        """15 when the wanted sex is there (any puppy for « peu importe »), 5 while unknown, 0 if absent."""
        if snapshot.male_count is None or snapshot.female_count is None:
            return ScoreReason("Sexes connus à la naissance", 5)
        males = f"{snapshot.male_count} mâle{'s' if snapshot.male_count > 1 else ''}"
        females = f"{snapshot.female_count} femelle{'s' if snapshot.female_count > 1 else ''}"
        description = f"{males} et {females}"
        wanted_count = {
            SexPreference.MALE: snapshot.male_count,
            SexPreference.FEMALE: snapshot.female_count,
            SexPreference.ANY: snapshot.male_count + snapshot.female_count,
        }[criteria.sex_preference]
        return ScoreReason(description[0].upper() + description[1:], 15) if wanted_count > 0 else None

    @staticmethod
    def _freshness_reason(snapshot: LitterSnapshot, today: date) -> ScoreReason | None:
        """
        15 on the day the litter appeared, decreasing linearly to 0 at 14 days. A litter to be born
        takes the age of its mating declaration, which is when it appeared at the Centrale Canine.
        """
        age_in_days = max(0, (today - snapshot.first_seen_on).days)
        points = round(15 * max(0.0, 1 - age_in_days / FRESHNESS_WINDOW_DAYS))
        if points <= 0:
            return None
        if age_in_days == 0:
            return ScoreReason("Apparue aujourd’hui", points)
        return ScoreReason(f"Apparue il y a {age_in_days} jour{'s' if age_in_days > 1 else ''}", points)

    @staticmethod
    def _proximity_reason(snapshot: LitterSnapshot, criteria: ProfileCriteria) -> ScoreReason | None:
        """10 for the first department of the list, then 10 × (1 − rank / count), at least 2."""
        if snapshot.department_code is None or snapshot.department_code not in criteria.department_codes:
            return None
        rank = criteria.department_codes.index(snapshot.department_code)
        points = max(MINIMUM_PROXIMITY_POINTS, round(10 * (1 - rank / len(criteria.department_codes))))
        place = snapshot.department_name or snapshot.department_code
        if rank == 0:
            return ScoreReason(f"{place}, ton département le plus proche", points)
        return ScoreReason(f"{place}, {rank + 1}e département de ta liste", points)

    @staticmethod
    def _bonus_reasons(snapshot: LitterSnapshot) -> list[ScoreReason]:
        """+3 for a selected breeding (Centrale Canine group 1), +1 per parent rated 4 or more."""
        reasons: list[ScoreReason] = []
        if snapshot.breeder_selection_group == SELECTED_BREEDING_GROUP:
            reasons.append(ScoreReason("Élevage sélectionné par la Centrale Canine", 3))
        if snapshot.sire_rating is not None and snapshot.sire_rating >= GOOD_PARENT_RATING:
            reasons.append(ScoreReason(f"Père coté {snapshot.sire_rating}/6", 1))
        if snapshot.dam_rating is not None and snapshot.dam_rating >= GOOD_PARENT_RATING:
            reasons.append(ScoreReason(f"Mère cotée {snapshot.dam_rating}/6", 1))
        return reasons
