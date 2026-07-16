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

## 5. 회원 권한 변경 (REQ-USER-005)

|**Method**: PATCH
|**Endpoint**: /users/{user_id}/role
|**Description**: 관리자가 특정 유저의 권한(대기자, 스태프, 어드민)을 변경합니다.
|**Request Body**:
    JSON
        {
        "role": "string"
        }

**6. 마이페이지 조회 (REQ-USER-006)

        Method: GET
        Endpoint: /users/me
        Description: 로그인한 사용자의 상세 정보를 조회합니다.

**7. 회원 정보 수정 (REQ-USER-007)

        Method: PATCH
        Endpoint: /users/me
        Description: 로그인한 사용자의 정보를 수정합니다. (부서, 휴대폰 번호)
        Request Body:
            JSON
                {
                "department": "string",
                "phone": "string"
                }

** 8. 비밀번호 변경 (REQ-USER-008)
        Method: PATCH
        Endpoint: /users/me/password
        Description: 기존 비밀번호를 확인 후 새로운 비밀번호로 변경합니다.
    Request Body:

        JSON
            {
            "current_password": "string",
            "new_password": "string"
            }
        9. 회원 탈퇴 (REQ-USER-009)
        Method: DELETE

        Endpoint: /users/me

        Description: 사용자의 계정과 관련 정보를 DB에서 삭제합니다.