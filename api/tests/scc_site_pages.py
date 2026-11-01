"""Pages of the Centrale Canine site of a breeding, shaped like the real JSON, without network."""

from typing import Any

import httpx

from core.text import without_accents
from services.collectors.scc_sites import SccSiteCollector

# The site of Élevage A: a cover photo, two gallery images, three social accounts and « mon autre site » hosted
# by Chiens de France. The site of Élevage G declares no link. The site of Élevage F is gone (404).
SITE_A_COVER_PATH = "/sites/default/files/2025-04/couverture-elevage-a.jpeg"
SITE_A_GALLERY_PATHS = ("/sites/default/files/2022-01/galerie-a-1.JPG", "/sites/default/files/2022-01/galerie-a-2.JPG")
SITE_A_FACEBOOK_PAGE_ID = "100000000000001"
SITE_A_INSTAGRAM_HANDLE = "elevage.a"
SITE_A_YOUTUBE_CHANNEL_ID = "UCelevageA00000000000000"
SITE_A_OTHER_SITE_URL = "http://elevage-a.chiens-de-france.com/cocker-spaniel-anglais.html "
SITE_A_CHIENS_DE_FRANCE_SITE_URL = "https://elevage-a.chiens-de-france.com"
SITE_A_SOCIALS: dict[str, str] = {
    "facebook_id": SITE_A_FACEBOOK_PAGE_ID,
    "instagram_id": f"@{SITE_A_INSTAGRAM_HANDLE}",
    "youtube_id": SITE_A_YOUTUBE_CHANNEL_ID,
}


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


def general_page(site_slug: str, socials: dict[str, str] | list[Any], other_site_url: str | None) -> dict[str, Any]:
    """
    The ``api/general`` JSON of a site: its menu, with « mon autre site » when the breeding declares one, and
    its social accounts in the footer.

    Args:
        site_slug: Slug of the site, which its menu paths start with.
        socials: ``footer.socials``: ``facebook_id``, ``instagram_id`` and ``youtube_id`` as declared, or the
            empty list the real site gives when nothing is declared.
        other_site_url: The address of « mon autre site », or None.

    Returns:
        The page.
    """
    menu: list[dict[str, Any]] = [
        {"is_expanded": False, "title": "Accueil", "url": f"/{site_slug}"},
        {"is_expanded": False, "title": "Les portées", "url": f"{site_slug}/nos-portees/cocker-spaniel-anglais"},
    ]
    if other_site_url is not None:
        menu.append({"is_expanded": False, "title": "mon autre site", "url": other_site_url})
    return {
        "header": {
            "main_menu": menu,
            "settings": {"main_logo": "/sites/default/files/logos/LOGO%20SCC%20POSITIF-RVB%20%281%29.jpg"},
        },
        "footer": {
            "footer_menu": [{"title": "Politique de cookies", "url": "/articles/utilisation-des-cookies"}],
            "socials": socials,
        },
        "general_data": {"backoffice_type": "simplified", "domain_type": "breeder"},
        "cache_tags": ["general:1"],
    }


def recorded_site_pages() -> dict[str, dict[str, Any]]:
    """The pages of the sites of the tests, by URL path."""
    return {
        f"/{SITE_A_SLUG}/api/homepage": homepage_page("DU CLOS DE L'ÉLEVAGE A", SITE_A_COVER_PATH),
        f"/{SITE_A_SLUG}/api/dogs": dogs_page(SITE_A_GALLERY_PATHS),
        f"/{SITE_A_SLUG}/api/general": general_page(SITE_A_SLUG, SITE_A_SOCIALS, SITE_A_OTHER_SITE_URL),
        f"/{SITE_G_SLUG}/api/homepage": homepage_page("DU CLOS DE L'ÉLEVAGE G", None),
        f"/{SITE_G_SLUG}/api/dogs": dogs_page(()),
        f"/{SITE_G_SLUG}/api/general": general_page(SITE_G_SLUG, [], None),
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
