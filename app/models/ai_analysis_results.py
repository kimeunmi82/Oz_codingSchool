from sqlalchemy import Column, BigInteger, Boolean, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.core.db.databases import Base

class AIAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"
    
    __table_args__ = {'comment': 'AI 분석 결과 저장 테이블'}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='기본 키')
    
    # 각 필드별로 note 내용을 comment로 넣어줍니다.
    record_id = Column(BigInteger, ForeignKey("medical_records.id"), nullable=False, comment='진료 기록 ID')
    is_pneumonia = Column(Boolean, nullable=False, comment='폐렴 진단 여부')
    confidence = Column(Numeric(5, 2), nullable=False, comment='AI 예측 확률')
    heatmap_url = Column(String(255), nullable=False, comment='AI 분석 결과 이미지 경로')
    ai_model = Column(String(50), nullable=False, comment='AI 예측 모델명')
    
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment='생성 일시')
    updated_at = Column(DateTime, onupdate=func.now(), comment='수정 일시')
