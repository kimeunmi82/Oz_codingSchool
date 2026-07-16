from pydantic import BaseModel, ConfigDict
from app.models.users import DepartmentEnum, GenderEnum, RoleEnum




#6번 마이페이지 조회
class MyPageResponse(BaseModel):
    name: str | None
    email: str | None
    department: DepartmentEnum
    gender: GenderEnum
    phone_number: str | None
    role: RoleEnum

    model_config = ConfigDict(from_attributes=True)


#7번 회원정보 수정
class MyPageUpdateRequest(BaseModel):
    department: DepartmentEnum | None = None
    phone_number: str | None = None


