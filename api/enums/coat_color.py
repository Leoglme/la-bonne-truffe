"""Canonical coat colours shared by every source (see docs/03-modele-de-donnees.md)."""

from enum import StrEnum


class CoatColor(StrEnum):
    """Canonical coat colours shared by every source (see docs/03-modele-de-donnees.md)."""

    GOLD = "gold"
    NOIR = "noir"
    NOIR_ET_FEU = "noir_et_feu"
    MARRON = "marron"
    MARRON_ET_FEU = "marron_et_feu"
    BLEU_ROUAN = "bleu_rouan"
    ORANGE_ROUAN = "orange_rouan"
    MARRON_ROUAN = "marron_rouan"
    TRICOLORE = "tricolore"
    PARTICOLORE = "particolore"
    ZIBELINE = "zibeline"
    INCONNUE = "inconnue"
