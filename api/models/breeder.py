"""Breeder model: the anchor of the deduplication between sources, and the object of the Éleveurs tab."""

from datetime import date, datetime

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.timestamps import TimestampMixin


class Breeder(TimestampMixin, Base):
    """
    A breeder (or a private seller), matched across sources by SIREN, then phone, then affix and department.

    Attributes:
        id: Primary key.
        display_name: Name shown in the dashboard (affix, or the name the source gives).
        affix: Kennel affix, null for a breeder without one.
        affix_normalized: Affix lowercased, accents and articles removed, used to match.
        siren: French company number, unique when known.
        phone_e164: Phone in E.164 format.
        email: Contact email.
        zip_code: Postal code.
        city: Town.
        department_code: Department code.
        latitude: Latitude of the breeding, when a source gives it.
        longitude: Longitude of the breeding, when a source gives it.
        website: Breeder's website.
        scc_breeder_id: Breeder identifier at the Centrale Canine (``n_breeder_id``).
        scc_selection_group: Centrale Canine group: 1 selected, 2 with affix, 3 without affix.
        is_breed_club_member: Member of the club of the breed (the Spaniel Club Français for the cocker), as the
            Centrale Canine shows it; null until a Centrale Canine page lists the breeder.
        notes: Free notes.
        scc_user_id: User identifier of the breeder in the Centrale Canine directory (``u_id``).
        scc_breeder_number: Breeder number at the Centrale Canine (``u_breeder_number``).
        scc_site_slug: Slug of the breeder's mini-site at the Centrale Canine (``u_breeder_site``).
        logo_url: Logo the breeder uploaded at the Centrale Canine.
        scc_variety_ids: Variety identifiers the breeder produces, every breed mixed (``u_variety``).
        scc_last_litter_at: Last litter the Centrale Canine directory dates (``u_last_litter_date``).
        is_scc_selected: Selected breeding, as the directory flags it (``is_selected``).
        scc_directory_seen_at: Last time the directory of the Centrale Canine listed the breeder.
        chiens_de_france_site_url: Site of the breeder hosted by Chiens de France (``https://<slug>.chiens-de-france.com``).
        chiens_de_france_registered_on: « Inscrit sur chiens-de-france.com depuis le … ».
        breeding_females_count: « 18 femelles reproductrices au sein de l'élevage », as Chiens de France writes it.
        litters_last_year_count: « 14 portées au cours de l'année écoulée », as Chiens de France writes it.
        chiens_de_france_site_seen_at: Last time the breeder's site on Chiens de France was read.
        chiens_de_france_litters: The litters of the year its « Chiots nés chez nous » page lists, each
            ``{"birth_date", "sire_name", "dam_name"}``.
        cover_photo_url: First photo found on the breeder's site.
        scc_site_cover_url: Cover photo of the breeder's site at the Centrale Canine (``h_image_uri``).
        scc_site_photos: Gallery images of that site, absolute URLs.
        scc_site_seen_at: Last time that site was read; it rests a month between two readings.
        website_photo_url: Main photo of the breeding's own website (the image of its shares, else its first photo).
        website_read_at: Last time that website was read for its photo; a website is read once.
        facebook_url: Facebook page of the breeding, as an address.
        instagram_url: Instagram account of the breeding, as an address.
        youtube_url: YouTube channel of the breeding, as an address.
        social_link_origins: Where each of these accounts was found, ``SocialLinkOrigin`` by ``facebook``,
            ``instagram`` or ``youtube``.
        links: Links Léo added by hand, each ``{"label", "url"}`` (Facebook, Instagram, a site).
        is_manual: Created by hand from the app, before any source listed the breeder.
        created_by_user_id: User who created the breeder by hand.
        search_text: Normalized text the breeder search looks into (docs/05, ``BreederQueryService``).
    """

    __tablename__ = "breeders"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    affix: Mapped[str | None] = mapped_column(String(255))
    affix_normalized: Mapped[str | None] = mapped_column(String(255), index=True)
    siren: Mapped[str | None] = mapped_column(String(9), unique=True)
    phone_e164: Mapped[str | None] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    zip_code: Mapped[str | None] = mapped_column(String(10))
    city: Mapped[str | None] = mapped_column(String(120))
    department_code: Mapped[str | None] = mapped_column(ForeignKey("departments.code"), index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    website: Mapped[str | None] = mapped_column(String(500))
    scc_breeder_id: Mapped[str | None] = mapped_column(String(40), unique=True)
    scc_selection_group: Mapped[int | None]
    is_breed_club_member: Mapped[bool | None]
    notes: Mapped[str | None] = mapped_column(Text)
    scc_user_id: Mapped[str | None] = mapped_column(String(40), unique=True)
    scc_breeder_number: Mapped[str | None] = mapped_column(String(40))
    scc_site_slug: Mapped[str | None] = mapped_column(String(120))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    scc_variety_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    scc_last_litter_at: Mapped[datetime | None]
    is_scc_selected: Mapped[bool | None]
    scc_directory_seen_at: Mapped[datetime | None]
    chiens_de_france_site_url: Mapped[str | None] = mapped_column(String(500))
    chiens_de_france_registered_on: Mapped[date | None]
    breeding_females_count: Mapped[int | None]
    litters_last_year_count: Mapped[int | None]
    chiens_de_france_site_seen_at: Mapped[datetime | None]
    chiens_de_france_litters: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    cover_photo_url: Mapped[str | None] = mapped_column(String(500))
    scc_site_cover_url: Mapped[str | None] = mapped_column(String(500))
    scc_site_photos: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    scc_site_seen_at: Mapped[datetime | None]
    website_photo_url: Mapped[str | None] = mapped_column(String(500))
    website_read_at: Mapped[datetime | None]
    facebook_url: Mapped[str | None] = mapped_column(String(500))
    instagram_url: Mapped[str | None] = mapped_column(String(500))
    youtube_url: Mapped[str | None] = mapped_column(String(500))
    social_link_origins: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    links: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    is_manual: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    search_text: Mapped[str | None] = mapped_column(Text)

    @property
    def card_name(self) -> str | None:
        """The affix, else the name of the breeding: how the cards, the pushes and the CLI name the breeder."""
        return self.affix or self.display_name

    @property
    def site_photo_url(self) -> str | None:
        """
        The photo the sites of the breeding give: the cover of its Chiens de France site, else the cover then the
        first photo of the gallery of its Centrale Canine site, else the main photo of its own website.
        """
        return (
            self.cover_photo_url
            or self.scc_site_cover_url
            or next(iter(self.scc_site_photos), None)
            or self.website_photo_url
        )

    def __repr__(self) -> str:
        return f"<Breeder id={self.id} display_name={self.display_name}>"
