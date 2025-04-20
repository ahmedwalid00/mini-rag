from pydantic_settings import BaseSettings , SettingsConfigDict

class Settings(BaseSettings):

    APP_NAME : str
    APP_VERSION : str
    OPENAI_API_KEY : str
    FILE_MAX_SIZE : int
    FILE_ALLOWED_TYPE : list
    FILE_DEFAULT_CHUNK_SIZE : int
    MONGODB_URL : str
    MONGODB_DATABASE :str

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()