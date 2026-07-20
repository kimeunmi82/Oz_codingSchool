from datetime import datetime

from pydantic import BaseModel, Field


class MedicalRecordData(BaseModel):
    id: int = Field(..., description="진료기록 고유 ID")
    patient_id: int = Field(..., description="환자 고유 ID")
    chart_number: str = Field(..., description="환자 진료 차트 번호")
    symptoms: str = Field(..., description="환자 증상 기록")
    created_at: datetime = Field(..., description="진료 정보 등록 일시")
    updated_at: datetime | None = Field(None, description="진료 정보 수정 일시")


class XrayImageData(BaseModel):
    id: int = Field(..., description="X-ray 이미지 고유 ID")
    record_id: int = Field(..., description="진료 기록 ID")
    uploader_id: int = Field(..., description="X-ray 이미지를 업로드한 유저 ID")
    image_url: str = Field(..., description="저장된 X-ray 이미지 URL")
    preview_url: str = Field(..., description="업로드된 X-ray 이미지 미리보기 URL")
    shooting_datetime: datetime = Field(..., description="X-ray 촬영 일시")
    created_at: datetime = Field(..., description="X-ray 이미지 등록 일시")


class MedicalRecordCreateMessage(BaseModel):
    detail: str = Field(..., description="진료기록 등록 결과 메시지")
    medical_record: MedicalRecordData
    xray_image: XrayImageData


class MedicalRecordDetailItem(BaseModel):
    medical_record: MedicalRecordData
    xray_images: list[XrayImageData]


class MedicalRecordDetailResponse(BaseModel):
    patient_id: int = Field(..., description="환자 고유 ID")
    records: list[MedicalRecordDetailItem]
