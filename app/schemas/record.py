from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# X-ray 이미지 정보를 위한 기본 스키마 (필요 시 필드 추가)
class XrayImageItem(BaseModel):
    id: int
    image_url: str  # 이미지 경로 또는 URL

    model_config = ConfigDict(from_attributes=True)

# 목록 조회용 스키마
class MedicalRecordListItem(BaseModel):
    id: int
    chart_number: str
    # 증상 요약 (필요시 100자 제한)
    symptoms: str = Field(..., max_length=100) 
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 상세 조회용 스키마
class MedicalRecordDetail(BaseModel):
    id: int
    chart_number: str
    symptoms: str
    created_at: datetime
    xray_images: list[XrayImageItem] = [] # 상세 조회 시 이미지 리스트 포함

    model_config = ConfigDict(from_attributes=True)





