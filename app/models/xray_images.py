from datetime import datetime  # DB의 DATETIME 컬럼 타입

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String  # Python에서 사용하는 날짜 객체
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base

from app.core.db.models import TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.medical_records import MedicalRecord


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
        Integer,
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
    
    # MedicalRecord 테이블과 연결
     
    medical_record: Mapped["MedicalRecord"] = relationship(
    back_populates="xray_images",
)