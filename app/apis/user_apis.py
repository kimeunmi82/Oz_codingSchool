

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.security import hash_password_async

from sqlalchemy import or_, select

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from app.core.db.databases import async_get_db
from app.models.users import User, RoleEnum, DepartmentEnum
from app.schemas.user import (
    UserListItem,
    UserCreateRequest,
    UserCreateResponse,
    UserRoleUpdateRequest
)

from sqlalchemy.orm import load_only

#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/user_api", tags=["user"])

#####################################################
# 2. API Endpoints 구현
#####################################################
# 회원 가입
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
        hashed_password=await hash_password_async(body.password),
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

@router.get(
        "/v1/users",
        response_model=list[UserListItem],
        status_code=status.HTTP_200_OK,
        summary='사용자 목록 조회 API',
        description=(
            '관리자가 모든 사용자를 목록으로 조회합니다.'
            '이메일 또는 이름 검색과 부서별 필터를 지원합니다.'
        )
)
async def get_user_list(
    query: str | None = Query(
        default=None,
        description='사용자 이메일 또는 이름 검색어',
    ),
    department: DepartmentEnum | None = Query (
        default=None,
        description='부서 필터: RESEARCH, MEDICAL, DEV',
    ),
    page: int = Query(
    default=1,
    ge=1,
    description="페이지 번호",
),
    page_size: int = Query(
    default=20,
    ge=1,
    le=100,
    description="페이지당 사용자 수",
),
    db: AsyncSession = Depends(async_get_db),
):
    stmt = select(User).options(
        load_only(
            User.id,
            User.email,
            User.name,
            User.phone_number,
            User.gender,
            User.department,
            User.is_active,
            raiseload=True,
        )
    )

    # 이메일 또는 이름 검색
    if query:
        search_keyword = f"%{query}%"

        stmt = stmt.where(
            or_(
                User.email.ilike(search_keyword),
                User.name.ilike(search_keyword),
            )
        )

    # 부서 필터
    if department:
        stmt = stmt.where(User.department == department)

    offset = (page - 1) * page_size

    stmt = (
        stmt
        .order_by(User.id.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    users = result.scalars().all()

    return users

# 5. 회원 권한 변경
@router.patch("/v1/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    data: UserRoleUpdateRequest,
    db: AsyncSession = Depends(async_get_db)
):
    stmt = (
        select(User)
        .options(
            load_only(
                User.id,
                User.role,
                raiseload=True,
            )
        )
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자를 찾을 수 없습니다.",
        )

    user.role = data.role

    try:
        await db.commit()
    except SQLAlchemyError as error:
        await db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="사용자 권한 변경 중 오류가 발생했습니다.",
        ) from error

    return {
        "message": "사용자 권한이 성공적으로 변경되었습니다."
    }