from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://docsearch:docsearch@localhost:5432/docsearch"
    elasticsearch_url: str = "http://localhost:9200"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="")


settings = Settings()