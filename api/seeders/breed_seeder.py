"""Seeder of the breeds and of their colour varieties on each source."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.listing_source import ListingSource
from models.breed import Breed
from models.breed_variety import BreedVariety

COCKER_SLUG = "cocker-spaniel-anglais"


@dataclass(frozen=True)
class VarietySeed:
    """A colour variety to create, as documented in docs/03-modele-de-donnees.md."""

    source_variety_id: str | None
    label: str
    covered_colors: tuple[CoatColor, ...]


COCKER_SCC_VARIETIES: tuple[VarietySeed, ...] = (
    VarietySeed("158", "rouge et doré", (CoatColor.GOLD,)),
    VarietySeed(
        "159",
        "noir, noir et feu, marron, marron et feu",
        (CoatColor.NOIR, CoatColor.NOIR_ET_FEU, CoatColor.MARRON, CoatColor.MARRON_ET_FEU),
    ),
    VarietySeed(
        "317",
        "autres couleurs",
        (
            CoatColor.BLEU_ROUAN,
            CoatColor.ORANGE_ROUAN,
            CoatColor.MARRON_ROUAN,
            CoatColor.TRICOLORE,
            CoatColor.PARTICOLORE,
        ),
    ),
)


class BreedSeeder:
    """Creates the cocker spaniel anglais and keeps its Centrale Canine varieties as seeded."""

    def run(self, db: Session) -> int:
        """
        Seed the breed and its varieties. A variety already there, found by its label, gets the
        identifier and the colours of its seed: a database seeded before 28/10/2026 holds « 317 » for
        gold, the identifier then assumed.

        Args:
            db: Database session.

        Returns:
            Number of rows created (breed and varieties).
        """
        created_count = 0
        cocker = db.query(Breed).filter(Breed.slug == COCKER_SLUG).first()
        if cocker is None:
            cocker = Breed(
                name_fr="Cocker spaniel anglais",
                slug=COCKER_SLUG,
                scc_slug="cocker-spaniel-anglais",
                scc_breed_id=237,
                is_active=True,
            )
            db.add(cocker)
            db.flush()
            created_count += 1

        existing_by_label = {
            variety.label: variety
            for variety in db.query(BreedVariety).filter(
                BreedVariety.breed_id == cocker.id, BreedVariety.source == ListingSource.CENTRALE_CANINE
            )
        }
        for seed in COCKER_SCC_VARIETIES:
            variety = existing_by_label.get(seed.label)
            if variety is None:
                variety = BreedVariety(breed_id=cocker.id, source=ListingSource.CENTRALE_CANINE, label=seed.label)
                db.add(variety)
                created_count += 1
            variety.source_variety_id = seed.source_variety_id
            variety.covered_colors = [color.value for color in seed.covered_colors]
            variety.is_ambiguous = len(seed.covered_colors) > 1
        db.commit()
        return created_count
