import os
from dotenv import load_dotenv

load_dotenv()


class ConfigEnvs:
    """Configurações de ambiente para a aplicação."""
    
    # ChromaDB Configuration
    HOST_CHROMA_DB = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "hospital_protocols")
    
    # Ollama Configuration
    HOST_OLLAMA = os.getenv("HOST_OLLAMA", "localhost")
    
    # MCP Configuration
    MCP_API_HOST = os.getenv("MCP_HOST", "localhost")
    MCP_API_PORT = int(os.getenv("MCP_PORT", "8080"))
    
    # Embeddings Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


