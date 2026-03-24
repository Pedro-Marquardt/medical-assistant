from abc import ABC, abstractmethod
from typing import Optional


class SemanticAnchorInterface(ABC):
    """
    Interface para roteador semântico.
    Define o contrato para implementações que decidem entre busca MCP e busca vetorial.
    """
    
    @abstractmethod
    def __init__(self, host: Optional[str] = None) -> None:
        """
        Inicializa o roteador semântico.
        
        Args:
            host: Host do serviço de embeddings (opcional)
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Inicializa as âncoras e modelo de embeddings.
        Deve ser chamado antes de usar o método route().
        
        Returns:
            bool: True se inicialização foi bem-sucedida, False caso contrário
        """
        pass
    
    @abstractmethod
    def route(self, query: str, threshold: float = 0.6) -> str:
        """
        Determina o tipo de busca baseado na análise semântica da query.
        
        Args:
            query: Consulta do usuário a ser analisada
            threshold: Limiar de similaridade para decisão (padrão: 0.6)
            
        Returns:
            str: Tipo de busca a ser executada ('hybrid_search' ou 'vector_search')
        """
        pass