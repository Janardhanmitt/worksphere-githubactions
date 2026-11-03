from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_host: str = "localhost"
    database_port: int = 3306
    database_name: str = "worksphere"
    database_username: str = "worksphere_user"
    database_password: str = "change_me"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus
        user, password = quote_plus(self.database_username), quote_plus(self.database_password)
        return f"mysql+pymysql://{user}:{password}@{self.database_host}:{self.database_port}/{self.database_name}?charset=utf8mb4"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
