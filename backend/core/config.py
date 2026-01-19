from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hustler IA Smart Waiter"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    
    # Security
    ALLOWED_ORIGINS: list[str] = ["*"] # Allow all for mobile testing
    
    # RAG
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # External APIs
    GEMINI_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_AGENT_ID: str = ""

    # Context Settings
    DEFAULT_CITY: str = "Barcelona"
    AI_PERSONA_NAME: str = "Alexandra"
    
    class Config:
        env_file = "config/.env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
