from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, String, func, text, Column
from sqlalchemy.orm import  Mapped, mapped_column

from app.core.db.databases import Base

class GenderEnum(str, Enum):
    M = "M"
    F = "F"


class RoleEnum(str, Enum):
    PENDING = "PENDING"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class DepartmentEnum(str, Enum):
    MEDICAL = "MEDICAL"
    DEV = "DEV"
    RESEARCH = "RESEARCH"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
    )
    email: Mapped[str | None] = mapped_column(
        String(255), 
        unique=True, 
        nullable=True
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255), 
        nullable=True,        
        comment="평문 저장 x -> 해쉬화 된 비밀번호 저장",
    )
    name: Mapped[str | None] = mapped_column(
        String(20), 
        nullable=True
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20), 
        unique=True, 
        nullable=True,       
        comment="유저 휴대폰 번호",
    )
    gender: Mapped[GenderEnum] = mapped_column(
        SQLEnum(GenderEnum, name="gender"),
        nullable=False,        
        comment="성별 선택",
    )
    department: Mapped[DepartmentEnum] = mapped_column(
        SQLEnum(DepartmentEnum, name="department"),
        nullable=False,        
        comment="부서 선택",
    )
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum, name="role"),
        nullable=False,        
        comment="부여된 역할 권한",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
        comment="계정 활성화 여부",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="유저 생성 일시",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=func.now(),
        comment="유저 정보 수정 일시",
    )


