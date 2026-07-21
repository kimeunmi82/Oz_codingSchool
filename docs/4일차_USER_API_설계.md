markdown_content = """# 4일차 User API 설계서

본 문서는 프로젝트의 User 관련 기능에 대한 API 엔드포인트 명세입니다.

---

## 1. 인증 및 사용자 관리 API

| 기능 | Method | Endpoint | 설명 |
| :--- | :--- | :--- | :--- |
| **회원가입** | POST | `/users/signup` | 신규 사용자 등록 |
| **로그인** | POST | `/users/login` | 이메일/비밀번호 인증 후 JWT 토큰 발급 |
| **로그아웃** | POST | `/users/logout` | 사용자 로그아웃 처리 |
| **회원 탈퇴** | DELETE | `/users/me` | 계정 정보 즉시 삭제 |

## 2. 관리자 및 목록 조회 API

| 기능 | Method | Endpoint | 설명 |
| :--- | :--- | :--- | :--- |
| **회원 목록 조회** | GET | `/users` | 전체 회원 목록 조회 (필터링/검색 포함) |
| **회원 권한 변경** | PATCH | `/users/{user_id}/role` | 특정 사용자의 권한(대기자, 스태프, 어드민) 변경 |

## 3. 마이페이지 API

| 기능 | Method | Endpoint | 설명 |
| :--- | :--- | :--- | :--- |
| **마이페이지 조회** | GET | `/users/me` | 로그인한 사용자의 상세 정보 조회 |
| **회원 정보 수정** | PATCH | `/users/me` | 로그인한 사용자의 정보(부서, 휴대폰) 수정 |
| **비밀번호 변경** | PATCH | `/users/me/password` | 기존 비밀번호 확인 후 새 비밀번호 적용 |

---

## 4. 상세 요청 예시 (Request Body)

### [REQ-USER-001] 회원가입
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "홍길동",
  "department": "연구",
  "gender": "M",
  "phone": "010-1234-5678"
}
```

## 5. 회원 권한 변경 (REQ-USER-005)

**Method**: PATCH <br>
**Endpoint**: /users/{user_id}/role<br>
**Description**: 관리자가 특정 유저의 권한(대기자, 스태프, 어드민)을 변경합니다.<br>
**Request Body**:
```JSON
 {
    "role": "string"
}
```
## 6. 마이페이지 조회 (REQ-USER-006)
**Method**: GET <br>
**Endpoint**: /users/me<br>
**Description**: 로그인한 사용자의 상세 정보를 조회합니다.

## 7. 회원 정보 수정 (REQ-USER-007)
**Method**: PATCH<br>
**Endpoint**: /users/me<br>
**Description**: 로그인한 사용자의 정보를 수정합니다. (부서, 휴대폰 번호)<br>
**Request Body**:
```json
    {
        "department": "string",
        "phone": "string"
}
```

## 8. 비밀번호 변경 (REQ-USER-008)
 **Method**: PATCH<br>
 **Endpoint**: /users/me/password<br>
**Description:** 기존 비밀번호를 확인 후 새로운 비밀번호로 변경합니다.<br>
**Request Body**:

```JSON
{
    "current_password": "string",
    "new_password": "string"
}
```  
        9. 회원 탈퇴 (REQ-USER-009)
        Method: DELETE

        Endpoint: /users/me

        Description: 사용자의 계정과 관련 정보를 DB에서 삭제합니다.

# 사용자 비밀번호 변경 API 및 비기능 요구사항 명세서

## 관련 데이터베이스 컬럼

| 컬럼 | 타입 | 용도 |
| --- | --- | --- |
| `users.id` | integer, PK | 인증된 사용자 식별 |
| `users.email` | varchar(255), unique | 로그인 식별자 |
| `users.hashed_password` | varchar(255) | 단방향 해시 비밀번호 저장 |
| `users.is_active` | boolean | 계정 활성화 여부 확인 |
| `users.updated_at` | datetime | 비밀번호 변경 일시 기록 |

---

# REQ-USER-008 - 사용자 비밀번호 변경

## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 사용자 비밀번호 변경 API |
| 요구사항 ID | `REQ-USER-008` |
| 설명 | 로그인 사용자의 현재 비밀번호를 검증한 후 새 비밀번호로 변경한다. |
| 엔드포인트 | `/api/v1/users/me/password/` |
| 메서드 | `PATCH` |
| 인증 필요 여부 | Y |
| 관련 테이블 | `users` |
| 목표 응답 시간 | 3초 이내 |

---

## 2. 요청(Request)

### Headers

| Key | Value | 필수 | 설명 |
| --- | --- | --- | --- |
| Content-Type | `application/json` | Y | 요청 본문 형식 |
| Authorization | `Bearer <access_token>` | Y | JWT 액세스 토큰 |

### 본문 예시

```json
{
  "current_password": "CurrentPassword123!",
  "new_password": "NewPassword456!"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `current_password` | string | Y | 현재 사용 중인 비밀번호 |
| `new_password` | string | Y | 새로 변경할 비밀번호 |

### 유효성 검사

| 항목 | 조건 |
| --- | --- |
| 현재 비밀번호 | 저장된 `users.hashed_password`와 일치해야 한다. |
| 새 비밀번호 | 현재 비밀번호와 달라야 한다. |
| 길이 | 8자 이상 128자 이하 |
| 구성 | 영문, 숫자, 특수문자를 각각 1개 이상 포함 |
| 계정 상태 | `users.is_active = true`여야 한다. |

### Pydantic 요청 스키마 예시

```python
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class PasswordChangeRequest(BaseModel):
    current_password: Annotated[
        str,
        Field(min_length=8, max_length=128),
    ]
    new_password: Annotated[
        str,
        Field(min_length=8, max_length=128),
    ]

    @model_validator(mode="after")
    def validate_different_passwords(self):
        if self.current_password == self.new_password:
            raise ValueError(
                "새 비밀번호는 현재 비밀번호와 달라야 합니다."
            )

        return self
```

### 쿼리 파라미터

없음.

---

## 3. 응답(Response)

### 성공 - `200 OK`

```json
{
  "message": "비밀번호가 변경되었습니다.",
  "updated_at": "2026-07-16T14:30:00+09:00"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `message` | string | 처리 결과 메시지 |
| `updated_at` | string(datetime) | 비밀번호 변경 일시 |

### 실패 - `400 Bad Request`

```json
{
  "code": "INVALID_CURRENT_PASSWORD",
  "message": "현재 비밀번호가 일치하지 않습니다."
}
```

| 오류 코드 | 발생 조건 |
| --- | --- |
| `EMPTY_FIELDS` | 필수값이 누락된 경우 |
| `INVALID_CURRENT_PASSWORD` | 현재 비밀번호가 일치하지 않는 경우 |
| `SAME_AS_CURRENT_PASSWORD` | 새 비밀번호가 현재 비밀번호와 같은 경우 |
| `INVALID_PASSWORD_FORMAT` | 새 비밀번호가 비밀번호 정책을 충족하지 않는 경우 |

### 실패 - `401 Unauthorized`

```json
{
  "code": "UNAUTHORIZED",
  "message": "로그인이 필요합니다."
}
```

발생 조건:

- 액세스 토큰이 없는 경우
- 액세스 토큰이 만료된 경우
- 유효하지 않은 토큰인 경우

### 실패 - `403 Forbidden`

```json
{
  "code": "INACTIVE_ACCOUNT",
  "message": "비활성화된 계정입니다."
}
```

### 실패 - `404 Not Found`

```json
{
  "code": "USER_NOT_FOUND",
  "message": "사용자 정보를 찾을 수 없습니다."
}
```

### 실패 - `429 Too Many Requests`

```json
{
  "code": "TOO_MANY_REQUESTS",
  "message": "요청 횟수가 너무 많습니다. 잠시 후 다시 시도해 주세요."
}
```

### 실패 - `500 Internal Server Error`

```json
{
  "code": "INTERNAL_SERVER_ERROR",
  "message": "서버 오류가 발생했습니다."
}
```

### 오류 응답 공통 필드

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `code` | string | 클라이언트가 오류를 구분하는 코드 |
| `message` | string | 사용자에게 표시할 오류 메시지 |
| `errors` | object | 필드별 상세 오류. 필요한 경우에만 반환 |

---

## 4. 데이터베이스 처리

### 관련 컬럼

| 컬럼 | 사용 목적 |
| --- | --- |
| `users.id` | 인증 사용자 조회 |
| `users.hashed_password` | 현재 비밀번호 검증 및 새 해시 저장 |
| `users.is_active` | 활성 계정 여부 확인 |
| `users.updated_at` | 비밀번호 변경 일시 기록 |

### 사용자 조회 SQL

```sql
SELECT
  id,
  hashed_password,
  is_active,
  updated_at
FROM users
WHERE id = :authenticated_user_id;
```

`authenticated_user_id`는 요청 본문이 아니라 검증된 JWT에서 가져온다.

### 사용자 조회 SQLAlchemy

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


async def get_user_for_password_change(
    db: AsyncSession,
    authenticated_user_id: int,
) -> User | None:
    statement = (
        select(User)
        .where(User.id == authenticated_user_id)
    )

    result = await db.execute(statement)

    return result.scalar_one_or_none()
```

### 사용자 상태 검사

```python
user = await get_user_for_password_change(
    db=db,
    authenticated_user_id=authenticated_user_id,
)

if user is None:
    raise UserNotFoundError

if not user.is_active:
    raise InactiveAccountError

if user.hashed_password is None:
    raise PasswordNotConfiguredError
```

### 현재 비밀번호 검증

```python
if not verify_password(
    plain_password=current_password,
    hashed_password=user.hashed_password,
):
    raise InvalidCurrentPasswordError
```

비밀번호 평문과 해시 문자열을 `==` 연산자로 직접 비교하지 않고, Argon2 또는 bcrypt와 같은 비밀번호 해시 라이브러리의 검증 함수를 사용한다.

### 비밀번호 변경 SQL

```sql
UPDATE users
SET
  hashed_password = :new_hashed_password,
  updated_at = CURRENT_TIMESTAMP
WHERE id = :authenticated_user_id;
```

### 비밀번호 변경 SQLAlchemy

```python
user.hashed_password = hash_password(new_password)

try:
    await db.commit()
    await db.refresh(user)
except Exception:
    await db.rollback()
    raise
```

현재 `User.updated_at`에는 `onupdate=func.now()`가 설정되어 있으므로 UPDATE 실행 시 변경 시간이 자동으로 기록된다.

### 전체 처리 순서

1. JWT를 검증한다.
2. JWT에서 사용자 ID를 가져온다.
3. SQLAlchemy로 `users.id`를 조회한다.
4. 사용자 존재 여부와 `users.is_active`를 확인한다.
5. 현재 비밀번호를 `users.hashed_password`와 검증한다.
6. 새 비밀번호를 단방향 해싱한다.
7. `User.hashed_password`에 새 해시를 할당한다.
8. `commit()`을 실행하고 `updated_at`을 갱신한다.
9. 실패 시 `rollback()`을 실행한다.

---

## 5. 비고

- 비밀번호 평문을 DB에 저장하지 않는다.
- 비밀번호 평문이나 해시를 API 응답에 포함하지 않는다.
- 비밀번호를 서버 로그 또는 오류 추적 서비스에 기록하지 않는다.
- 비밀번호 해싱에는 Argon2id 또는 bcrypt 사용을 권장한다.
- 현재 DB에는 토큰 관리 테이블이 없으므로 비밀번호 변경 후 기존 JWT를 즉시 폐기하려면 추가 설계가 필요하다.

---

# NFR-USER-002 - 비밀번호 입력 보안

## 1. 요구사항 개요

| 항목 | 내용 |
| --- | --- |
| 요구사항 이름 | 비밀번호 입력 보안 |
| 요구사항 ID | `NFR-USER-002` |
| 설명 | 모든 비밀번호 입력란을 기본적으로 마스킹하며, 보기 아이콘으로 입력한 비밀번호를 확인할 수 있도록 한다. |
| 분류 | 비기능 요구사항 - 보안 및 사용성 |
| 적용 대상 | 로그인, 회원가입, 비밀번호 변경, 비밀번호 재설정 화면 |
| 엔드포인트 | 해당 없음 |
| 메서드 | 해당 없음 |
| 인증 필요 여부 | 적용 화면에 따라 다름 |
| 관련 DB 컬럼 | `users.hashed_password` |

---

## 2. 입력(Input)

### 입력 화면 예시

```html
<label for="current-password">현재 비밀번호</label>
<input
  id="current-password"
  name="current_password"
  type="password"
  autocomplete="current-password"
/>

<button
  type="button"
  aria-label="비밀번호 보기"
  aria-pressed="false"
>
  보기
</button>
```

### 입력 필드

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `current_password` | password | 화면에 따라 Y | 현재 비밀번호 |
| `new_password` | password | 화면에 따라 Y | 새 비밀번호 |
| 비밀번호 보기 버튼 | button | Y | 마스킹 상태 변경 |

### 화면 상태

| 상태 | input type | 버튼 설명 |
| --- | --- | --- |
| 기본 상태 | `password` | 비밀번호 보기 |
| 비밀번호 표시 상태 | `text` | 비밀번호 숨기기 |

### 쿼리 파라미터

해당 없음.

---

## 3. 결과(Output)

### 정상 동작

| 사용자 동작 | 결과 |
| --- | --- |
| 비밀번호 입력 | 입력 문자가 마스킹된다. |
| 보기 아이콘 선택 | 입력한 비밀번호가 평문으로 표시된다. |
| 숨기기 아이콘 선택 | 비밀번호가 다시 마스킹된다. |
| 표시 상태 변경 | 입력값과 커서 위치가 유지된다. |
| 페이지 새로고침 | 기본 마스킹 상태로 초기화된다. |
| 키보드 사용 | `Tab`, `Enter`, `Space`로 버튼을 조작할 수 있다. |

### 요구사항 미충족 조건

| 식별 코드 | 조건 |
| --- | --- |
| `PASSWORD_NOT_MASKED` | 화면 진입 시 비밀번호가 평문으로 표시되는 경우 |
| `PASSWORD_TOGGLE_FAILED` | 보기 또는 숨기기 기능이 작동하지 않는 경우 |
| `PASSWORD_VALUE_RESET` | 표시 상태 변경 시 입력값이 초기화되는 경우 |
| `PASSWORD_LOGGED` | 비밀번호가 콘솔이나 로그에 기록되는 경우 |
| `PASSWORD_EXPOSED_IN_RESPONSE` | 비밀번호 또는 해시가 API 응답에 포함되는 경우 |
| `PASSWORD_TOGGLE_INACCESSIBLE` | 키보드나 스크린 리더로 버튼을 사용할 수 없는 경우 |

위 식별 코드는 API 오류 코드가 아니라 테스트 및 결함 관리용 코드이다.

---

## 4. 데이터 처리 및 SQLAlchemy

화면 마스킹은 프론트엔드 기능이므로 SQLAlchemy가 직접 처리하지 않는다. SQLAlchemy는 제출된 새 비밀번호를 해싱한 후 저장하는 역할을 담당한다.

### 올바른 처리

```python
new_hashed_password = hash_password(new_password)

user.hashed_password = new_hashed_password

await db.commit()
```

### 금지되는 처리

```python
# 평문 저장 금지
user.hashed_password = new_password

await db.commit()
```

### 데이터 처리 흐름

```text
비밀번호 입력
  ↓ 화면 마스킹
HTTPS 요청
  ↓
FastAPI 요청 검증
  ↓
비밀번호 단방향 해싱
  ↓
SQLAlchemy User.hashed_password 할당
  ↓
DB에는 해시값만 저장
```

### API 응답 처리

SQLAlchemy의 `User` 객체를 직접 반환하지 않고 별도의 응답 스키마를 사용한다.

```python
return PasswordChangeResponse(
    message="비밀번호가 변경되었습니다.",
    updated_at=user.updated_at,
)
```

---

## 5. 검증 기준

| 검증 항목 | 기대 결과 |
| --- | --- |
| 최초 화면 진입 | 비밀번호가 마스킹된다. |
| 보기 버튼 | 비밀번호가 표시된다. |
| 숨기기 버튼 | 비밀번호가 다시 마스킹된다. |
| 표시 상태 변경 | 입력값이 유지된다. |
| API 응답 | `hashed_password`가 포함되지 않는다. |
| 서버 로그 | 비밀번호 평문이 존재하지 않는다. |
| DB 저장값 | 해시 문자열만 존재한다. |
| 접근성 | 버튼의 현재 기능을 스크린 리더가 안내한다. |

---

## 6. 비고

- 화면 마스킹은 비밀번호 암호화가 아니다.
- 데이터 전송에는 HTTPS를 사용해야 한다.
- 비밀번호 평문을 콘솔, 로그 또는 오류 추적 서비스에 기록하지 않는다.
- `aria-label`은 상태에 따라 `비밀번호 보기` 또는 `비밀번호 숨기기`로 변경한다.
- `hashed_password`도 클라이언트에 전달하지 않는다.

---

# NFR-USER-003 - 사용자 API 성능

## 1. 요구사항 개요

| 항목 | 내용 |
| --- | --- |
| 요구사항 이름 | 사용자 API 성능 |
| 요구사항 ID | `NFR-USER-003` |
| 설명 | 모든 사용자 API는 정상 운영 조건에서 3초 이내에 로직을 처리하고 응답해야 한다. |
| 분류 | 비기능 요구사항 - 성능 |
| 적용 엔드포인트 | `/api/v1/users/**`, `/api/v1/auth/**` |
| 메서드 | `GET`, `POST`, `PATCH`, `DELETE` |
| 인증 필요 여부 | API에 따라 다름 |
| 주요 관련 테이블 | `users` |
| 성능 목표 | p95 응답 시간 3,000ms 이하 |

---

## 2. 요청(Request)

### Headers

각 사용자 API 명세에 정의된 Header를 따른다.

| Key | Value | 필수 | 설명 |
| --- | --- | --- | --- |
| Content-Type | `application/json` | API에 따라 다름 | 요청 본문 형식 |
| Authorization | `Bearer <access_token>` | API에 따라 다름 | JWT 액세스 토큰 |

### 본문

각 사용자 API 명세의 요청 본문을 따른다.

### 성능 테스트 입력 조건

| 항목 | 기준 |
| --- | --- |
| 동시 사용자 | 100명 |
| 테스트 시간 | 10분 이상 |
| 테스트 데이터 | 운영 환경과 유사한 사용자 데이터 |
| 워밍업 | 본 테스트 전에 별도로 수행 |
| 요청 분포 | 실제 사용 환경과 유사하게 구성 |

### 쿼리 파라미터

각 사용자 API 명세를 따른다.

---

## 3. 응답(Response)

### 정상 성능 기준

| 측정 항목 | 성공 기준 |
| --- | --- |
| p95 응답 시간 | 3,000ms 이하 |
| 요청 성공률 | 99% 이상 |
| HTTP 5xx 오류율 | 1% 미만 |
| 데이터 정확성 | 정상 요청의 처리 결과가 정확해야 함 |
| 보안 절차 | 인증 및 비밀번호 검증을 생략하지 않아야 함 |

### 측정 범위

| 구분 | 포함 여부 |
| --- | --- |
| JWT 인증 | 포함 |
| 요청 유효성 검사 | 포함 |
| SQLAlchemy 쿼리 실행 | 포함 |
| 데이터베이스 조회 및 변경 | 포함 |
| 비밀번호 해싱 | 포함 |
| 사용자 네트워크 지연 | 제외 |
| 클라이언트 화면 렌더링 | 제외 |

### 성능 기준 초과 기록 예시

API가 3초를 초과하더라도 API 응답 형식 자체를 변경하지 않는다. 모니터링 시스템에 다음 정보를 기록한다.

```json
{
  "endpoint": "/api/v1/users/me/password/",
  "method": "PATCH",
  "status_code": 200,
  "duration_ms": 3250
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `endpoint` | string | 호출한 API 경로 |
| `method` | string | HTTP 메서드 |
| `status_code` | integer | HTTP 응답 상태 |
| `duration_ms` | integer | 서버 처리 시간 |

---

## 4. 데이터베이스 처리 및 SQLAlchemy

### 사용자 조회 SQL

```sql
SELECT
  id,
  hashed_password,
  is_active
FROM users
WHERE id = :authenticated_user_id;
```

### 사용자 조회 SQLAlchemy

```python
statement = (
    select(User)
    .where(User.id == authenticated_user_id)
)

result = await db.execute(statement)
user = result.scalar_one_or_none()
```

`users.id`는 Primary Key이므로 인덱스를 이용해 조회한다.

### 권장 처리

한 번 조회한 `User` 객체에서 필요한 값을 함께 사용한다.

```python
user = await get_user_for_password_change(
    db=db,
    authenticated_user_id=authenticated_user_id,
)

if user is None:
    raise UserNotFoundError

if not user.is_active:
    raise InactiveAccountError

stored_password = user.hashed_password
```

### 피해야 하는 처리

동일한 사용자를 여러 번 조회하지 않는다.

```python
# 불필요한 중복 조회
user = await get_user(db, user_id)
password = await get_user_password(db, user_id)
active = await get_user_active_status(db, user_id)
```

### 비동기 SQLAlchemy 기준

현재 프로젝트는 `AsyncSession`을 사용하므로 모든 DB 실행에 `await`를 사용한다.

```python
result = await db.execute(statement)
await db.commit()
await db.refresh(user)
```

동기 방식을 혼용하지 않는다.

```python
# 현재 프로젝트 방식과 맞지 않음
result = db.execute(statement)
db.commit()
```

### 오류 발생 시 롤백

```python
try:
    await db.commit()
except Exception:
    await db.rollback()
    raise
```

---

## 5. 검증 기준

### 정상 부하

- **Given:** 운영 환경과 유사한 테스트 환경이 준비되어 있다.
- **When:** 정상 부하로 사용자 API를 호출한다.
- **Then:** 각 API의 p95 응답 시간이 3초 이하여야 한다.

### 비밀번호 변경

- **Given:** 활성 사용자가 비밀번호 변경을 요청한다.
- **When:** JWT 검증, 현재 비밀번호 검증, 새 비밀번호 해싱 및 DB 저장을 실행한다.
- **Then:** 모든 보안 절차를 포함하여 p95 응답 시간이 3초 이하여야 한다.

### 데이터 정확성

- **Given:** 여러 사용자가 동시에 요청한다.
- **When:** SQLAlchemy로 조회 및 변경 쿼리를 실행한다.
- **Then:** 인증된 사용자의 데이터만 조회 또는 변경되어야 한다.

### 오류 처리

- **Given:** 데이터베이스 저장 중 오류가 발생한다.
- **When:** `commit()`이 실패한다.
- **Then:** `rollback()`을 실행하고 일부 데이터만 저장되는 현상이 없어야 한다.

---

## 6. 성능 테스트 결과 기록 양식

| API | 요청 수 | 성공률 | 평균 | p95 | 최대 | 5xx 오류율 | 판정 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 로그인 |  |  |  |  |  |  |  |
| 사용자 조회 |  |  |  |  |  |  |  |
| 사용자 정보 변경 |  |  |  |  |  |  |  |
| 비밀번호 변경 |  |  |  |  |  |  |  |
| 회원 탈퇴 |  |  |  |  |  |  |  |

---

## 7. 비고

- 성능을 높이기 위해 JWT 검증이나 비밀번호 해싱을 생략하면 안 된다.
- `users.id`와 `users.email`의 인덱스를 활용한다.
- SQLAlchemy의 비동기 `AsyncSession`을 사용한다.
- 동일 데이터를 반복 조회하지 않는다.
- 느린 쿼리와 API 처리 시간을 모니터링한다.
- 모든 단일 요청의 절대 최대 시간을 보장하기보다는 `p95 3초 이하`를 운영 성능 기준으로 사용한다.

---

# REQ-USER-002 - 로그인 API
## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 사용자 로그인 API |
| 설명 | 이메일, 비밀번호를 활용한 로그인 API |
| 엔드포인트(Endpoint) | `/auth_api/v1/auth/login/` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | N |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |
|  |  |  |
|  |  |  |

### 본문 예시

```
{
  "email": "example@example.com",
  "password": "securepassword"
}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
| email | string | Y | 사용자 이메일 |
| password | string | Y | 사용자 비밀번호 |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |

---

## 3. 응답(Response)

### 성공

- 200 OK
    
    ```
    {
      "access_token": "string",
      "refresh_token": "string",
      "user": {
        "id": 1,
        "email": "example@example.com",
        "username": "example"
      }
    }
    ```
    
    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | access_token | string | JWT 액세스 토큰 |
    | refresh_token | string | JWT 리프레시 토큰 |
    | user | object | 사용자 정보 |

### 실패

- 404 Bad Request
    
    ```
    {
      "detail": "이메일 또는 비밀번호가 일치하지 않습니다."
    }
    ```
    
    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | detail | string | - invalid_email_or_password : 이메일 혹은 비밀번호가 잘못된 경우
    - empty_fields : 필수 필드 중 하나라도 필드가 비어있는 값인 경우 |

---

### 4. 비고

- 로그인 시 JWT(Json Web Token)를 발급하며, API 인가에 사용합니다.
- 액세스 토큰 만료주기는 30분입니다.
- 리프레시 토큰 만료주기는 7일입니다.
- JWT 페이로드에는 최소 정보인 `user_id`만 저장합니다.
- 리프레시 토큰은 클라이언트에서 접근할 수 없도록 `HttpOnly` 쿠키로 전달합니다.
---

# REQ-USER-003 - 로그아웃 API
## 1. API 개요

| 항목 | 내용 |
| --- | --- |
| API 이름 | 사용자 로그아웃 API |
| 설명 | 로그인 사용자의 세션을 종료하고 로그아웃 처리하는 API |
| 엔드포인트(Endpoint) | `/auth_api/v1/auth/logout/` |
| 메서드(Method) | `POST` |
| 인증 필요 여부 | Y |

---

## 2. 요청(Request)

### Headers

| Key | Value | 설명 |
| --- | --- | --- |
| Content-Type | application/json | 요청 타입 |
| Authorization | Bearer <access_token> | 액세스 토큰 |
|  |  |  |

### 본문 예시

```
{}
```

### 본문 필드

| 파라미터명 | 타입 | 필수 ( Y / N ) | 설명 |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |

### 쿼리 파라미터 (GET 요청시)

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |

---

## 3. 응답(Response)

### 성공

- 200 OK
    
    ```
    {
      "detail": "로그아웃이 완료되었습니다."
    }
    ```
    
    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | detail | string | 로그아웃 결과 메시지 |
    |  |  |  |
    |  |  |  |

### 실패

- 401 Unauthorized
    
    ```
    {
      "detail": "string"
    }
    ```
    
    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | detail | string | `invalid_token` : 유효하지 않은 토큰, 
    `expired_token` : 만료된 토큰 |

---

### 4. 비고

- 로그아웃 시 클라이언트는 저장된 액세스 토큰을 제거해야 합니다.
- 서버는 리프레시 토큰 쿠키를 만료 처리해야 합니다.
- 로그아웃 이후 사용자는 로그인 페이지로 전환됩니다.
---

# 데이터베이스 및 구현 권장사항

## User 모델 제약조건

현재 DB에서 이메일과 비밀번호가 로그인 계정의 필수 정보라면 다음 제약조건을 권장한다.

```python
email: Mapped[str] = mapped_column(
    String(255),
    unique=True,
    nullable=False,
)

hashed_password: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
    comment="단방향 해시로 저장된 비밀번호",
)
```

현재 모델에서 위 컬럼은 `nullable=True`이므로 실제 변경 시 기존 NULL 데이터를 확인하고 Alembic 마이그레이션을 수행해야 한다.

## JWT 무효화 정책

현재 데이터베이스에는 리프레시 토큰이나 로그인 세션 테이블이 없다. 비밀번호 변경 후 기존 JWT를 무효화해야 한다면 다음 중 한 가지 구조를 추가로 설계해야 한다.

| 정책 | 필요한 구조 |
| --- | --- |
| 기존 JWT 유지 | 추가 테이블 불필요 |
| 모든 기기 로그아웃 | 리프레시 토큰 저장 및 폐기 구조 |
| 액세스 토큰 즉시 차단 | 토큰 블랙리스트 또는 사용자 토큰 버전 |

## 구현 전 확인사항

- `hash_password()`와 `verify_password()`에 사용할 해시 라이브러리를 결정한다.
- 오류 코드와 공통 오류 응답 형식을 프로젝트 전체에서 통일한다.
- 비밀번호 변경 후 기존 로그인 세션 유지 여부를 결정한다.
- Rate Limit의 횟수와 적용 시간을 결정한다.
- 운영 환경에 맞는 성능 테스트 동시 사용자 수를 결정한다.
