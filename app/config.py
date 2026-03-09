from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    deepinfra_api_key: str
    app_api_key: str
    max_file_size_mb: int = 20

    model_config = {"env_file": ".env"}


settings = Settings()
