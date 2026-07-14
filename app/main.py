import os
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse
from app.apis.practice_apis import add_user, UserCreate, user_list

# apis 패키지에서 라우터를 가져옵니다.
from app.apis.practice_apis import router as practice_router

app = FastAPI()

# 라우터 등록
app.include_router(practice_router)

BASE_DIR = Path(__file__).resolve().parent.parent

# 만약 static, media 폴더가 존재하지 않으면 생성
if not (BASE_DIR / "static").exists():
    os.mkdir(BASE_DIR / "static")
if not (BASE_DIR / "media").exists():
    os.mkdir(BASE_DIR / "media")

# 'static' 폴더를 '/static' 경로로 마운트 (CSS, JS 파일 서빙용)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
# 'media' 폴더를 '/media' 경로로 마운트 (사용자 업로드 파일 서빙용)
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")


@app.get(path="/healthcheck", status_code=200, include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    # API나 정적 파일 경로는 제외 (FastAPI가 먼저 매칭하지 못한 경우에만 실행됨)
    if (
        path.startswith("api/v1")
        or path.startswith("static/")
        or path.startswith("media/")
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
    return FileResponse(BASE_DIR / "static" / "index.html")

# 1. 전체 유저 목록 확인 (확인용)
@app.get("/users")
def read_users():
    return user_list

# 2. 회원 추가 API
@app.post("/practice_api/users")
def create_user(user: UserCreate):
    try:
        new_user = add_user(user)
        return {"message": "회원가입 성공!", "user": new_user}
    except ValueError as e:
        # Pydantic 검증에서 걸리지 않은 비즈니스 로직 에러(이메일 중복 등) 처리
        raise HTTPException(status_code=400, detail=str(e))