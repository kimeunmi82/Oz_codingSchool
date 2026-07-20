# 5일차 환자관리 API 설계서

## 1. 문서 개요

본 문서는 환자 상세 페이지에서 사용하는 환자 정보 수정 및 삭제 API의 계약을 정의한다.

| 항목 | 내용 |
| --- | --- |
| 대상 요구사항 | `REQ-PTNT-004`, `REQ-PTNT-005` |
| API 버전 | v1 |
| Base URL | `/api/v1` |
| 인증 방식 | JWT Bearer Token |
| 요청/응답 형식 | `application/json` |
| 오류 형식 | FastAPI `HTTPException`의 `detail` 응답 |
| 목표 처리 시간 | 3초 이내 |

## 2. 프로젝트 코드 분석 결과

### 2.1 요구사항과 프론트엔드

`static/apis.js`에는 다음과 같이 요구사항 ID와 호출 경로가 정의되어 있다.

| 요구사항 ID | 기능 | 프론트엔드 호출 |
| --- | --- | --- |
| `REQ-PTNT-004` | 환자 정보 수정 | `PATCH /api/v1/patients/{patient_id}` |
| `REQ-PTNT-005` | 환자 정보 삭제 | `DELETE /api/v1/patients/{patient_id}` |

`static/pages.js`와 `static/templates/patient-detail.html`을 기준으로 수정 화면에서 입력하는 값은 환자 이름과 전화번호이다. 수정 요청은 다음 형태로 전송된다.

```json
{
  "name": "홍길동",
  "phone_number": "01012345678"
}
```

삭제 확인 모달에는 환자 삭제 시 모든 진료기록과 AI 분석 데이터가 영구 삭제된다고 안내되어 있다.

### 2.2 Patient 모델

`app/models/patients.py`의 실제 컬럼은 다음과 같다.

| 모델 속성 | DB 타입 | Nullable | 설명 |
| --- | --- | --- | --- |
| `id` | BigInteger, PK | N | 환자 고유 ID |
| `name` | String(30) | N | 환자 이름 |
| `age` | SmallInteger | N | 나이 |
| `gender` | Enum(`M`, `F`) | Y | 성별 |
| `phone` | String(11) | N | 국내 전화번호 |
| `created_at` | DateTime | N | 등록 일시 |
| `updated_at` | DateTime | Y | 수정 일시 |

Patient 모델은 `SoftDeleteMixin`을 사용하지 않으므로 `REQ-PTNT-005`는 소프트 삭제가 아닌 실제 행 삭제로 설계한다.

### 2.3 연관 데이터

```text
Patient
└── MedicalRecord
    ├── XrayImages
    └── AIAnalysisResult
```

- `Patient.medical_records`에 `cascade="all, delete-orphan"`이 설정되어 있다.
- `MedicalRecord.xray_images`에 `cascade="all, delete-orphan"`이 설정되어 있다.
- `MedicalRecord.ai_analysis_results`에 `cascade="all, delete-orphan"`이 설정되어 있다.
- `medical_records.patient_id` 외래키에는 `ON DELETE CASCADE`가 설정되어 있다.
- `xray_images.record_id`와 `ai_analysis_results.record_id` 외래키에는 DB 레벨의 `ON DELETE CASCADE`가 설정되어 있지 않다.
- X-Ray 파일 경로는 `xray_images.image_url`, AI Heatmap 파일 경로는 `ai_analysis_results.heatmap_url`에 저장된다.
- `app/main.py`는 프로젝트의 `media` 디렉터리를 `/media` 경로로 제공한다.

따라서 환자 삭제 시 단순 bulk delete를 사용하지 않고 ORM 관계를 통해 삭제하거나, 하위 외래키에도 `ON DELETE CASCADE`를 추가해야 한다. DB 행과 별개로 로컬 이미지 파일도 애플리케이션에서 제거해야 한다.

### 2.4 현재 코드와 공개 API 계약의 차이

| 구분 | 현재 코드 | 본 명세의 공개 계약 |
| --- | --- | --- |
| API Base URL | 프론트엔드 `/api/v1` | `/api/v1` |
| Patient 라우터 | `/patient_api`, 엔드포인트 미구현 | `/api/v1/patients` |
| 전화번호 모델 필드 | `phone` | 요청/응답 `phone_number` |
| 성별 모델 값 | `M`, `F` | 응답 `male`, `female` |
| Patient 스키마 | 미작성 | 별도 요청/응답 스키마 필요 |
| 라우터 등록 | `main.py`에 미등록 | `app.include_router(patient_router)` 필요 |

프론트엔드 변경을 최소화하기 위해 외부 API 필드는 `phone_number`를 유지하고 내부에서 `Patient.phone`으로 매핑한다. 성별도 상세 화면이 기대하는 `male`, `female`로 변환해 반환한다.

## 3. 공통 정책

### 3.1 인증 헤더

```http
Authorization: Bearer <access_token>
```

### 3.2 권한

사용자 모델의 역할은 `PENDING`, `STAFF`, `ADMIN`이며 부서는 `DEV`, `MEDICAL`, `RESEARCH`이다.

두 API는 다음 사용자에게 허용한다.

- 활성 상태의 `STAFF`
- 활성 상태의 `ADMIN`

환자 상세 기능은 개발진, 의료 실무진, 연구진 모두 사용할 수 있으므로 `STAFF`의 부서는 제한하지 않는다. `ADMIN`은 기존 `require_permissions()` 정책에 따라 항상 허용한다. `PENDING` 또는 비활성 사용자는 허용하지 않는다.

구현 시 권한 의존성은 다음 정책과 동일해야 한다.

```python
require_permissions(
    allowed_roles=(RoleEnum.STAFF,),
)
```

### 3.3 오류 응답 형식

프로젝트의 기존 API와 동일하게 오류는 `detail` 필드로 반환한다.

```json
{
  "detail": "오류 메시지"
}
```

Pydantic 유효성 검사 오류는 FastAPI 기본 `422` 형식을 사용한다.

```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "name"],
      "msg": "String should have at most 30 characters",
      "input": "..."
    }
  ]
}
```

### 3.4 공통 상태 코드

| 상태 코드 | 의미 |
| --- | --- |
| `401 Unauthorized` | 토큰 누락, 만료, 변조 또는 활성 사용자를 찾을 수 없음 |
| `403 Forbidden` | 로그인했지만 역할이 `PENDING` 등으로 허용되지 않음 |
| `404 Not Found` | `patient_id`에 해당하는 환자가 없음 |
| `422 Unprocessable Entity` | 경로 또는 요청 본문의 유효성 검사 실패 |
| `500 Internal Server Error` | DB 또는 파일 시스템 처리 실패 |
| `504 Gateway Timeout` | `TimeoutRoute`의 3초 제한 초과 |

---

## 4. REQ-PTNT-004 환자 정보 수정

### 4.1 API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 수정 |
| 요구사항 ID | `REQ-PTNT-004` |
| Method | `PATCH` |
| Endpoint | `/api/v1/patients/{patient_id}` |
| 인증 | 필수 |
| 권한 | `STAFF`, `ADMIN` |
| Content-Type | `application/json` |
| 성공 상태 | `200 OK` |

환자 상세 페이지의 정보 수정 모달에서 환자 이름과 전화번호를 수정한다. 나이와 성별은 현재 수정 화면에 없으므로 이 API의 수정 대상에 포함하지 않는다.

### 4.2 요청

#### Path Parameter

| 이름 | 타입 | 필수 | 제약 조건 | 설명 |
| --- | --- | --- | --- | --- |
| `patient_id` | integer(int64) | Y | 1 이상 | 수정할 환자의 고유 ID |

#### Request Body

```json
{
  "name": "홍길동",
  "phone_number": "01012345678"
}
```

| 필드 | 타입 | 필수 | 제약 조건 | DB 매핑 |
| --- | --- | --- | --- | --- |
| `name` | string | Y | 앞뒤 공백 제거 후 1~30자 | `patients.name` |
| `phone_number` | string | Y | 숫자로만 구성된 10~11자 | `patients.phone` |

현재 화면의 두 입력란에는 모두 `required`가 설정되어 있고 프론트엔드가 두 필드를 항상 전송하므로 본 명세에서도 두 값을 필수로 정의한다.

프론트엔드는 전화번호에서 숫자가 아닌 문자를 제거한 뒤 전송한다. API도 브라우저 외 클라이언트의 요청을 고려해 숫자 여부와 길이를 다시 검증해야 한다.

#### 요청 예시

```bash
curl -X PATCH "http://localhost:8000/api/v1/patients/42" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "홍길동",
    "phone_number": "01012345678"
  }'
```

### 4.3 성공 응답

#### `200 OK`

```json
{
  "id": 42,
  "name": "홍길동",
  "age": 45,
  "gender": "male",
  "phone_number": "01012345678",
  "created_at": "2026-07-15T10:20:30",
  "updated_at": "2026-07-20T15:30:00"
}
```

| 필드 | 타입 | Nullable | 설명 |
| --- | --- | --- | --- |
| `id` | integer(int64) | N | 환자 고유 ID |
| `name` | string | N | 수정된 환자 이름 |
| `age` | integer | N | 환자 나이 |
| `gender` | string enum | Y | `male` 또는 `female` |
| `phone_number` | string | N | 숫자만 저장된 환자 연락처 |
| `created_at` | string(datetime) | N | 환자 등록 일시 |
| `updated_at` | string(datetime) | Y | 환자 정보 수정 일시 |

### 4.4 실패 응답

#### `401 Unauthorized`

```json
{
  "detail": "인증된 사용자를 찾을 수 없습니다."
}
```

토큰 자체가 유효하지 않으면 인증 코드의 현재 규칙에 따라 `invalid_token` 또는 `expired_token`이 `detail`에 반환될 수 있다.

#### `403 Forbidden`

```json
{
  "detail": "허용되지 않은 권한입니다."
}
```

#### `404 Not Found`

```json
{
  "detail": "해당 환자를 찾을 수 없습니다."
}
```

#### `422 Unprocessable Entity`

다음 경우에 반환한다.

- `patient_id`가 1보다 작음
- 이름이 비어 있거나 30자를 초과함
- 전화번호가 숫자가 아님
- 전화번호 길이가 10~11자가 아님
- 필수 필드가 누락됨

#### `500 Internal Server Error`

```json
{
  "detail": "환자 정보 수정 중 오류가 발생했습니다."
}
```

### 4.5 처리 절차

1. JWT를 검증하고 활성 사용자 및 역할을 확인한다.
2. 요청 본문의 이름과 전화번호를 검증한다.
3. `patient_id`로 환자를 조회한다.
4. 환자가 없으면 `404 Not Found`를 반환한다.
5. `Patient.name`과 `Patient.phone`을 변경한다.
6. 트랜잭션을 커밋하고 환자 객체를 refresh한다.
7. DB의 `M` 또는 `F`를 `male` 또는 `female`로 변환한다.
8. DB의 `phone`을 응답의 `phone_number`로 변환해 반환한다.
9. DB 오류가 발생하면 rollback 후 `500`을 반환한다.

### 4.6 인수 조건

- 유효한 이름과 전화번호를 보내면 두 값이 수정되고 `200`을 반환한다.
- 응답 필드명이 프론트엔드가 사용하는 `phone_number`와 일치한다.
- 나이와 성별은 변경되지 않는다.
- 존재하지 않는 환자는 `404`를 반환한다.
- 잘못된 입력값은 DB를 변경하지 않고 `422`를 반환한다.
- 권한이 없는 사용자는 DB를 변경하지 않고 `403`을 반환한다.

---

## 5. REQ-PTNT-005 환자 정보 삭제

### 5.1 API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 환자 정보 삭제 |
| 요구사항 ID | `REQ-PTNT-005` |
| Method | `DELETE` |
| Endpoint | `/api/v1/patients/{patient_id}` |
| 인증 | 필수 |
| 권한 | `STAFF`, `ADMIN` |
| Request Body | 없음 |
| 성공 상태 | `204 No Content` |

환자 상세 페이지의 삭제 확인 모달에서 호출한다. 환자와 연결된 진료기록, X-Ray 이미지, AI 분석 결과 및 로컬 이미지 파일을 함께 영구 삭제한다.

### 5.2 요청

#### Path Parameter

| 이름 | 타입 | 필수 | 제약 조건 | 설명 |
| --- | --- | --- | --- | --- |
| `patient_id` | integer(int64) | Y | 1 이상 | 삭제할 환자의 고유 ID |

요청 본문과 쿼리 파라미터는 없다.

#### 요청 예시

```bash
curl -X DELETE "http://localhost:8000/api/v1/patients/42" \
  -H "Authorization: Bearer <access_token>"
```

### 5.3 성공 응답

#### `204 No Content`

응답 본문은 반환하지 않는다. 이는 `static/apis.js`의 공통 요청 함수가 `204` 응답을 `null`로 처리하는 동작과 일치한다.

```http
HTTP/1.1 204 No Content
```

삭제 대상은 다음과 같다.

| 저장 위치 | 삭제 대상 |
| --- | --- |
| `patients` | 대상 환자 |
| `medical_records` | 환자의 모든 진료기록 |
| `xray_images` | 진료기록의 모든 X-Ray 메타데이터 |
| `ai_analysis_results` | 진료기록의 모든 AI 분석 결과 |
| 로컬 `media` 디렉터리 | `image_url`이 가리키는 X-Ray 파일 |
| 로컬 `media` 디렉터리 | `heatmap_url`이 가리키는 AI Heatmap 파일 |

### 5.4 실패 응답

#### `401 Unauthorized`

```json
{
  "detail": "인증된 사용자를 찾을 수 없습니다."
}
```

#### `403 Forbidden`

```json
{
  "detail": "허용되지 않은 권한입니다."
}
```

#### `404 Not Found`

환자가 존재하지 않거나 이미 삭제된 경우이다.

```json
{
  "detail": "해당 환자를 찾을 수 없습니다."
}
```

#### `422 Unprocessable Entity`

`patient_id`가 정수가 아니거나 1보다 작은 경우이다.

#### `500 Internal Server Error`

```json
{
  "detail": "환자 정보 삭제 중 오류가 발생했습니다."
}
```

### 5.5 처리 절차

1. JWT를 검증하고 활성 사용자 및 역할을 확인한다.
2. `patient_id`로 환자를 조회한다.
3. 환자가 없으면 `404 Not Found`를 반환한다.
4. 연관된 `XrayImages.image_url`과 `AIAnalysisResult.heatmap_url`을 수집한다.
5. 삭제할 파일을 `/media` 공개 경로 밖의 임시 격리 경로로 이동한다.
6. ORM을 통해 환자와 연관 데이터를 하나의 DB 트랜잭션에서 삭제한다.
7. DB 커밋에 성공하면 격리한 파일을 영구 삭제하고 `204`를 반환한다.
8. DB 커밋에 실패하면 rollback하고 격리 파일을 원래 위치로 복구한 뒤 `500`을 반환한다.

파일이 이미 존재하지 않는 경우에는 DB 삭제를 중단하지 않고 누락 사실을 로그로 남긴다. 저장된 경로를 사용할 때에는 정규화한 실제 경로가 프로젝트의 `media` 디렉터리 아래인지 확인하여 임의 경로 삭제를 방지한다.

### 5.6 연쇄 삭제 구현 주의사항

현재 ORM 관계에는 삭제 cascade가 설정되어 있지만 `xray_images.record_id`와 `ai_analysis_results.record_id`에는 DB 레벨 `ON DELETE CASCADE`가 없다.

따라서 다음 중 하나를 적용해야 한다.

1. 관계 데이터를 로드한 Patient 객체에 `await db.delete(patient)`를 사용하여 ORM cascade로 삭제한다.
2. 두 외래키에 `ON DELETE CASCADE`를 추가하는 Alembic migration을 작성한다.

현재 구조에서 `delete(Patient).where(...)` 형태의 bulk delete만 실행하면 하위 외래키 제약 조건 때문에 실패하거나 로컬 파일 경로를 수집하지 못할 수 있으므로 사용하지 않는다.

### 5.7 인수 조건

- 존재하는 환자를 삭제하면 `204`를 반환한다.
- 삭제 후 동일한 환자를 조회하면 `404`를 반환한다.
- 환자의 모든 진료기록, X-Ray 메타데이터 및 AI 분석 결과가 삭제된다.
- X-Ray와 Heatmap 파일이 `/media` URL로 더 이상 노출되지 않는다.
- 존재하지 않는 환자를 삭제하면 `404`를 반환한다.
- 권한이 없는 사용자는 DB와 파일 시스템을 변경하지 않고 `403`을 반환한다.
- DB 삭제 실패 시 데이터와 접근 가능한 파일의 상태가 삭제 전으로 복구된다.

## 6. 구현 대상 파일

| 파일 | 필요한 작업 |
| --- | --- |
| `app/schemas/patient.py` | 수정 요청 및 환자 응답 Pydantic 스키마 작성 |
| `app/apis/patient_apis.py` | PATCH 및 DELETE 엔드포인트 구현, 인증·권한 적용 |
| `app/main.py` | Patient 라우터 import 및 등록 |
| `app/models/xray_images.py` | 필요 시 `record_id`에 `ondelete="CASCADE"` 추가 |
| `app/models/ai_analysis_results.py` | 필요 시 `record_id`에 `ondelete="CASCADE"` 추가 |
| `alembic/versions/` | DB cascade 정책 변경 시 migration 추가 |
| `tests/` | 정상, 권한, 유효성 검사, rollback, 파일 삭제 테스트 작성 |

권장 라우터 선언은 프론트엔드의 실제 호출 경로와 일치하도록 다음과 같이 구성한다.

```python
router = APIRouter(
    prefix="/api/v1/patients",
    tags=["patient"],
    route_class=TimeoutRoute,
)
```

## 7. 최종 API 요약

| 요구사항 ID | Method | Endpoint | 성공 응답 | 기능 |
| --- | --- | --- | --- | --- |
| `REQ-PTNT-004` | `PATCH` | `/api/v1/patients/{patient_id}` | `200 OK` | 이름 및 전화번호 수정 |
| `REQ-PTNT-005` | `DELETE` | `/api/v1/patients/{patient_id}` | `204 No Content` | 환자와 모든 연관 데이터 영구 삭제 |
