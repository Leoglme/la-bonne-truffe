"""Read back what a run stored, for the tests that run several sources."""

from sqlalchemy.orm import Session

from models.listing import Listing


def listing_of(db: Session, external_id: str) -> Listing:
    """
    The listing of an identifier, whatever its source.

    Args:
        db: Database session.
        external_id: Identifier of the listing on its source.

    Returns:
        The listing.
    """
    return db.query(Listing).filter(Listing.external_id == external_id).one()
