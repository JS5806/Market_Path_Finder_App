"""
애플리케이션 설정 (환경변수 로드)
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mart_user:changeme@localhost:5432/mart_path_db"
    DATABASE_URL_SYNC: str = "postgresql://mart_user:changeme@localhost:5432/mart_path_db"

    # JWT
    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC_ESL: str = "mart/esl/update"
    MQTT_TOPIC_BEACON: str = "mart/beacon/signal"
    MQTT_TOPIC_NFC: str = "mart/nfc/tag"

    # Local LLM
    LLM_API_BASE: str = "http://192.168.0.100:8000/v1"
    LLM_MODEL_NAME: str = "llama3-ko"

    # Server
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
