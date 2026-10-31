"""Pages of the Centrale Canine site of a breeding, shaped like the real JSON, without network."""

from typing import Any

import httpx

from core.text import without_accents
from services.collectors.scc_sites import SccSiteCollector

# The site of Élevage A: a cover photo and two gallery images. The site of Élevage F is gone (404).
SITE_A_COVER_PATH = "/sites/default/files/2025-04/couverture-elevage-a.jpeg"
SITE_A_GALLERY_PATHS = ("/sites/default/files/2022-01/galerie-a-1.JPG", "/sites/default/files/2022-01/galerie-a-2.JPG")


def site_slug_of(affix: str) -> str:
    """
    The slug the directory gives a breeding (``u_breeder_site``), as the test entries build it.

    Args:
        affix: The affix, in capitals as published.

    Returns:
        « du-clos-de-lelevage-a ».
    """
    return without_accents(affix).lower().replace(" ", "-").replace("'", "")


SITE_A_SLUG = site_slug_of("DU CLOS DE L'ÉLEVAGE A")
SITE_F_SLUG = site_slug_of("DU CLOS DE L'ÉLEVAGE F")
SITE_G_SLUG = site_slug_of("DU CLOS DE L'ÉLEVAGE G")


def homepage_page(title: str, cover_path: str | None) -> dict[str, Any]:
    """
    The ``api/homepage`` JSON of a site.

    Args:
        title: ``h_main_title``.
        cover_path: ``h_image_uri``, empty when the breeding has no cover.

    Returns:
        The page.
    """
    return {
        "main_content": {
            "h_domain": title.lower().replace(" ", "_"),
            "h_gallery": [],
            "h_image_uri": cover_path or "",
            "h_main_title": title,
            "h_show_gallery": False,
            "h_show_news": True,
            "h_widgets": [],
        },
        "cache_tags": ["homepage:1"],
    }


def dogs_page(gallery_paths: tuple[str, ...]) -> dict[str, Any]:
    """
    The ``api/dogs`` JSON of a site, whose ``media`` block lists the gallery images.

    Args:
        gallery_paths: ``m_image_uri`` of each image.

    Returns:
        The page.
    """
    media: dict[str, Any] = {
        str(150000 + index): {"m_bundle": "gallery_image", "m_id": str(150000 + index), "m_image_uri": path}
        for index, path in enumerate(gallery_paths)
    }
    media["999"] = {"m_bundle": "document", "m_id": "999", "m_image_uri": "/sites/default/files/reglement.pdf"}
    return {"main_content": {"n_type": "page", "n_title": "Les chiens"}, "media": media}


def recorded_site_pages() -> dict[str, dict[str, Any]]:
    """The pages of the sites of the tests, by URL path."""
    return {
        f"/{SITE_A_SLUG}/api/homepage": homepage_page("DU CLOS DE L'ÉLEVAGE A", SITE_A_COVER_PATH),
        f"/{SITE_A_SLUG}/api/dogs": dogs_page(SITE_A_GALLERY_PATHS),
        f"/{SITE_G_SLUG}/api/homepage": homepage_page("DU CLOS DE L'ÉLEVAGE G", None),
        f"/{SITE_G_SLUG}/api/dogs": dogs_page(()),
    }


def answer_site_request(request: httpx.Request) -> httpx.Response:
    """
    Serve a site page like the real endpoints; a site unknown here is gone (404).

    Args:
        request: The collector's request.

    Returns:
        The JSON page.
    """
    page = recorded_site_pages().get(request.url.path)
    if page is None:
        return httpx.Response(404, json={"message": "Document not found"})
    return httpx.Response(200, json=page)


def site_collector_serving(requests: list[httpx.Request] | None = None) -> SccSiteCollector:
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
        return answer_site_request(request)

    return SccSiteCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None
    )
