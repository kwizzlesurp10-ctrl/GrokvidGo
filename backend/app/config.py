from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    grok_api_key: str
    elevenlabs_api_key: str
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_secret: str
    x_bearer_token: str
    supabase_url: str
    supabase_service_key: str
    redis_url: str = "redis://redis:6379/0"
    virality_threshold: float = 70.0

    model_config = {"env_file": ".env"}


settings = Settings()
