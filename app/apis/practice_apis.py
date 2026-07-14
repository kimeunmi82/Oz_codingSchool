from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

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


#####################################################
# 4. API Endpoints 구현
#####################################################
# task01 - 정현우






# task02 - 정현우






# task03 - 홍승완






# task04 - 김지혜






# task05 - 김은미
# API 5: 특정 회원의 정보를 삭제하는 API
@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    for index, user in enumerate(user_list):
        if user["id"] == user_id:
            user_list.pop(index)
            return
            
    raise HTTPException(status_code=404, detail="해당 ID의 회원을 찾을 수 없습니다.")