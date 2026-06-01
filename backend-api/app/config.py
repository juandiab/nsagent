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
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "NSAgent"
    webauthn_origin: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.webauthn_origin and self.webauthn_origin not in origins:
            origins.append(self.webauthn_origin)
        return origins


settings = Settings()
