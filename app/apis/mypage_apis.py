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


from app.schemas.mypage import (
    MyPageResponse,
    MyPageUpdateRequest,
    PasswordChangeRequest,
    PasswordChangeResponse
)

from app.core.db.databases import async_get_db
from app.models.users import User
from app.apis.auth_apis import decode_jwt

from sqlalchemy.exc import SQLAlchemyError
from app.core.security import (hash_password_async, verify_password_async,)

from app.apis.auth_apis import get_current_user_id
from app.core.timeout import TimeoutRoute

from app.core.authorization import require_permissions
from app.models.users import RoleEnum

#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(
    prefix="/mypage_api", 
    tags=["mypage"],
    route_class=TimeoutRoute,
)

#####################################################
# 2. API Endpoints 구현
#####################################################

# 회원 탈퇴 API
@router.delete(
    "/v1/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원 탈퇴 API",
    description="로그인한 사용자의 계정을 비활성화합니다.",
)
async def delete_my_account(
    response: Response,
    authenticated_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(async_get_db),
):
    statement = select(User).where(
        User.id == authenticated_user_id
    )
    result = await db.execute(statement)
    current_user = result.scalar_one_or_none()

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 정보를 찾을 수 없습니다.",
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 탈퇴한 사용자입니다.",
        )

    current_user.is_active = False

    try:
        await db.commit()
    except SQLAlchemyError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원 탈퇴 중 오류가 발생했습니다.",
        ) from error

    response.delete_cookie(
        key="refresh_token",
        path="/",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response



# 6. 마이페이지 조회
@router.get("/v1/users/me", response_model=MyPageResponse,)
async def get_my_page(
    authenticated_user_id: int = Depends(
        get_current_user_id
    ),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(
        require_permissions(
            allowed_roles=(
                RoleEnum.STAFF,),
        )
    ),
):
    statement = (
        select(User)
        .where(User.id == authenticated_user_id)
    )
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    return user

# 7. 회원 정보 수정
@router.patch("/v1/users/me", response_model=MyPageResponse,)
async def update_my_info(data: MyPageUpdateRequest, authenticated_user_id: int = Depends(
        get_current_user_id
    ),
    db: AsyncSession = Depends(async_get_db),
):

    statement = select(User).where(User.id == authenticated_user_id)
    
    result = await db.execute(statement)
    current_user = result.scalar_one_or_none()
        
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 정보를 찾을 수 없습니다.",
        )   
    
    for key, value in data.model_dump(
        exclude_unset=True
    ).items():
        setattr(current_user, key, value)
    
    try:
        await db.commit()
    except SQLAlchemyError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원 정보 수정 중 오류가 발생했습니다.",
        ) from error

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

    is_current_password_valid = (
        await verify_password_async(
            body.current_password,
            current_user.hashed_password,
        )
    )  

    if not is_current_password_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_CURRENT_PASSWORD",
                "message": "현재 비밀번호가 일치하지 않습니다.",
            },
        )

    new_hashed_password = await hash_password_async(
    body.new_password
    )
    
    current_user.hashed_password = new_hashed_password

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