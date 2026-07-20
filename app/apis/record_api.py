from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.security import hash_password_async
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from app.core.authorization import require_permissions
from app.models.users import DepartmentEnum
from app.core.db.databases import async_get_db
from app.schemas.record import MedicalRecordListItem, MedicalRecordDetail
from app.models.medical_records import MedicalRecord

from sqlalchemy.orm import load_only, selectinload
from app.core.timeout import TimeoutRoute

#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(
    prefix="/record_api", 
    tags=["record"],
    route_class=TimeoutRoute,
)

#####################################################
# 2. API Endpoints 구현
#####################################################

# 1. 목록 조회 API [REQ-MDR-002]
@router.get("/v1/records", response_model=list[MedicalRecordListItem])
async def get_medical_records(
    patient_id: int, 
    db: AsyncSession = Depends(async_get_db),
    # 의료 부서만 접근 가능하도록 설정
    current_user = Depends(require_permissions(allowed_departments=(DepartmentEnum.MEDICAL,)))
):
    # ... 기존 로직 그대로 유지 ...
    stmt = select(MedicalRecord).where(MedicalRecord.patient_id == patient_id).order_by(MedicalRecord.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

# 2. 상세 조회 API [REQ-MDR-003]
@router.get("/v1/records/{record_id}", response_model=MedicalRecordDetail)
async def get_medical_record_detail(
    record_id: int, 
    db: AsyncSession = Depends(async_get_db),
    # 의료 부서만 접근 가능하도록 설정
    current_user = Depends(require_permissions(allowed_departments=(DepartmentEnum.MEDICAL,)))
):
    # ... 기존 로직 그대로 유지 ...
    stmt = select(MedicalRecord).options(selectinload(MedicalRecord.xray_images)).where(MedicalRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="진료기록을 찾을 수 없습니다.")
    
    return record