from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cookbook API"
    database_url: str = "postgresql+psycopg://cookbook:cookbook@localhost:5432/cookbook"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret-key-change-me-0123456789abcdef"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = [
        "http://localhost:8081",
        "http://localhost:3000",
        "http://nirvanamaple.cn",
        "https://nirvanamaple.cn",
        "http://web.nirvanamaple.cn",
        "https://web.nirvanamaple.cn",
        "http://123.56.254.175",
    ]

    import_source: str = "chinese-recipes-corpus"
    import_sample_limit: int = 2000
    import_cron_hour: int = 3
    import_cron_minute: int = 17
    import_data_dir: str = "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
