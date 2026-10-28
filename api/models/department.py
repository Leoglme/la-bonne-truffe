"""Department model: French departments with their Centrale Canine taxonomy identifier."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.timestamps import TimestampMixin


class Department(TimestampMixin, Base):
    """
    A French department.

    Attributes:
        code: Official code (« 35 », « 2A »), primary key.
        name: Name (« Ille-et-Vilaine »).
        region: Region the department belongs to (« Bretagne »).
        scc_term_id: Centrale Canine taxonomy identifier (``t_41``) expected by its ``department`` filter;
            read from the « Département » ``<select>`` of the breed page, null until read.
    """

    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    scc_term_id: Mapped[str | None] = mapped_column(String(20), unique=True)

    def __repr__(self) -> str:
        return f"<Department code={self.code} scc_term_id={self.scc_term_id}>"
