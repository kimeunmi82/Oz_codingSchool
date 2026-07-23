import asyncio
import hashlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_results import AIAnalysisResult
from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImages
from worker.predictors.registry import get_predictor


MEDIA_ROOT = Path(__file__).resolve().parents[2] / "media"
HEATMAP_DIR = MEDIA_ROOT / "uploads" / "heatmaps"


class MedicalRecordNotFoundError(Exception):
    """진료기록을 찾을 수 없는 경우."""


class XrayImageNotFoundError(Exception):
    """진료기록에 예측 가능한 X-ray가 없는 경우."""


class PredictionFailedError(Exception):
    """AI 모델 추론에 실패한 경우."""


async def _find_medical_record(
    db: AsyncSession,
    record_id: int,
) -> MedicalRecord | None:
    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id,
        )
    )
    return result.scalar_one_or_none()


async def _find_existing_prediction(
    db: AsyncSession,
    record_id: int,
    ai_model: str,
) -> AIAnalysisResult | None:
    """동일 진료기록과 동일 모델의 기존 결과를 조회한다."""

    result = await db.execute(
        select(AIAnalysisResult).where(
            AIAnalysisResult.record_id == record_id,
            AIAnalysisResult.ai_model == ai_model,
        )
    )
    return result.scalar_one_or_none()


async def _find_latest_xray(
    db: AsyncSession,
    record_id: int,
) -> XrayImages | None:
    """진료기록에 등록된 가장 최신 X-ray를 조회한다."""

    result = await db.execute(
        select(XrayImages)
        .where(XrayImages.record_id == record_id)
        .order_by(
            XrayImages.shooting_datetime.desc(),
            XrayImages.id.desc(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


def _resolve_xray_path(image_url: str) -> Path:
    """DB의 /media URL을 안전한 로컬 파일 경로로 변환한다."""

    media_prefix = "/media/"

    if not image_url.startswith(media_prefix):
        raise XrayImageNotFoundError

    relative_path = image_url.removeprefix(media_prefix)
    media_root = MEDIA_ROOT.resolve()
    image_path = (media_root / relative_path).resolve()

    # ../ 등을 이용해 media 디렉터리 밖으로 접근하는 것을 방지한다.
    if not image_path.is_relative_to(media_root):
        raise XrayImageNotFoundError

    if not image_path.is_file():
        raise XrayImageNotFoundError

    return image_path


def _has_available_heatmap(analysis: AIAnalysisResult) -> bool:
    """DB의 히트맵 URL이 실제 media 파일을 가리키는지 확인한다."""

    if not analysis.heatmap_url or not analysis.heatmap_model:
        return False

    try:
        _resolve_xray_path(analysis.heatmap_url)
    except XrayImageNotFoundError:
        return False

    return True


def _heatmap_destination(
    record_id: int,
    model_key: str,
    ai_model: str,
) -> tuple[Path, str]:
    """모델별 디렉터리에 재사용 가능한 히트맵 경로를 만든다."""

    model_hash = hashlib.sha256(
        ai_model.encode("utf-8")
    ).hexdigest()[:12]
    file_name = f"record_{record_id}_{model_hash}.jpg"
    return (
        HEATMAP_DIR / model_key / file_name,
        f"/media/uploads/heatmaps/{model_key}/{file_name}",
    )


async def get_or_create_prediction(
    db: AsyncSession,
    record_id: int,
    model_key: str,
) -> tuple[AIAnalysisResult, bool]:
    """
    기존 예측 결과가 있으면 반환하고,
    없으면 모델 추론 후 DB에 저장한다.

    반환값:
        (AIAnalysisResult, cached)
    """

    medical_record = await _find_medical_record(db, record_id)

    if medical_record is None:
        raise MedicalRecordNotFoundError

    predictor = get_predictor(model_key)

    # 모델을 실행하기 전에 기존 저장 결과를 먼저 확인한다.
    existing_prediction = await _find_existing_prediction(
        db,
        record_id,
        predictor.ai_model,
    )

    if (
        existing_prediction is not None
        and _has_available_heatmap(existing_prediction)
    ):
        return existing_prediction, True

    xray = await _find_latest_xray(db, record_id)

    if xray is None:
        raise XrayImageNotFoundError

    image_path = _resolve_xray_path(xray.image_url)

    # 긴 모델 추론 동안 DB 연결을 점유하지 않도록 읽기 트랜잭션을 종료한다.
    await db.rollback()

    heatmap_path, heatmap_url = _heatmap_destination(
        record_id,
        predictor.model_key,
        predictor.ai_model,
    )

    try:
        # 예측과 weighted ensemble Grad-CAM은 동기 CPU/GPU 작업이므로
        # FastAPI 이벤트 루프를 막지 않게 별도 worker thread에서 실행한다.
        prediction_result = await asyncio.to_thread(
            predictor.predict,
            image_path,
            heatmap_path,
        )
    except Exception as exc:
        raise PredictionFailedError from exc

    # 기존 예측 결과에 히트맵만 없었던 경우에는 진단 결과를 새로 만들지 않고
    # 동일한 행을 보완한다. 기존 데이터의 생성 시각과 예측값도 유지한다.
    if existing_prediction is not None:
        existing_prediction.heatmap_url = heatmap_url
        existing_prediction.heatmap_model = prediction_result.heatmap_model

        try:
            await db.commit()
            await db.refresh(existing_prediction)
            return existing_prediction, False
        except Exception:
            await db.rollback()
            raise

    analysis = AIAnalysisResult(
        record_id=record_id,
        is_pneumonia=prediction_result.is_pneumonia,
        confidence=prediction_result.confidence,
        heatmap_url=heatmap_url,
        heatmap_model=prediction_result.heatmap_model,
        ai_model=prediction_result.ai_model,
    )

    db.add(analysis)

    try:
        await db.commit()
        await db.refresh(analysis)
        return analysis, False

    except IntegrityError:
        # 동시에 같은 요청이 들어오면 Unique Constraint 충돌이 발생할 수 있다.
        # 먼저 저장된 결과를 다시 조회해 반환한다.
        await db.rollback()

        existing_prediction = await _find_existing_prediction(
            db,
            record_id,
            predictor.ai_model,
        )

        if existing_prediction is not None:
            return existing_prediction, True

        raise

    except Exception:
        await db.rollback()
        raise


async def get_prediction_results(
    db: AsyncSession,
    record_id: int,
) -> list[AIAnalysisResult]:
    """진료기록의 저장된 예측 결과를 최신순으로 조회한다."""

    medical_record = await _find_medical_record(db, record_id)

    if medical_record is None:
        raise MedicalRecordNotFoundError

    result = await db.execute(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(
            AIAnalysisResult.created_at.desc(),
            AIAnalysisResult.id.desc(),
        )
    )

    return list(result.scalars().all())
