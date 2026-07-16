from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.models.users import User
from app.schemas.user import UserListItem, UserRoleUpdateRequest


#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/user_api")

#####################################################
# 2. API Endpoints 구현
#####################################################

# 회원 목록 조회
@router.get("/v1/users", response_model=list[UserListItem])
async def get_user_list(db: AsyncSession = Depends(async_get_db)):
    stmt = select(User).order_by(User.id.desc())
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
    # 대상 사용자 조회
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")
    
    # 권한 업데이트
    user.role = data.role
    await db.commit()
    
    return {"message": "사용자 권한이 성공적으로 변경되었습니다."}