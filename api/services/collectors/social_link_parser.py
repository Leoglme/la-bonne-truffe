"""Turns what a site declares as its social accounts (an address, a numeric page id, a handle) into addresses."""

import re
from urllib.parse import urlparse

HTTP_SCHEME_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
DIGITS_PATTERN = re.compile(r"^\d+$")
YOUTUBE_CHANNEL_ID_PATTERN = re.compile(r"^UC[\w-]{22}$")

FACEBOOK_ACCOUNT = "facebook"
INSTAGRAM_ACCOUNT = "instagram"
YOUTUBE_ACCOUNT = "youtube"
SOCIAL_ACCOUNTS: tuple[str, ...] = (FACEBOOK_ACCOUNT, INSTAGRAM_ACCOUNT, YOUTUBE_ACCOUNT)
ACCOUNTS_BY_HOST: dict[str, str] = {
    "facebook.com": FACEBOOK_ACCOUNT,
    "fb.com": FACEBOOK_ACCOUNT,
    "instagram.com": INSTAGRAM_ACCOUNT,
    "youtube.com": YOUTUBE_ACCOUNT,
}
NOT_AN_ACCOUNT_PATH_PREFIXES: tuple[str, ...] = (
    "/sharer",
    "/share",
    "/plugins",
    "/dialog",
    "/tr",
    "/hashtag/",
    "/p/",
    "/reel/",
    "/watch",
    "/embed/",
    "/shorts/",
)
HOST_PREFIXES_DROPPED: tuple[str, ...] = ("www.", "m.", "web.")


class SocialLinkParser:
    """Normalizes the Facebook, Instagram and YouTube values a site gives, each into the address of the account."""

    @staticmethod
    def account_of_address(address: str) -> str | None:
        """
        The social account an address leads to, when it leads to the page of an account.

        Args:
            address: A link of a page (« https://www.facebook.com/elevage.a », « https://instagram.com/elevage.a »).

        Returns:
            « facebook », « instagram » or « youtube »; None for another site, or for a share button, a post or a
            video rather than the account itself.
        """
        parsed = urlparse(address.strip())
        host = parsed.netloc.lower()
        for prefix in HOST_PREFIXES_DROPPED:
            host = host.removeprefix(prefix)
        account = ACCOUNTS_BY_HOST.get(host)
        path = parsed.path.lower()
        if account is None or path in ("", "/") or path.startswith(NOT_AN_ACCOUNT_PATH_PREFIXES):
            return None
        return account

    @classmethod
    def accounts_in(cls, addresses: list[str]) -> dict[str, str]:
        """
        The first address of each social account among the links of a page.

        Args:
            addresses: The links, in page order.

        Returns:
            Address by account (``facebook``, ``instagram``, ``youtube``), for those found.
        """
        accounts: dict[str, str] = {}
        for address in addresses:
            account = cls.account_of_address(address)
            if account is not None:
                accounts.setdefault(account, address.strip())
        return accounts

    @classmethod
    def facebook(cls, value: str | None) -> str | None:
        """
        The address of a Facebook page: the address given, the page by its numeric id, or the page by its name.

        Args:
            value: ``facebook_id`` as declared: ``https://www.facebook.com/elevage.a/``, ``100000000000001``,
                ``www.facebook.com/elevage.a`` or ``Elevage-A-Cockers``.

        Returns:
            The address, or None when the site declares none.
        """
        address = cls._declared(value)
        if address is None:
            return None
        if HTTP_SCHEME_PATTERN.match(address):
            return address
        handle = address.strip("@/")
        if "facebook.com/" in handle:
            return f"https://{handle}"
        if DIGITS_PATTERN.match(handle):
            return f"https://www.facebook.com/profile.php?id={handle}"
        return f"https://www.facebook.com/{handle}"

    @classmethod
    def instagram(cls, value: str | None) -> str | None:
        """
        The address of an Instagram account: the address given, or the account by its handle.

        Args:
            value: ``instagram_id`` as declared: ``elevage.a``, ``@elevage.a`` or an address.

        Returns:
            The address, or None when the site declares none.
        """
        address = cls._declared(value)
        if address is None:
            return None
        if HTTP_SCHEME_PATTERN.match(address):
            return address
        handle = address.strip("@/")
        if "instagram.com/" in handle:
            return f"https://{handle}"
        return f"https://www.instagram.com/{handle}/"

    @classmethod
    def youtube(cls, value: str | None) -> str | None:
        """
        The address of a YouTube channel: the address given, the channel by its id (``UC…``), or by its handle.

        Args:
            value: ``youtube_id`` as declared: ``UCelevageA00000000000000``, ``@elevagea`` or an address.

        Returns:
            The address, or None when the site declares none.
        """
        address = cls._declared(value)
        if address is None:
            return None
        if HTTP_SCHEME_PATTERN.match(address):
            return address
        handle = address.strip("@/")
        if "youtube.com/" in handle or "youtu.be/" in handle:
            return f"https://{handle}"
        if YOUTUBE_CHANNEL_ID_PATTERN.match(handle):
            return f"https://www.youtube.com/channel/{handle}"
        return f"https://www.youtube.com/@{handle}"

    @staticmethod
    def _declared(value: str | None) -> str | None:
        """
        The value without the spaces around it.

        Args:
            value: The declared value.

        Returns:
            The value, or None when nothing is declared.
        """
        declared = (value or "").strip()
        return declared or None
