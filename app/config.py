from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # X credentials (placeholders; fill with your own)
    X_BEARER_TOKEN: str | None = None
    X_CONSUMER_KEY: str | None = None
    X_CONSUMER_SECRET: str | None = None
    X_ACCESS_TOKEN: str | None = None
    X_ACCESS_TOKEN_SECRET: str | None = None

    BOT_USERNAME: str = "isthisai"
    BOT_HANDLE: str = "@isthisai"

    # Media processing limits
    MAX_VIDEO_SECONDS: int = 60
    MAX_VIDEO_FRAMES: int = 30
    FRAME_FPS: int = 1

    # Anti-spam / safety
    REPLY_COOLDOWN_SECONDS: int = 60
    DOWNLOAD_TIMEOUT_SECONDS: int = 30
    MAX_DOWNLOAD_MB: int = 40

settings = Settings()
