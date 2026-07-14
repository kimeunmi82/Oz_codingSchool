from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, field_validator, Field

import re
#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/practice_api")


#####################################################
# 2. 초기 데이터 정의
#####################################################
user_list = [
	{
		"id": 1,
		"name": "홍길동",
		"age": 24,
		"email": "gildong24@example.com",
		"password": "Password1234!!"
	},
	{
		"id": 2,
		"name": "장문복",
		"age": 21,
		"email": "moonluck12@example.com",
		"password": "Check1321!"
	},
	{
		"id": 3,
		"name": "임우진",
		"age": 31,
		"email": "limousine33@example.com",
		"password": "lwsPAssword12@"
	}
]

#####################################################
# 3. Pydantic 스키마 정의
#####################################################

# API 응답용 회원 정보 스키마 (비밀번호 제외)
class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str

# 회원 정보 업데이트 스키마
class UserUpdateRequest(BaseModel):
    age: int | None = Field(default=None, ge=14)
    email: str | None = Field(default=None, max_length=30)
    password: str | None = Field(default=None, min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is None:
            return value

        email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.match(email_pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if value is None:
            return value

        has_upper = re.search(r"[A-Z]", value)
        has_lower = re.search(r"[a-z]", value)
        has_special = re.search(r"[^A-Za-z0-9]", value)

        if not has_upper or not has_lower or not has_special:
            raise ValueError("비밀번호는 대문자, 소문자, 특수문자를 각각 1개 이상 포함해야 합니다.")

        return value

#####################################################
# 4. API Endpoints 구현
#####################################################
# task01 - 정현우






# task02 - 정현우






# task03 - 홍승완






# task04 - 김지혜
@router.patch("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdateRequest):
    update_data = user_update.model_dump(exclude_none=True)

    if update_data == {}:
        raise HTTPException(status_code=400, detail="수정할 항목을 입력해주세요.")

    for user in user_list:
        if user["id"] == user_id:
            user.update(update_data)
            return user

    raise HTTPException(status_code=404, detail="해당 회원을 찾을 수 없습니다.")





# task05 - 김은미
# API 5: 특정 회원의 정보를 삭제하는 API
@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    for index, user in enumerate(user_list):
        if user["id"] == user_id:
            user_list.pop(index)
            return
            
    raise HTTPException(status_code=404, detail="해당 ID의 회원을 찾을 수 없습니다.")