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
            log.info("📋 Iniciando busca de protocolos via ChromaDB")
            
            # Log da query
            log.info(f"🔹 Query para ChromaDB: '{query}'")
            
            # Usa o retriever do ChromaDB
            retriever = self.chroma_db.get_retriever(k=3)
            results = retriever.invoke(query)
            
            # Log dos resultados
            log.info(f"Resultados ChromaDB: {len(results)} documentos encontrados")
            
            if results:
                protocols = []
                for i, doc in enumerate(results):
                    protocols.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": "chromadb",
                        "rank": i + 1
                    })
                    log.info(f"  📄 Doc {i+1}: {doc.metadata.get('source', 'N/A')} - {doc.page_content[:100]}...")
                
                return protocols
            else:
                log.info("❌ Nenhum protocolo encontrado no ChromaDB")
                return []
                
        except Exception as e:
            log.error(f"Erro na busca de protocolos: {e}")
            return []