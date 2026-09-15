import os


from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: os.getenv("GOOGLE_API_KEY", "")
    GITHUB_WEBHOOK_SECRET: os.getenv("GITHUB_WEBHOOK_SECRET", "")
    GITHUB_TOKEN: os.getenv("GITHUB_TOKEN", "")
    REDIS_URL: os.getenv("REDIS_URL", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()