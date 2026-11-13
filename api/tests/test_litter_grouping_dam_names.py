"""Whether two listings name the same mother, as the grouping of a litter judges it."""

from models.listing import Listing
from services.litter_grouping import LitterGroupingService


def listing_of(dam_name: str | None) -> Listing:
    """
    A listing that names a mother.

    Args:
        dam_name: The mother as a source writes her, None when it names none.

    Returns:
        The listing, not stored.
    """
    return Listing(dam_name=dam_name)


def test_a_source_that_leaves_out_the_second_name_of_the_mother_still_names_her() -> None:
    declared = listing_of("Tahiti Robyroc du Domaine de la Pruneraie")

    assert LitterGroupingService._has_same_dam(declared, listing_of("Tahiti Du Domaine De La Pruneraie"))
    assert LitterGroupingService._has_same_dam(declared, listing_of("CH. Tahiti Robyroc du Domaine de la Pruneraie"))
    assert LitterGroupingService._has_same_dam(declared, listing_of(None))
    assert not LitterGroupingService._has_same_dam(declared, listing_of("Topaze Blue du Domaine de la Pruneraie"))
