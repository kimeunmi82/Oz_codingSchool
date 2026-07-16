from fastapi import APIRouter, HTTPException, status, Path, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator, StringConstraints
import re
from typing import Annotated
from app.schemas.mypage import (
    MyPageResponse, 
    MyPageUpdateRequest, 
    PasswordChangeRequest, 
    PasswordChangeResponse,
    )
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db.databases import async_get_db
from app.models.users import User
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.core.security import hash_password, verify_password

from app.apis.auth_apis import get_current_user_id


#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/mypage_api")

#####################################################
# 2. API Endpoints 구현
#####################################################




# 6. 마이페이지 조회
@router.get("/v1/users/me", response_model=MyPageResponse)
async def get_my_page(
    authenticated_user_id: int = Depends(
        get_current_user_id
    ),
    db: AsyncSession = Depends(async_get_db),
):
    statement = (
        select(User)
        .where(User.id == authenticated_user_id)
    )
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    return user

# 7. 회원 정보 수정
@router.patch("/v1/users/me", response_model=MyPageResponse)
async def update_my_info(data: MyPageUpdateRequest,    authenticated_user_id: int = Depends(
        get_current_user_id
    ),
    db: AsyncSession = Depends(async_get_db),
):

    statement = (
        select(User)
        .where(User.id == authenticated_user_id)
    )
    
    result = await db.execute(statement)
    current_user = result.scalar_one_or_none()
    
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    await db.commit()
    await db.refresh(current_user)
    return current_user

# 비밀번호 변경

@router.patch(
    "/v1/users/me/password/",
    response_model=PasswordChangeResponse,
    status_code=status.HTTP_200_OK,
    summary="사용자 비밀번호 변경 API",
)
async def change_my_password(
    body: PasswordChangeRequest,
    authenticated_user_id: int = Depends(
        get_current_user_id
    ),
    db: AsyncSession = Depends(async_get_db),
):

    statement = (
        select(User)
        .where(User.id == authenticated_user_id)
    )

    result = await db.execute(statement)
    current_user = result.scalar_one_or_none()

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "사용자 정보를 찾을 수 없습니다.",
            },
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "INACTIVE_ACCOUNT",
                "message": "비활성화된 계정입니다.",
            },
        )

    if current_user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PASSWORD_NOT_CONFIGURED",
                "message": "비밀번호가 설정되지 않은 계정입니다.",
            },
        )

    if not verify_password(
        body.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "현재 비밀번호가 일치하지 않습니다.",
            },
        )

    if verify_password(
        body.new_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SAME_AS_CURRENT_PASSWORD",
                "message": "새 비밀번호는 현재 비밀번호와 달라야 합니다.",
            },
        )

    current_user.hashed_password = hash_password(
        body.new_password
    )

    try:
        await db.commit()
        await db.refresh(current_user)
    except SQLAlchemyError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "비밀번호 변경 중 오류가 발생했습니다.",
            },
        ) from error

    return PasswordChangeResponse(
        message="비밀번호가 변경되었습니다.",
        updated_at=current_user.updated_at,
    )