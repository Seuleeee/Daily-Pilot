import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

current_directory = Path(__file__).parent
backend_directory = current_directory.parent.parent
project_directory = backend_directory.parent

# pytest 실행 시엔 .env.dev 로드 생략
if os.getenv("PYTHON_ENV") == "test":
    print("Loading .env.test for testing environment")
    dotenv_path = project_directory / ".env.test"
else:
    print("Loading .env.dev for development environment")
    dotenv_path = project_directory / ".env.dev"

load_dotenv(dotenv_path=dotenv_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,  # 대소문자 구분 허용
        env_file_encoding="utf-8",  # setting env file encoding
        # test 환경에서는 .env 파일을 명시적으로 로드하지 않음
    )
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_URL: str

    # MongoDB
    MONGODB_HOST: str
    MONGODB_PORT: str
    MONGODB_USERNAME: str
    MONGODB_PASSWORD: str
    MONGODB_URL: str

    # Mongo Express (웹 UI용)
    ME_ADMIN: str
    ME_ADMIN_PASS: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_URL: str

    OPENAI_API_KEY: str


@lru_cache
def get_settings():
    """"""
    return Settings()
