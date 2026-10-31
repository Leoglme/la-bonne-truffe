"""Writes on a breeder the contact details a source gives: a value the source leaves empty never erases a known one."""

from models.breeder import Breeder
from services.collectors.breeder_contact_parser import BreederContactParser
from services.stored_value import known_or_current


def apply_breeder_contact(
    breeder: Breeder,
    *,
    display_name: str | None,
    affix: str | None,
    phone_e164: str | None,
    zip_code: str | None,
    city: str | None,
    department_code: str | None,
    latitude: float | None,
    longitude: float | None,
) -> None:
    """
    Refresh the name, the affix and its key, the phone and the place of a breeder from what a source says.

    Args:
        breeder: The breeder to update.
        display_name: Name of the person or the company, readable.
        affix: The affix, readable.
        phone_e164: Phone in E.164.
        zip_code: Postal code.
        city: Town, readable.
        department_code: Department code, already checked against the seeded departments.
        latitude: Latitude of the breeding.
        longitude: Longitude of the breeding.
    """
    breeder.display_name = known_or_current(display_name, breeder.display_name)
    breeder.affix = known_or_current(affix, breeder.affix)
    breeder.affix_normalized = known_or_current(BreederContactParser.affix_key(affix), breeder.affix_normalized)
    breeder.phone_e164 = known_or_current(phone_e164, breeder.phone_e164)
    breeder.zip_code = known_or_current(zip_code, breeder.zip_code)
    breeder.city = known_or_current(city, breeder.city)
    breeder.department_code = known_or_current(department_code, breeder.department_code)
    breeder.latitude = known_or_current(latitude, breeder.latitude)
    breeder.longitude = known_or_current(longitude, breeder.longitude)
