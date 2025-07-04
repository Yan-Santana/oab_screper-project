import os
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações do agente OAB"""
    
    # API do scraper
    SCRAPER_API_URL: str = os.getenv("SCRAPER_API_URL", "http://localhost:8000")
    
    # Configurações do LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # openai, ollama, mock
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Ollama
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Cloudflare Workers AI
    CF_ACCOUNT_ID: Optional[str] = os.getenv("CF_ACCOUNT_ID")
    CF_API_TOKEN: Optional[str] = os.getenv("CF_API_TOKEN")
    CF_MODEL: str = os.getenv("CF_MODEL", "@cf/meta/llama-2-7b-chat-int8")
    
    # Configurações gerais
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "120"))
    VERBOSE: bool = os.getenv("VERBOSE", "true").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validar configurações"""
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            print("Aviso: OPENAI_API_KEY não configurada. Usando mock LLM.")
            cls.LLM_PROVIDER = "mock"
        
        if cls.LLM_PROVIDER == "cloudflare" and (not cls.CF_ACCOUNT_ID or not cls.CF_API_TOKEN):
            print("Aviso: CF_ACCOUNT_ID ou CF_API_TOKEN não configurados. Usando mock LLM.")
            cls.LLM_PROVIDER = "mock"
        
        return True