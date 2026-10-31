"""Pages of the Centrale Canine breeder directory and of the Spaniel Club, shaped like the real JSON, without network."""

from typing import Any

import httpx

from services.collectors.scc_breeders import CLUB_API_PATH, SccBreederDirectoryCollector

RECORDED_DEPARTMENT_TERM_ID = "t_41"

# The breeder of the recorded litters 4337070 and 4320820 (Élevage A), as the directory lists it.
BREEDER_A_ID = "266172"
BREEDER_A_USER_ID = "72101"

# A breeder the recorded litters never named, with no litter ever.
BREEDER_F_ID = "999001"
BREEDER_F_USER_ID = "900001"

# A member of the club, out of the recorded departments.
BREEDER_G_ID = "999002"
BREEDER_G_USER_ID = "900002"

EMPTY_DIRECTORY_PAGE: dict[str, Any] = {"breeders": {"count": 0, "users": [], "filters": {}}}


def directory_user(
    breeder_id: str,
    user_id: str,
    affix: str,
    name: str,
    siren: str,
    phone: str,
    zip_code: str,
    town: str,
    location: str,
    varieties: list[str],
    last_litter_timestamp: int | None,
    is_member: bool,
    logo_path: str = "",
) -> dict[str, Any]:
    """
    One entry of the directory, with the Drupal one-element lists of the real page.

    Args:
        breeder_id: ``u_breeder_id``, the identifier the litters carry as ``n_breeder_id``.
        user_id: ``u_id``.
        affix: Affix in capitals, as published.
        name: Name of the person in capitals, as published.
        siren: SIREN, empty when confidential.
        phone: Phone, empty when confidential.
        zip_code: Postal code.
        town: Town in capitals.
        location: ``"lat,long"``.
        varieties: Variety identifiers produced.
        last_litter_timestamp: ``u_last_litter_date``, None for a breeder without any litter.
        is_member: Whether the breed club lists the breeder.
        logo_path: ``u_user_picture_uri``, empty without a logo.

    Returns:
        The entry.
    """
    return {
        "mail": "jamais.garde@exemple.fr",
        "u_breed": ["1728"],
        "u_breeder_address_3": "1 RUE DE TEST",
        "u_breeder_country": "FRANCE",
        "u_breeder_department": "41",
        "u_breeder_id": [int(breeder_id)],
        "u_breeder_number": f"35{breeder_id[-4:]}",
        "u_breeder_phone": phone,
        "u_breeder_siren": siren,
        "u_breeder_site": affix.lower().replace(" ", "-").replace("'", ""),
        "u_breeder_status": True,
        "u_breeder_town": town,
        "u_breeder_zip_code": zip_code,
        "u_farming_affix": affix,
        "u_farming_name": name,
        "u_id": user_id,
        "u_is_breeder": True,
        "u_last_litter_date": [last_litter_timestamp] if last_litter_timestamp is not None else [],
        "u_location": [location],
        "u_user_picture_uri": logo_path,
        "u_variety": varieties,
        "is_member": is_member,
        "is_selected": False,
    }


def directory_page(users: list[dict[str, Any]], count: int) -> dict[str, Any]:
    """
    One page of the directory.

    Args:
        users: Its entries.
        count: ``breeders.count``, the total over the pages.

    Returns:
        The page.
    """
    return {"breed": {"breed_title": "Cocker spaniel anglais"}, "breeders": {"count": count, "users": users}}


def breeder_a_entry(is_member: bool = False) -> dict[str, Any]:
    """The directory entry of Élevage A, the breeder of the recorded litters."""
    return directory_user(
        BREEDER_A_ID,
        BREEDER_A_USER_ID,
        "DU CLOS DE L'ÉLEVAGE A",
        "ÉLEVEUSE DE TEST A",
        "000000001",
        "0600000001",
        "35140",
        "SAINT-AUBIN-DU-CORMIER",
        "48.26,-1.40",
        ["158", "159"],
        1792843200,
        is_member,
        logo_path="/sites/default/files/logos/logo-a.jpg",
    )


def breeder_f_entry() -> dict[str, Any]:
    """The directory entry of Élevage F, never seen in a litter, without any litter yet."""
    return directory_user(
        BREEDER_F_ID,
        BREEDER_F_USER_ID,
        "DU CLOS DE L'ÉLEVAGE F",
        "ÉLEVEUR DE TEST F",
        "000000006",
        "0600000006",
        "35000",
        "RENNES",
        "48.11,-1.68",
        ["158"],
        None,
        False,
    )


def breeder_g_entry() -> dict[str, Any]:
    """The club entry of Élevage G, out of the recorded departments."""
    return directory_user(
        BREEDER_G_ID,
        BREEDER_G_USER_ID,
        "DU CLOS DE L'ÉLEVAGE G",
        "ÉLEVEUSE DE TEST G",
        "000000007",
        "0600000007",
        "56000",
        "VANNES",
        "47.65,-2.76",
        ["158"],
        1790000000,
        True,
    )


def recorded_directory_pages() -> list[dict[str, Any]]:
    """The directory of Ille-et-Vilaine: two breeders, on two pages so that the count is followed."""
    return [directory_page([breeder_a_entry()], 11), directory_page([breeder_f_entry()], 11)]


def recorded_club_pages() -> list[dict[str, Any]]:
    """The club list: Élevage G, and Élevage A as a member."""
    return [directory_page([breeder_g_entry(), breeder_a_entry(is_member=True)], 2)]


def answer_directory_request(request: httpx.Request) -> httpx.Response:
    """
    Serve a directory or club page like the real endpoints, an empty page for the other departments.

    Args:
        request: The collector's request.

    Returns:
        The JSON page.
    """
    page_number = int(request.url.path.rsplit("/", 1)[1])
    if request.url.path.startswith(CLUB_API_PATH):
        pages = recorded_club_pages()
    elif request.url.params.get("department") == RECORDED_DEPARTMENT_TERM_ID:
        pages = recorded_directory_pages()
    else:
        pages = []
    page = pages[page_number] if page_number < len(pages) else EMPTY_DIRECTORY_PAGE
    return httpx.Response(200, json=page)


def directory_collector_serving(requests: list[httpx.Request] | None = None) -> SccBreederDirectoryCollector:
    """
    A collector that gets the pages above, without pausing between pages.

    Args:
        requests: Filled with every request sent, when given.

    Returns:
        The collector.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Record the request and serve its page.

        Args:
            request: The collector's request.

        Returns:
            The JSON page.
        """
        if requests is not None:
            requests.append(request)
        return answer_directory_request(request)

    return SccBreederDirectoryCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None
    )
