from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.users import DepartmentEnum, GenderEnum, RoleEnum


# 회원가입 스키마
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = Field(min_length=1, max_length=20)
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        password_pattern = (
            r"^(?=.*[a-z])"
            r"(?=.*[A-Z])"
            r"(?=.*\d)"
            r"(?=.*[!@#$%^&*(),.?\":{}|<>])"
            r".{8,}$"
        )

        if not re.match(password_pattern, value):
            raise ValueError(
                "비밀번호는 영문 대문자, 영문 소문자, 숫자, "
                "특수문자를 각각 1개 이상 포함한 8자리 이상이어야 합니다."
            )

        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not re.match(r"^010-\d{4}-\d{4}$", value):
            raise ValueError(
                "휴대폰 번호는 010-1234-5678 형식이어야 합니다."
            )

        return value


class UserCreateResponse(BaseModel):
    id: int
    email: str
    name: str
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str
    role: RoleEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)




# 회원 정보 조회 스키마 - 정보 조회에 필요없는 항목 제거 
class UserListItem(BaseModel):
    id: int
    email: str | None
    name: str | None
    phone_number: str | None
    gender: GenderEnum
    department: DepartmentEnum
    role: RoleEnum
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


#5번 권한 변경
class UserRoleUpdateRequest(BaseModel):
    role: RoleEnum


