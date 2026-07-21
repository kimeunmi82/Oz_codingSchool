from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permissions
from app.core.db.databases import async_get_db
from app.core.timeout import TimeoutRoute
from app.models.ai_analysis_results import AIAnalysisResult
from app.models.medical_records import MedicalRecord
from app.models.users import DepartmentEnum, RoleEnum, User
from app.schemas.analysis import AIAnalysisListItem

#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(
    prefix="/analysis_api",
    tags=["analysis"],
    route_class=TimeoutRoute,
)

#####################################################
# 2. API Endpoints 구현
#####################################################

# AI 모델 활용 폐렴 예측 결과 조회
@router.get(
    "/v1/analysis/{record_id}",
    response_model=list[AIAnalysisListItem],
    status_code=status.HTTP_200_OK,
    summary="진료기록별 AI 폐렴 예측 결과 목록 조회 API",
)
async def get_analysis_list(
    record_id: Annotated[int, Path(ge=1)],
    db: AsyncSession = Depends(async_get_db),
    _current_user: User = Depends(
        require_permissions(
            allowed_departments=(
                DepartmentEnum.MEDICAL,
                DepartmentEnum.DEV,
                DepartmentEnum.RESEARCH,
            )
        )
    ),
) -> list[AIAnalysisListItem]:
    record_result = await db.execute(
        select(MedicalRecord.id).where(MedicalRecord.id == record_id)
    )
    if record_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    statement = (
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(
            AIAnalysisResult.created_at.desc(),
            AIAnalysisResult.id.desc(),
        )
    )
    result = await db.execute(statement)
    return list(result.scalars().all())
