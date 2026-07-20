import secrets
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeout import TimeoutRoute
from app.core.db.databases import async_get_db

from app.apis.auth_apis import get_current_access_token_payload
from app.schemas.record import (
    MedicalRecordCreateMessage,
    MedicalRecordData,
    XrayImageData,
)
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImages
from app.core.authorization import require_permissions
from app.models.users import DepartmentEnum

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

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "media" / "uploads" / "xray"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validate_image(content_type: str | None) -> None:
    allowed_types = {"image/png", "image/jpeg", "image/jpg"}
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_xray_image_type",
        )

def _delete_existing_xray_files(patient_id: int) -> None:
    for existing_file in UPLOAD_DIR.glob(f"{patient_id}.*"):
        if existing_file.is_file():
            existing_file.unlink()
            
# 진료기록 등록
@router.post(
    "/v1/record/{patient_id}",
    response_model=MedicalRecordCreateMessage,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record(
    patient_id: int,
    chart_number: Annotated[str, Form(...)],
    symptoms: Annotated[str, Form(...)],
    shooting_datetime: Annotated[datetime, Form(...)],
    xray_image: Annotated[UploadFile, File(...)],
    token_payload: dict = Depends(get_current_access_token_payload),
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(
        require_permissions(
            allowed_departments=(DepartmentEnum.MEDICAL,),
        )
    ),
) -> MedicalRecordCreateMessage:
    chart_number = chart_number.strip()
    symptoms = symptoms.strip()

    if patient_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_patient_id",
        )

    if not chart_number or not symptoms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="empty_fields",
        )

    existing_record_stmt = select(MedicalRecord).where(
        MedicalRecord.chart_number == chart_number
    )
    existing_record_result = await db.execute(existing_record_stmt)
    existing_record = existing_record_result.scalar_one_or_none()
            
    # 로그인한 사용자 ID
    uploader_id = token_payload.get("user_id")
    if not isinstance(uploader_id, int) or uploader_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    _validate_image(xray_image.content_type)

    suffix = Path(xray_image.filename or "").suffix.lower() or ".png"
    file_name = f"{patient_id}{suffix}"
    file_path = UPLOAD_DIR / file_name
    file_bytes = await xray_image.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="empty_xray_image",
        )

    # 기존 등록 이미지 삭제 후 최신 파일만 유지
    _delete_existing_xray_files(patient_id)
    file_path.write_bytes(file_bytes)

    image_url = f"/media/uploads/xray/{file_name}"

    try:
        if existing_record is None:
            record_model = MedicalRecord(
                patient_id=patient_id,
                chart_number=chart_number,
                symptoms=symptoms,
            )
            db.add(record_model)
            await db.flush()
        else:
            record_model = existing_record
            record_model.patient_id = patient_id
            record_model.symptoms = symptoms
            record_model.updated_at = datetime.now()
            await db.flush()

        existing_xray_stmt = select(XrayImages).where(
            XrayImages.record_id == record_model.id
        )
        
        existing_xray_result = await db.execute(existing_xray_stmt)
        existing_xray = existing_xray_result.scalar_one_or_none()

        if existing_xray is None:
            xray_model = XrayImages(
                record_id=record_model.id,
                uploader_id=uploader_id,
                image_url=image_url,
                shooting_datetime=shooting_datetime,
            )
            db.add(xray_model)
            await db.flush()
        else:
            xray_model = existing_xray
            xray_model.uploader_id = uploader_id
            xray_model.image_url = image_url
            xray_model.shooting_datetime = shooting_datetime
            xray_model.updated_at = datetime.now()
            await db.flush()

        await db.commit()
        await db.refresh(record_model)
        await db.refresh(xray_model)

    except Exception:
        await db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise

    record = MedicalRecordData(
        id=record_model.id,
        patient_id=record_model.patient_id,
        chart_number=record_model.chart_number,
        symptoms=record_model.symptoms,
        created_at=record_model.created_at,
        updated_at=record_model.updated_at,
    )

    xray_image_data = XrayImageData(
        id=xray_model.id,
        record_id=xray_model.record_id,
        uploader_id=xray_model.uploader_id,
        image_url=xray_model.image_url,
        preview_url=f"/record_api/v1/record/images/{file_name}",
        shooting_datetime=xray_model.shooting_datetime,
        created_at=xray_model.created_at,
    )

    return MedicalRecordCreateMessage(
        detail="진료기록이 등록되었습니다.",
        medical_record=record,
        xray_image=xray_image_data,
    )

# 이미지 미리보기
@router.get("/v1/record/images/{file_name}")
async def get_uploaded_xray_preview(
    file_name: str,
    current_user=Depends(
        require_permissions(
            allowed_departments=(DepartmentEnum.MEDICAL,),
        )
    ),
) -> FileResponse:
    file_path = UPLOAD_DIR / file_name
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="xray_image_not_found",
        )
    return FileResponse(file_path)
