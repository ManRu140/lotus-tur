from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MediaAsset(Base):
    """Metadata for one uploaded file. The file itself lives on disk
    under app/static/uploads/<stored_filename> (see admin_media.py for
    the upload handler and the security checks applied there).
    """

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Random, extension-preserving filename actually used on disk —
    # deliberately NOT derived from the user-supplied original filename,
    # to rule out path traversal and filename-collision overwrites.
    stored_filename: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(256))
    content_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)

    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    uploaded_by: Mapped["User"] = relationship(foreign_keys=[uploaded_by_id])

    @property
    def url(self) -> str:
        return f"/static/uploads/{self.stored_filename}"
