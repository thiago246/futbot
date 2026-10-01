"""Configuración general. Lee variables de entorno (o usa valores por defecto)."""
import os


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-cambiar")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./futbot.db")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    API_PREFIX: str = "/api/v1"


settings = Settings()
