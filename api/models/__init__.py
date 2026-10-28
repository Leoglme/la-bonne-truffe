"""
Every SQLAlchemy model, imported here so that importing ``models`` registers all the tables.
"""

from models.breed import Breed
from models.breed_variety import BreedVariety
from models.breeder import Breeder
from models.department import Department
from models.follow_up import FollowUp, FollowUpNote
from models.listing import Listing
from models.listing_change import ListingChange
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from models.notification import Notification
from models.push_subscription import PushSubscription
from models.search_profile import SearchProfile
from models.source_run import SourceRun
from models.user import User

__all__ = [
    "Breed",
    "BreedVariety",
    "Breeder",
    "Department",
    "FollowUp",
    "FollowUpNote",
    "Listing",
    "ListingChange",
    "ListingMatch",
    "LitterGroup",
    "Notification",
    "PushSubscription",
    "SearchProfile",
    "SourceRun",
    "User",
]
