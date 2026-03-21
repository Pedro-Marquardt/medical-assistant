from abc import ABC, abstractmethod
from typing import Any


class ChromaDatabaseInterface(ABC):
    """Interface para operações de banco de dados ChromaDB."""
    
    @abstractmethod
    def get_client(self) -> Any:
        """Retorna o cliente ChromaDB.
        
        Returns:
            Any: Cliente ChromaDB configurado
        """
        pass
    
    @abstractmethod
    def get_vector_store(self) -> Any:
        """Retorna o vector store configurado.
        
        Returns:
            Any: Vector store do Chroma
        """
        pass
    
    @abstractmethod
    def get_retriever(self, k: int = 3) -> Any:
        """Retorna um retriever configurado para busca.
        
        Args:
            k (int, optional): Número de documentos a retornar. Defaults to 3.
            
        Returns:
            Any: Retriever configurado
        """
        pass
