from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "TrustVault"
    database_url: str = "postgresql+psycopg://trustvault:trustvault_dev@localhost:5432/trustvault"
    jwt_secret_key: str = "CHANGE-ME-BEFORE-RUNNING"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    storage_path: str = "./storage"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
