from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "root"
    DB_PASSWORD: str = "password1234"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "ai_health"
   
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10 # 기본적으로 유지할 DB 연결 수
    DB_MAX_OVERFLOW: int = 20 # 기본 풀을 초과해 임시 생성할 연결 수
    DB_POOL_TIMEOUT: int = 30 # 연결을 얻기 위해 기다릴 최대 시간
    DB_POOL_RECYCLE: int = 1800 #30분이 지난 연결을 교체
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()

