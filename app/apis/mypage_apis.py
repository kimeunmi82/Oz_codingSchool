from fastapi import (
    APIRouter,
    HTTPException,
    status, 
    Path, 
    Depends,
    Response
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)
from pydantic import BaseModel, EmailStr, Field, field_validator, StringConstraints

import re
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.schemas.mypage import MyPageResponse, MyPageUpdateRequest
from app.core.db.databases import async_get_db
from app.models.users import User
from app.apis.auth_apis import decode_jwt



#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/mypage_api")

#####################################################
# 2. API Endpoints 구현
#####################################################

# 회원탈퇴 API 
 
# 임시 인증함수 추가

security = HTTPBearer()


# TODO:
# 인증 담당자가 공통 get_current_user 함수를 완성하면
# 이 함수를 삭제하고 공통 함수를 import해서 사용한다.

async def get_current_user_for_delete(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(async_get_db),
) -> User:
    access_token = credentials.credentials.strip()

    payload = decode_jwt(
        access_token,
        invalid_detail="invalid_token",
        expired_detail="expired_token",
    )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    user_id = payload.get("user_id")

    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user

# 회원 탈퇴 API
@router.delete(
    "/v1/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원 탈퇴 API",
    description="로그인한 사용자의 계정을 비활성화합니다.",
)
async def delete_my_account(
    response: Response,
    current_user: User = Depends(get_current_user_for_delete),
    db: AsyncSession = Depends(async_get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 탈퇴한 사용자입니다.",
        )

    current_user.is_active = False

    await db.commit()

    response.delete_cookie(
        key="refresh_token",
        path="/",
    )
    response.status_code = status.HTTP_204_NO_CONTENT

    return response



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