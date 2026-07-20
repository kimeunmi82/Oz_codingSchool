from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.security import hash_password_async
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from app.core.db.databases import async_get_db


from sqlalchemy.orm import load_only
from app.core.timeout import TimeoutRoute

#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(
    prefix="/patient_api", 
    tags=["patient"],
    route_class=TimeoutRoute,
)

#####################################################
# 2. API Endpoints 구현
#####################################################