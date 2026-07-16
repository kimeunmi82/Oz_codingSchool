from fastapi import APIRouter, HTTPException, status, Path, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator, StringConstraints
import re
from typing import Annotated
from app.schemas.mypage import MyPageResponse, MyPageUpdateRequest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db.databases import async_get_db
from app.models.users import User
from sqlalchemy import select


#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/mypage_api")

#####################################################
# 2. API Endpoints 구현
#####################################################

# # 회원탈퇴 API 
# # 탈퇴는 별도 schema가 없어서 만들지 않았습니다.
# # 로그인 담당자(은미님)의 get_current_user 인증 의존성이 완성되면 함수를 연결해야 합니다. 우선 주석처리 하겠습니다. 
 

# @router.delete(
#     "/v1/mypage",
#     status_code=status.HTTP_204_NO_CONTENT,
#     summary="회원 탈퇴 API",
#     description="로그인한 사용자의 계정을 비활성화합니다.",
# )
# async def delete_my_account(
#     response: Response,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(async_get_db),
# ):
#     if not current_user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="이미 탈퇴한 사용자입니다.",
#         )

#     # 사용자를 DB에서 삭제하지 않고 비활성화
#     current_user.is_active = False

#     await db.commit()

#     # 브라우저의 Refresh Token 쿠키 삭제
#     response.delete_cookie(
#         key="refresh_token",
#         path="/",
#         secure=True,
#         httponly=True,
#         samesite="lax",
#     )

#     response.status_code = status.HTTP_204_NO_CONTENT
#     return response



# 6. 마이페이지 조회
@router.get("/v1/users/me", response_model=MyPageResponse)
async def get_my_page(db: AsyncSession = Depends(async_get_db)):
    
    result = await db.execute(select(User).where(User.id == 1)) #테스트로 1로 정의
    user = result.scalar_one_or_none()
    return user

# 7. 회원 정보 수정
@router.patch("/v1/users/me", response_model=MyPageResponse)
async def update_my_info(data: MyPageUpdateRequest,db: AsyncSession = Depends(async_get_db)):
    
    result = await db.execute(select(User).where(User.id == 1))
    current_user = result.scalar_one_or_none()
    
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    await db.commit()
    await db.refresh(current_user)
    return current_user