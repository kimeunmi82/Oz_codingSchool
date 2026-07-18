from pydantic import BaseModel, EmailStr, Field
from app.models.users import DepartmentEnum, RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=1, description="사용자 비밀번호")

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    department: DepartmentEnum
    role: RoleEnum

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

class RefreshTokenResponse(BaseModel):
    access_token: str
    
class MessageResponse(BaseModel):
    detail: str    