"""Generation of the VAPID key pair that signs the Web Push messages."""

import base64
from dataclasses import dataclass

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid01


@dataclass(frozen=True)
class VapidKeyPair:
    """The two values to paste into ``.env``."""

    public_key: str
    private_key_b64: str


class VapidKeyGenerator:
    """Creates a VAPID key pair in the formats ``.env`` expects."""

    @staticmethod
    def generate() -> VapidKeyPair:
        """
        Generate a new P-256 key pair.

        Returns:
            ``VAPID_PUBLIC_KEY`` (base64url uncompressed point, what the browser expects as
            ``applicationServerKey``) and ``VAPID_PRIVATE_KEY_B64`` (base64 of the PKCS8 PEM).
        """
        vapid = Vapid01()
        vapid.generate_keys()
        public_point = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        return VapidKeyPair(
            public_key=base64.urlsafe_b64encode(public_point).rstrip(b"=").decode("ascii"),
            private_key_b64=base64.b64encode(vapid.private_pem()).decode("ascii"),
        )
