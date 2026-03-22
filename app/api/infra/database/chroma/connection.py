import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from api.infra.config.env import ConfigEnvs
from api.application.database.chroma.connection_interface import ChromaDatabaseInterface

class ChromaDatabase(ChromaDatabaseInterface):
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=ConfigEnvs.HOST_CHROMA_DB, 
            port=ConfigEnvs.CHROMA_PORT
        )
        
        # Usar host.docker.internal para acessar Ollama do container
        ollama_host = "http://host.docker.internal:11434" if ConfigEnvs.HOST_OLLAMA == "http://localhost:11434" else ConfigEnvs.HOST_OLLAMA
        
        self.embeddings = OllamaEmbeddings(
            model=ConfigEnvs.EMBEDDING_MODEL,
            base_url=ollama_host
        )
        
        self.vector_store = Chroma(
            client=self.client,
            collection_name=ConfigEnvs.CHROMA_COLLECTION,
            embedding_function=self.embeddings
        )

    def get_client(self):
        return self.client

    def get_vector_store(self):
        return self.vector_store

    def get_retriever(self, k: int = 3):

        return self.vector_store.as_retriever(search_kwargs={"k": k})