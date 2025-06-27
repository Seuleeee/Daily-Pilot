from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

current_directory = Path(__file__).parent
backend_directory = current_directory.parent.parent
project_directory = backend_directory.parent
dotenv_path = project_directory / ".env.dev"  # TODO: 향후 dev, stage 분리 필요.

load_dotenv(dotenv_path=dotenv_path)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,  # 대소문자 구분 허용
        env_file=".env",  # settings env file name
        env_file_encoding="utf-8",  # setting env file encoding
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
    ME_PASSWORD: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_URL: str

    OPENAI_API_KEY: str


@lru_cache
def get_settings():
    """"""
    return Settings()
