from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIAnalysisListItem(BaseModel):
    id: int = Field(description="AI 분석 결과 고유 ID")
    is_pneumonia: bool = Field(description="폐렴 예측 여부")
    confidence: float = Field(ge=0, le=100, description="예측 신뢰도(%)")
    heatmap_url: str = Field(description="Heatmap 이미지 URL")
    created_at: datetime = Field(description="예측 수행 일시")
    ai_model: str = Field(description="예측에 사용한 모델")

    model_config = ConfigDict(from_attributes=True)
