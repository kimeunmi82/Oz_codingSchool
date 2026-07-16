from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.models.users import User
from app.schemas.user import UserListItem


#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/user_api")

#####################################################
# 2. API Endpoints 구현
#####################################################

# 회원 목록 조회
@router.get("/users", response_model=list[UserListItem])
async def get_user_list(db: AsyncSession = Depends(async_get_db)):
    stmt = select(User).order_by(User.id.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users