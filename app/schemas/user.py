from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.users import DepartmentEnum, GenderEnum, RoleEnum


class UserListItem(BaseModel):
    id: int
    email: str | None
    name: str | None
    phone_number: str | None
    gender: GenderEnum
    department: DepartmentEnum
    role: RoleEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

#5번 권한 변경
class UserRoleUpdateRequest(BaseModel):
    role: RoleEnum