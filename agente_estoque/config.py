"""Configuração via variáveis de ambiente (ou arquivo .env).

Nenhuma credencial fica no código. O provedor de LLM é a Gemini Developer API
(Google AI Studio), via langchain-google-genai: chave em GOOGLE_API_KEY e
modelo em GEMINI_MODEL.
"""

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM (Gemini Developer API / Google AI Studio) ---
    google_api_key: SecretStr | None = None  # GOOGLE_API_KEY
    gemini_model: str = "gemini-3.5-flash-lite"  # GEMINI_MODEL
    llm_timeout_s: float = 30.0

    # --- API de estoque (somente leitura) ---
    estoque_api_url: str = "http://127.0.0.1:8000"
    estoque_timeout_s: float = 5.0
    estoque_retries: int = 1  # novas tentativas só para falha de rede/timeout
    estoque_retry_backoff_s: float = 0.2

    # --- Entrada ---
    mensagem_max_chars: int = 500

    @field_validator("estoque_api_url")
    @classmethod
    def _sem_barra_final(cls, valor: str) -> str:
        return valor.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
