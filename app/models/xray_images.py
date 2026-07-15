from datetime import datetime  # DB의 DATETIME 컬럼 타입

from sqlalchemy import ForeignKey, BigInteger, String, DateTime  # Python에서 사용하는 날짜 객체
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base

from app.core.db.models import UUIDMixin, TimestampMixin


class XrayImages(Base, TimestampMixin):
    __tablename__ = "xray_images"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement= True
    )
    record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("medical_records.id"),
        nullable=False,
        index=True
    )
    uploader_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    image_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    shooting_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
