import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshTokenResponse,
    UserResponse,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db.databases import async_get_db
from app.models.users import User

from app.core.security import verify_password

from app.core.config import settings

#####################################################
# 1. 라우터 선언
#####################################################
router = APIRouter(prefix="/auth_api", tags=["auth"])

#####################################################
# 2. API Endpoints 구현
#####################################################
# Bearer 토큰 보안 스키마 정의
security = HTTPBearer()

SECRET_KEY = settings.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = (
    settings.ACCESS_TOKEN_EXPIRE_MINUTES
)    # 액세스 토큰 만료주기           
REFRESH_TOKEN_EXPIRE_DAYS = (
    settings.REFRESH_TOKEN_EXPIRE_DAYS
)       # 리프레시 토큰 만료주기


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _create_jwt(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _base64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = _base64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    encoded_signature = _base64url_encode(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_jwt(
    token: str,
    invalid_detail: str = "invalid_refresh_token",
    expired_detail: str = "expired_refresh_token",
) -> dict:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= invalid_detail,
        ) from exc

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    provided_signature = _base64url_decode(encoded_signature)

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= invalid_detail,
        )

    try:
        payload = json.loads(_base64url_decode(encoded_payload).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= invalid_detail,
        ) from exc

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= invalid_detail,
        )

    now_timestamp = int(datetime.now(timezone.utc).timestamp())
    if exp < now_timestamp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= expired_detail,
        )

    return payload


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return _create_jwt(payload)


def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }
    return _create_jwt(payload)

# 현재 로그인 사용자 ID 반환
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> int:
    token = credentials.credentials

    payload = decode_jwt(
        token,
        invalid_detail="invalid_token",
        expired_detail="expired_token",
    )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    user_id = payload.get("user_id")

    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    return user_id
# 로그인
@router.post("/v1/auth/login/", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest, 
    response: Response,
    db: AsyncSession = Depends(async_get_db)
) -> LoginResponse:
    email = body.email.strip()

    if not email or not body.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="empty_fields",
        )
    
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if (
    user is None
    or user.hashed_password is None
    or not verify_password(
        body.password,
        user.hashed_password,
    )
):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다."
        )
        
    if not user.is_active:
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="비활성화된 계정입니다.",
    )
    access_token = create_access_token(user_id = user.id)
    refresh_token = create_refresh_token(user_id = user.id)
    
    # refresh token - 쿠키로 저장
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.name,
        ),
    )
  
# 인증/인가   
@router.post(
    "/v1/auth/refresh/",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_access_token(
    request: Request,
    response: Response,
) -> RefreshTokenResponse:
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_refresh_token",
        )

    try:
        payload = decode_jwt(refresh_token)
    except HTTPException as exc:
        # 리프레시 토큰 만료
        if exc.detail == "expired_refresh_token":
            response.delete_cookie(key="refresh_token")
            raise exc
        raise exc

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_refresh_token",
        )

    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_refresh_token",
        )

    new_access_token = create_access_token(user_id=user_id)
    return RefreshTokenResponse(access_token=new_access_token)

# 로그아웃
@router.post(
    "/v1/auth/logout/",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> MessageResponse:
    access_token = credentials.credentials.strip()
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    payload = decode_jwt(
        access_token,
        invalid_detail="invalid_token",
        expired_detail="expired_token",
    )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    response.delete_cookie(key="refresh_token")
    return MessageResponse(detail="로그아웃이 완료되었습니다.")