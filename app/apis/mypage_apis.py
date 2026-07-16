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