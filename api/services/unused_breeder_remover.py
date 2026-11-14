"""Removes a breeder nothing names any more: its ads found their real breeder, and no directory lists it."""

from sqlalchemy.orm import Session

from models.breeder import Breeder
from models.breeder_follow import BreederFollow
from models.dog import Dog
from models.listing import Listing
from models.litter_group import LitterGroup


def remove_breeder_left_with_nothing(db: Session, breeder_id: int) -> bool:
    """
    Delete a breeder once no listing, litter, dog or follow points at it. A breeder a directory lists (SIREN,
    Centrale Canine identifiers, its site on Chiens de France) stays, as does one Léo created or annotated by hand.

    Args:
        db: Database session; flushed.
        breeder_id: The breeder a listing or a litter just left.

    Returns:
        Whether the breeder was deleted.
    """
    breeder = db.get(Breeder, breeder_id)
    if breeder is None:
        return False
    is_listed_by_a_directory = any(
        (breeder.siren, breeder.scc_breeder_id, breeder.scc_user_id, breeder.chiens_de_france_site_url)
    )
    is_kept_by_hand = breeder.is_manual or bool(breeder.notes) or bool(breeder.links)
    is_still_used = any(
        db.query(model).filter(model.breeder_id == breeder_id).first() is not None
        for model in (Listing, LitterGroup, Dog, BreederFollow)
    )
    if is_listed_by_a_directory or is_kept_by_hand or is_still_used:
        return False
    db.delete(breeder)
    db.flush()
    return True
