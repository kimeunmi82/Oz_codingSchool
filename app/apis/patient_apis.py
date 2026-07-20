from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from sqlalchemy.orm import load_only


from app.core.timeout import TimeoutRoute
from app.core.security import hash_password_async
from app.core.authorization import require_permissions
from app.core.db.databases import async_get_db

from app.models.patients import GenderEnum, Patient
from app.models.users import DepartmentEnum, RoleEnum
from app.schemas.patient import (
    PatientCreate,
    PatientGender,
    PatientResponse,
)
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

# 환자 등록 API
@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="환자 정보 등록 API",
    description="의료 실무진이 환자 정보를 등록합니다.",
)
async def create_patient(
    body: PatientCreate,
    current_user=Depends(
        require_permissions(
            allowed_departments=(
                DepartmentEnum.MEDICAL,
            ),
            allowed_roles=(
                RoleEnum.STAFF,
            ),
        )
    ),
    db: AsyncSession = Depends(async_get_db),
) -> PatientResponse:
    patient = Patient(
        name=body.name,
        age=body.age,
        gender=(
            GenderEnum.M
            if body.gender == PatientGender.MALE
            else GenderEnum.F
        ),
        phone=body.phone_number,
    )

    db.add(patient)

    try:
        await db.commit()
        await db.refresh(patient)
    except SQLAlchemyError as error:
        await db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "환자 정보 등록 중 오류가 발생했습니다."
            ),
        ) from error

    return PatientResponse(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        gender=(
            PatientGender.MALE
            if patient.gender == GenderEnum.M
            else PatientGender.FEMALE
        ),
        phone_number=patient.phone,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


# 환자 목록 조회 API
@router.get(
    "",
    response_model=list[PatientResponse],
    status_code=status.HTTP_200_OK,
    summary="환자 목록 조회 API",
    description=(
        "환자 이름 검색과 성별 및 나이 범위 "
        "필터링을 지원합니다."
    ),
)
async def get_patient_list(
    name: str | None = Query(
        default=None,
        min_length=1,
        max_length=30,
        description="환자 이름 검색어",
    ),
    gender: PatientGender | None = Query(
        default=None,
        description="성별 필터: male 또는 female",
    ),
    min_age: int | None = Query(
        default=None,
        ge=0,
        le=150,
        description="최소 나이",
    ),
    max_age: int | None = Query(
        default=None,
        ge=0,
        le=150,
        description="최대 나이",
    ),
    current_user=Depends(
        require_permissions(
            allowed_roles=(
                RoleEnum.STAFF,
            ),
        )
    ),
    db: AsyncSession = Depends(async_get_db),
) -> list[PatientResponse]:
    if (
        min_age is not None
        and max_age is not None
        and min_age > max_age
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=[
                {
                    "loc": ["query", "min_age"],
                    "msg": (
                        "min_age는 max_age보다 "
                        "클 수 없습니다."
                    ),
                    "type": "value_error",
                }
            ],
        )

    statement = select(Patient)

    if name:
        search_name = name.strip()
        statement = statement.where(
            Patient.name.contains(search_name)
        )

    if gender:
        db_gender = (
            GenderEnum.M
            if gender == PatientGender.MALE
            else GenderEnum.F
        )
        statement = statement.where(
            Patient.gender == db_gender
        )

    if min_age is not None:
        statement = statement.where(
            Patient.age >= min_age
        )

    if max_age is not None:
        statement = statement.where(
            Patient.age <= max_age
        )

    statement = statement.order_by(
        Patient.id.desc()
    )

    try:
        result = await db.execute(statement)
        patients = result.scalars().all()
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "환자 목록 조회 중 오류가 발생했습니다."
            ),
        ) from error

    return [
        PatientResponse(
            id=patient.id,
            name=patient.name,
            age=patient.age,
            gender=(
                PatientGender.MALE
                if patient.gender == GenderEnum.M
                else PatientGender.FEMALE
            ),
            phone_number=patient.phone,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )
        for patient in patients
    ]