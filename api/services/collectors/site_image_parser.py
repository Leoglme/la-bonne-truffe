"""Finds the photo a page of a breeder's website puts forward: the image of its shares, else its first photo."""

from urllib.parse import urljoin, urlparse

from selectolax.lexbor import LexborHTMLParser, LexborNode

SHARE_IMAGE_KEYS: frozenset[str] = frozenset({"og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"})
IMAGE_SOURCE_ATTRIBUTES: tuple[str, ...] = ("src", "data-src", "data-lazy-src")
LOGO_WORDS: tuple[str, ...] = ("logo", "icon", "favicon", "avatar", "sprite")
PHOTO_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".webp")
DRAWING_EXTENSIONS: tuple[str, ...] = (".png",)
SMALLEST_PHOTO_SIDE = 300
WIX_MEDIA_HOST = "static.wixstatic.com"
WIX_RESIZING_MARK = "/v1/"


class SiteImageParser:
    """Picks the main photo of a page, leaving out logos, icons and thumbnails."""

    @classmethod
    def main_photo(cls, tree: LexborHTMLParser, page_url: str) -> str | None:
        """
        The photo a page puts forward: the image its shares show (``og:image``, ``twitter:image``) unless it is a
        logo, else its first photo large enough, a JPEG or a WebP before a PNG.

        Args:
            tree: The parsed page.
            page_url: Its address, which the image addresses are relative to.

        Returns:
            The address of the photo, or None when the page shows none.
        """
        for meta in tree.css("meta[content]"):
            key = (meta.attributes.get("property") or meta.attributes.get("name") or "").strip().lower()
            address = cls._absolute(meta.attributes.get("content"), page_url) if key in SHARE_IMAGE_KEYS else None
            if address is not None and not cls._is_logo(address):
                return address
        photos = [address for image in tree.css("img") if (address := cls._photo_of(image, page_url)) is not None]
        for extensions in (PHOTO_EXTENSIONS, DRAWING_EXTENSIONS):
            for address in photos:
                if urlparse(address).path.lower().endswith(extensions):
                    return address
        return None

    @classmethod
    def _photo_of(cls, image: LexborNode, page_url: str) -> str | None:
        """
        The address of an image of the page, when it can be a photo of the breeding: not a logo or an icon, and
        not declared smaller than ``SMALLEST_PHOTO_SIDE`` pixels. An image Wix resizes gives its original.

        Args:
            image: An ``img`` of the page, its address in ``src`` or, loaded later, in ``data-src``.
            page_url: The address of the page.

        Returns:
            The absolute address, or None for an image left out.
        """
        source = next(
            (image.attributes.get(name) for name in IMAGE_SOURCE_ATTRIBUTES if image.attributes.get(name)), None
        )
        address = cls._absolute(source, page_url)
        if address is None or cls._is_logo(address):
            return None
        for side in (image.attributes.get("width"), image.attributes.get("height")):
            if side is not None and side.strip().isdigit() and int(side) < SMALLEST_PHOTO_SIDE:
                return None
        parsed = urlparse(address)
        if parsed.netloc == WIX_MEDIA_HOST and WIX_RESIZING_MARK in parsed.path:
            return address.split(WIX_RESIZING_MARK, 1)[0]
        return address

    @staticmethod
    def _absolute(value: str | None, page_url: str) -> str | None:
        """
        An image address made absolute.

        Args:
            value: The address as the page writes it, maybe relative.
            page_url: The address of the page.

        Returns:
            The http(s) address, or None for an empty value or an image written in the page (``data:``).
        """
        text = (value or "").strip()
        if not text or text.startswith("data:"):
            return None
        address = urljoin(page_url, text)
        return address if urlparse(address).scheme in ("http", "https") else None

    @staticmethod
    def _is_logo(address: str) -> bool:
        """
        Whether an image is a logo or an icon, by its file name.

        Args:
            address: The address of the image.

        Returns:
            True for « logo-elevage.png », « favicon.ico », « icon-192.png ».
        """
        file_name = urlparse(address).path.rsplit("/", 1)[-1].lower()
        return any(word in file_name for word in LOGO_WORDS)
