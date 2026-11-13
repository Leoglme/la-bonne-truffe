"""Finds the stored breeder a source describes, in the order of docs/03 (« Le dédoublonnage »)."""

from sqlalchemy.orm import Session

from models.breeder import Breeder


class BreederMatcher:
    """Matches a breeder across sources: SIREN, then the Centrale Canine identifiers, then the phone, then the affix."""

    @staticmethod
    def find(
        db: Session,
        siren: str | None,
        scc_breeder_id: str | None,
        phone_e164: str | None,
        affix_key: str | None,
        department_code: str | None,
        scc_user_id: str | None = None,
        chiens_de_france_site_url: str | None = None,
    ) -> Breeder | None:
        """
        Match a breeder in the order of docs/03: SIREN, then the Centrale Canine breeder identifier, then its
        directory user identifier, then its own site on Chiens de France, then the phone, then the affix in the
        same department.

        Args:
            db: Database session.
            siren: SIREN the source gives, if any.
            scc_breeder_id: Centrale Canine breeder identifier (``n_breeder_id``, ``u_breeder_id``), if any.
            phone_e164: Phone the source gives, if any.
            affix_key: Normalized affix, for the last rule.
            department_code: Department of the breeding, for the last rule.
            scc_user_id: Centrale Canine directory user identifier (``u_id``), if any.
            chiens_de_france_site_url: The breeder's own site on Chiens de France, which an ad may link while it
                names no one (« https://elevage-a.chiens-de-france.com »), if any.

        Returns:
            The existing breeder, or None for a breeder never seen.
        """
        if siren is not None:
            breeder = db.query(Breeder).filter(Breeder.siren == siren).first()
            if breeder is not None:
                return breeder
        if scc_breeder_id is not None:
            breeder = db.query(Breeder).filter(Breeder.scc_breeder_id == scc_breeder_id).first()
            if breeder is not None:
                return breeder
        if scc_user_id is not None:
            breeder = db.query(Breeder).filter(Breeder.scc_user_id == scc_user_id).first()
            if breeder is not None:
                return breeder
        if chiens_de_france_site_url is not None:
            breeder = db.query(Breeder).filter(Breeder.chiens_de_france_site_url == chiens_de_france_site_url).first()
            if breeder is not None:
                return breeder
        if phone_e164 is not None:
            breeder = db.query(Breeder).filter(Breeder.phone_e164 == phone_e164).first()
            if breeder is not None:
                return breeder
        if affix_key is not None and department_code is not None:
            return (
                db.query(Breeder)
                .filter(Breeder.affix_normalized == affix_key, Breeder.department_code == department_code)
                .first()
            )
        return None

    @staticmethod
    def is_siren_taken(db: Session, siren: str, breeder_id: int) -> bool:
        """
        Whether another breeder already carries this SIREN (the column is unique).

        Args:
            db: Database session.
            siren: SIREN to store.
            breeder_id: Breeder being updated.

        Returns:
            True when another breeder has it.
        """
        return db.query(Breeder).filter(Breeder.siren == siren, Breeder.id != breeder_id).first() is not None

    @staticmethod
    def is_scc_breeder_id_taken(db: Session, scc_breeder_id: str, breeder_id: int) -> bool:
        """
        Whether another breeder already carries this Centrale Canine identifier (the column is unique).

        Args:
            db: Database session.
            scc_breeder_id: Identifier to store.
            breeder_id: Breeder being updated.

        Returns:
            True when another breeder has it.
        """
        return (
            db.query(Breeder).filter(Breeder.scc_breeder_id == scc_breeder_id, Breeder.id != breeder_id).first()
            is not None
        )

    @staticmethod
    def is_scc_user_id_taken(db: Session, scc_user_id: str, breeder_id: int) -> bool:
        """
        Whether another breeder already carries this directory user identifier (the column is unique).

        Args:
            db: Database session.
            scc_user_id: Identifier to store.
            breeder_id: Breeder being updated.

        Returns:
            True when another breeder has it.
        """
        return (
            db.query(Breeder).filter(Breeder.scc_user_id == scc_user_id, Breeder.id != breeder_id).first() is not None
        )
