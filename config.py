from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    telegram_bot_token: str
    
    class Config:
        env_file = ".env"
