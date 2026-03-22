from typing import Dict, Any, List
from api.infra.database.chroma.connection import ChromaDatabase
from api.infra.utils.logger import log

class VectorSearchNode:
    """Nó responsável por buscar protocolos médicos via ChromaDB."""
    
    def __init__(self, chroma_db: ChromaDatabase):
        self.chroma_db = chroma_db
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executa busca vetorial de protocolos."""
        try:
            query = state.get("query", "")
            
            log.info("Iniciando busca vetorial de protocolos")
            
            # Busca protocolos relevantes
            protocols = self._search_protocols(query)
            
            state.update({
                "protocols": protocols,
                "vector_search_completed": True
            })
            
            return state
            
        except Exception as e:
            log.error(f"Erro na busca vetorial: {e}")
            state.update({
                "protocols": [],
                "vector_search_completed": False,
                "vector_error": str(e)
            })
            return state
    
    def _search_protocols(self, query: str) -> List[Dict[str, Any]]:
        """Busca protocolos relevantes."""
        try:
            # Implementa busca no ChromaDB
            results = self.chroma_db.search(query, limit=5)
            return results
        except Exception:
            return []