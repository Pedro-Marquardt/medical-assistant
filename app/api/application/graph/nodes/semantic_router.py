from typing import Dict, Any
from api.infra.utils.logger import log
from api.infra.services.semantic_anchor.anchor import SemanticAnchor

class SemanticRouterNode:
    """
    Nó do grafo responsável pelo roteamento semântico.
    Decide se a query precisa buscar no MCP (hybrid_search) ou apenas protocolos (vector_search).
    """
    
    def __init__(self, semantic_anchor: SemanticAnchor):
        self.semantic_anchor = semantic_anchor
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa o roteamento semântico da query.
        
        Args:
            state: Estado atual do grafo contendo a query
            
        Returns:
            Dict: Estado atualizado com informações de roteamento
        """
        try:
            query = state.get("query", "")
            user_id = state.get("user_id", "unknown")
            
            log.info(f"Iniciando roteamento semântico para user: {user_id}")
            
            # Executa roteamento semântico
            search_type = self.semantic_anchor.route(query, threshold=0.6)  # Threshold ajustado para melhor precisão
            
            # Atualiza estado
            state.update({
                "search_type": search_type,
                "needs_mcp": search_type == "hybrid_search",
                "needs_vector_search": True,  # Sempre busca protocolos
                "routing_completed": True
            })
            
            log.info(f"Roteamento concluído - Tipo: {search_type}, MCP: {search_type == 'hybrid_search'}")
            
            return state
            
        except Exception as e:
            log.error(f"Erro no roteamento semântico: {e}")
            
            # Fallback para vector_search em caso de erro
            state.update({
                "search_type": "vector_search",
                "needs_mcp": False,
                "needs_vector_search": True,
                "routing_completed": True,
                "routing_error": str(e)
            })
            
            return state