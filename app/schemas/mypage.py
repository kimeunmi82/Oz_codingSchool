from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.users import (
    DepartmentEnum,
    GenderEnum,
    RoleEnum,
)

from datetime import datetime

import re


# 6번 마이페이지 조회
class MyPageResponse(BaseModel):
    name: str | None
    email: str | None
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str | None
    role: RoleEnum

    model_config = ConfigDict(from_attributes=True)


# 7번 회원정보 수정
class MyPageUpdateRequest(BaseModel):
    department: DepartmentEnum | None = None
    phone_number: str | None = None
      
# 비밀번호 변경
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("current_password")
    @classmethod
    def validate_current_password(cls, value: str) -> str:
        if not value:
            raise ValueError(
                "현재 비밀번호를 입력해 주세요."
            )

        if len(value) > 128:
            raise ValueError(
                "현재 비밀번호는 최대 128자까지 입력할 수 있습니다."
            )

        return value

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError(
                "새 비밀번호는 최소 8자 이상이어야 합니다."
            )

        if len(value) > 128:
            raise ValueError(
                "새 비밀번호는 최대 128자까지 입력할 수 있습니다."
            )

        required_patterns = (
            r"[a-z]",
            r"[A-Z]",
            r"\d",
            r'[!@#$%^&*(),.?":{}|<>]',
        )

        if not all(
            re.search(pattern, value)
            for pattern in required_patterns
        ):
            raise ValueError(
                "비밀번호는 영문 대문자, 영문 소문자, 숫자, "
                "특수문자를 각각 1개 이상 포함해야 합니다."
            )

        return value

    @model_validator(mode="after")
    def validate_different_passwords(self):
        if self.current_password == self.new_password:
            raise ValueError(
                "새 비밀번호는 현재 비밀번호와 달라야 합니다."
            )

        return self

class PasswordChangeResponse(BaseModel):
    message: str
    updated_at: datetime | None
