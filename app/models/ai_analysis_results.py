from sqlalchemy import BigInteger, ForeignKey, String, Boolean, Numeric

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base

from app.core.db.models import TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.medical_records import MedicalRecord 

class AIAnalysisResult(Base, TimestampMixin):
    __tablename__ = "ai_analysis_results"
    __table_args__ = {'comment': 'AI 분석 결과 저장 테이블'}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='기본 키')
    
    record_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("medical_records.id"), 
        nullable=False, comment='진료 기록 ID'
    )
    
    is_pneumonia: Mapped[bool] = mapped_column(Boolean, nullable=False, comment='폐렴 진단 여부')
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, comment='AI 예측 확률')
    heatmap_url: Mapped[str] = mapped_column(String(255), nullable=False, comment='AI 분석 결과 이미지 경로')
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False, comment='AI 예측 모델명')

    # 관계 설정
    medical_record: Mapped["MedicalRecord"] = relationship(
        back_populates="ai_analysis_results"
    )