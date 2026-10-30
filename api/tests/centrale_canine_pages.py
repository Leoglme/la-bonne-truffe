"""The two recorded Centrale Canine pages (cocker, Ille-et-Vilaine), served to a collector without network."""

import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import httpx

from services.collectors.centrale_canine import ALL_DEPARTMENTS_FILTER, CentraleCanineCollector

FIXTURES = Path(__file__).parent / "fixtures" / "centrale_canine"

RECORDED_DEPARTMENT_TERM_ID = "t_41"

EMPTY_PAGE: dict[str, Any] = {"litters": {"count": 0, "node": []}}


def load_recorded_pages() -> list[dict[str, Any]]:
    """
    Read both recorded pages again, so that a test can change them freely.

    Returns:
        Page 0, then page 1.
    """
    return [
        json.loads((FIXTURES / f"litters_35_page_{page_number}.json").read_text(encoding="utf-8"))
        for page_number in (0, 1)
    ]


def litter_in(pages: Sequence[dict[str, Any]], litter_id: str) -> dict[str, Any]:
    """
    Find a litter of the pages, to change it in place.

    Args:
        pages: Recorded pages.
        litter_id: ``n_id`` of the litter.

    Returns:
        The litter as the page holds it.

    Raises:
        KeyError: When no page holds the litter.
    """
    for page in pages:
        for selection_group in page["litters"]["node"].values():
            if f"n{litter_id}" in selection_group:
                litter: dict[str, Any] = selection_group[f"n{litter_id}"]
                return litter
    raise KeyError(litter_id)


def remove_litter(pages: Sequence[dict[str, Any]], litter_id: str) -> None:
    """
    Take a litter off the pages, as when the breeder withdraws it.

    Args:
        pages: Recorded pages.
        litter_id: ``n_id`` of the litter.
    """
    for page in pages:
        for selection_group in page["litters"]["node"].values():
            selection_group.pop(f"n{litter_id}", None)


def mark_published_an_hour_ago(pages: Sequence[dict[str, Any]], litter_id: str) -> None:
    """
    Date the publication of a recorded litter one hour ago: every recorded litter went online weeks
    before the tests run, which is never news.

    Args:
        pages: Recorded pages.
        litter_id: ``n_id`` of the litter.
    """
    litter_in(pages, litter_id)["n_created"] = [int(time.time()) - 3600]


def declare_birth_under_new_id(
    pages: Sequence[dict[str, Any]],
    litter_id: str,
    new_litter_id: str,
    birth_timestamp: int,
    male_count: int,
    female_count: int,
) -> None:
    """
    Replace a recorded mating by its birth declared under a new identifier, as the Centrale Canine may do: same
    breeder, parents and mating number, with a litter number, the sexes and ``n_is_borned`` true.

    Args:
        pages: Recorded pages.
        litter_id: ``n_id`` of the mating.
        new_litter_id: ``n_id`` the birth is declared under.
        birth_timestamp: Birth date, as the page writes it.
        male_count: Males born.
        female_count: Females born.

    Raises:
        KeyError: When no page holds the mating.
    """
    for page in pages:
        for selection_group in page["litters"]["node"].values():
            mating = selection_group.pop(f"n{litter_id}", None)
            if mating is None:
                continue
            mating_number = mating["n_servicing_number"][0]
            birth = dict(mating)
            birth.update(
                {
                    "n_id": new_litter_id,
                    "url": f"/portee/{new_litter_id}",
                    "n_litter_number": f"LOF-{mating_number}-2026-14",
                    "n_is_borned": True,
                    "n_birth_date": [birth_timestamp],
                    "n_male_number": [male_count],
                    "n_female_number": [female_count],
                    "n_litter_status": [2],
                }
            )
            selection_group[f"n{new_litter_id}"] = birth
            return
    raise KeyError(litter_id)


def turn_gold(pages: Sequence[dict[str, Any]], litter_id: str) -> None:
    """
    Make a recorded litter gold (variety ``158``, node 345). The recorded litters « à naître » are all
    of « autres couleurs »: a test that follows a preferred litter until its birth turns one gold.

    Args:
        pages: Recorded pages.
        litter_id: ``n_id`` of the litter.
    """
    litter_in(pages, litter_id).update({"n_variety": "158", "n_variety_id": [345]})


def mark_breed_club_member(pages: Sequence[dict[str, Any]], litter_id: str) -> None:
    """
    Make the breeder of a recorded litter a member of the club of the breed: no recorded breeder is one.

    Args:
        pages: Recorded pages.
        litter_id: ``n_id`` of a litter of the breeder.
    """
    breeder_user_id = str(litter_in(pages, litter_id)["n_breeder"][0])
    for page in pages:
        breeders = page["litters"].get("breeders")
        if isinstance(breeders, dict) and breeder_user_id in breeders:
            breeders[breeder_user_id]["is_member"] = True


def collector_serving(pages: Sequence[dict[str, Any]]) -> CentraleCanineCollector:
    """
    A collector that gets the recorded pages for Ille-et-Vilaine and an empty page for any other
    department, without pausing between pages. The « all departments » page read for the department
    identifiers is the first recorded page, whose filters are those of the real response.

    Args:
        pages: Pages to serve, by page number.

    Returns:
        The collector.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the page asked for, like the real endpoint.

        Args:
            request: The collector's request.

        Returns:
            The JSON page.
        """
        department = request.url.params.get("department")
        page_number = int(request.url.path.rsplit("/", 1)[1])
        is_recorded_department = department in (RECORDED_DEPARTMENT_TERM_ID, ALL_DEPARTMENTS_FILTER)
        if is_recorded_department and page_number < len(pages):
            return httpx.Response(200, json=pages[page_number])
        return httpx.Response(200, json=EMPTY_PAGE)

    return CentraleCanineCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None
    )


def refusing_collector() -> CentraleCanineCollector:
    """
    A collector that Cloudflare refuses, as it refuses a data-centre address.

    Returns:
        The collector.
    """
    return CentraleCanineCollector(
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda _request: httpx.Response(403, headers={"cf-mitigated": "challenge"}))
        ),
        sleep=lambda _seconds: None,
    )
