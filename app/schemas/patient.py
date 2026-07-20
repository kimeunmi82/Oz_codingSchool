from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# 환자 정보 등록 스키마
class PatientGender(str, Enum):
    MALE = "male"
    FEMALE = "female"

# Swagger 요청 데이터 검증
class PatientCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=30,
        description="환자 이름",
    )
    age: int = Field(
        ge=0,
        le=150,
        description="환자 나이",
    )
    gender: PatientGender
    phone_number: str = Field(
        pattern=r"^\d{10,11}$",
        description="숫자로 구성된 휴대폰 번호",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError(
                "이름은 비어 있을 수 없습니다."
            )

        return stripped_value

# 등록 완료 후 반환할 데이터
class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: PatientGender
    phone_number: str
    created_at: datetime
    updated_at: datetime | None


# 환자 상세 정보 조회 응답
class PatientDetailResponse(BaseModel):
    name: str
    gender: PatientGender
    phone_number: str
    age: int