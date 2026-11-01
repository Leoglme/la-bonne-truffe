"""The chip of a dog as both the Centrale Canine and the breeders' sites write it, to tell the same dog on both."""

import re

NON_DIGIT_PATTERN = re.compile(r"\D")
MIN_CHIP_DIGITS = 10


class DogChip:
    """Reads a chip number the same way whatever the source wrote around it."""

    @staticmethod
    def key_of(identifier: str | None) -> str | None:
        """
        The digits of a chip, to compare the chips two sources give.

        Args:
            identifier: The chip or the tattoo as a source writes it (« 250000000000003 », « 250 000 000 000 003 »).

        Returns:
            The digits, or None for a tattoo or a number too short to be a chip.
        """
        digits = NON_DIGIT_PATTERN.sub("", identifier or "")
        return digits if len(digits) >= MIN_CHIP_DIGITS else None
