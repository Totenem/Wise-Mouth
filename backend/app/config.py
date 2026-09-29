from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    assemblyai_api_key: str = ""
    assemblyai_ws_url: str = "wss://streaming.assemblyai.com/v3/ws"

    llm_provider: str = "groq"  # groq | gemini | none
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    llm_timeout_s: float = 3.5
    llm_cache_path: str = "data/llm_cache.json"

    database_url: str = ""  # empty -> local sqlite file
    cors_origins: str = "*"
    auth_secret: str = ""  # signs login tokens; empty -> random per process

    # Engine tuning
    min_signal_confidence: float = 0.6
    unanswered_after_utterances: int = 2
    unanswered_after_seconds: float = 25.0


settings = Settings()
