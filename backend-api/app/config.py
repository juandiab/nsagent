from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nsagent_encryption_key: str
    mongo_uri: str = "mongodb://mongodb:27017"
    mongo_db: str = "netscaler_copilot"
    mcp_server_url: str = "http://mcp-server:8001"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    admin_username: str = "admin"
    admin_password: str = "admin"


settings = Settings()
