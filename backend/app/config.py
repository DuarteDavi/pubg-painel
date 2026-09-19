from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./survival_macro.db"

    admin_login: str = ""
    admin_password_hash: str = ""

    jwt_secret: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15
    jwt_refresh_expiration_days: int = 7

    cors_origins: str = "http://127.0.0.1:5175,http://localhost:5175,https://survival.techduarte.tech"
    rate_limit_attempts: int = 5
    rate_limit_minutes: int = 15
    session_expiration_hours: int = 8

    api_host: str = "0.0.0.0"
    api_port: int = 3020
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
