from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import load_only, selectinload
from app.core.timeout import TimeoutRoute
from app.core.db.databases import async_get_db

from app.apis.auth_apis import get_current_access_token_payload
from app.core.authorization import require_permissions
from app.models.users import DepartmentEnum

#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(
    prefix="/prediction_api", 
    tags=["prediction"],
    route_class=TimeoutRoute,
)

#####################################################
# 2. API Endpoints 구현
#####################################################