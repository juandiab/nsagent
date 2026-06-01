from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001


settings = Settings()
