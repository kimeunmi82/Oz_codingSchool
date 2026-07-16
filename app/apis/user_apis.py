from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.db.databases import async_get_db
from app.models.users import User, RoleEnum
from app.schemas.user import (
    UserListItem,
    UserCreateRequest,
    UserCreateResponse
)


#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/user_api")

#####################################################
# 2. API Endpoints 구현
#####################################################
# 회원 가입

password_hash = PasswordHash.recommended()


@router.post(
    "/v1/users",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 회원가입 API",
)
async def create_user(
    body: UserCreateRequest,
    db: AsyncSession = Depends(async_get_db),
):
    duplicate_stmt = select(User).where(
        or_(
            User.email == body.email,
            User.phone_number == body.phone_number,
        )
    )

    duplicate_result = await db.execute(duplicate_stmt)
    duplicate_user = duplicate_result.scalar_one_or_none()

    if duplicate_user:
        if duplicate_user.email == body.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 가입된 이메일입니다.",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 휴대폰 번호입니다.",
        )

    new_user = User(
        email=body.email,
        hashed_password=password_hash.hash(body.password),
        name=body.name,
        department=body.department,
        gender=body.gender,
        phone_number=body.phone_number,
        role=RoleEnum.PENDING,
        is_active=True,
    )

    db.add(new_user)

    try:
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 가입된 이메일 또는 휴대폰 번호입니다.",
        )

    return new_user




# 회원 목록 조회
@router.get("/v1/users", response_model=list[UserListItem])
async def get_user_list(db: AsyncSession = Depends(async_get_db)):
    stmt = select(User).order_by(User.id.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users