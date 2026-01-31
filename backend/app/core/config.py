

from pydantic_settings import BaseSettings
from functools import lru_cache

from typing import List
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ChatBotDanSu API"
    BACKEND_CORS_ORIGINS: List[str] = []
    
    # Database
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SERVER: str = ""
    POSTGRES_DB: str = ""


    DATABASE_URL: str = ""

    # JWT
    SECRET_KEY: str  
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 0
    REFRESH_TOKEN_EXPIRE_DAYS: int = 0
    

    # Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""


    # Local LLM (Ollama)
    OLLAMA_BASE_URL: str = ""
    LOCAL_MODEL_NAME: str = ""

    # Security
    DATA_INTEGRITY_HASH: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore" # Bỏ qua các biến thừa trong .env không được khai báo



    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Nếu chưa có DATABASE_URL, tự động build từ các biến thành phần
        if not self.DATABASE_URL:
            from urllib.parse import quote_plus
            encoded_pwd = quote_plus(self.POSTGRES_PASSWORD)
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_pwd}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        
        # Đảm bảo dùng asyncpg driver
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


@lru_cache()
def get_settings():
    return Settings()
