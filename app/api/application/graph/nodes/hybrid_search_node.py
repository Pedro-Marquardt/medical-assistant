import asyncio
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.application.agents.mcp_agent import MCPAgent
from api.infra.database.chroma.connection import ChromaDatabase
from api.infra.utils.logger import log

class HybridSearchNode:
    """
    Nó responsável por executar busca híbrida paralela.
    Combina busca de pacientes via MCP Agent + busca de protocolos via ChromaDB.
    """
    
    def __init__(self, mcp_agent: MCPAgent, chroma_db: ChromaDatabase):
        self.mcp_agent = mcp_agent
        self.chroma_db = chroma_db
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa busca híbrida paralela.
        
        Args:
            state: Estado atual do grafo
            
        Returns:
            Dict: Estado atualizado com dados de pacientes e protocolos
        """
        try:
            query = state.get("query", "")
            user_id = state.get("user_id", "unknown")
            
            log.info(f"Iniciando busca híbrida paralela para user: {user_id}")
            
            # 🚀 EXECUÇÃO PARALELA
            patient_data, protocols = self._parallel_search(query)
            
            # Atualiza estado com ambos os resultados
            state.update({
                "patient_data": patient_data,
                "protocols": protocols,
                "hybrid_search_completed": True,
                "mcp_search_completed": patient_data is not None,
                "vector_search_completed": len(protocols) > 0
            })
            
            log.info(f"Busca híbrida concluída - Paciente: {patient_data is not None}, Protocolos: {len(protocols)}")
            
            return state
            
        except Exception as e:
            log.error(f"Erro na busca híbrida: {e}")
            
            # Fallback em caso de erro
            state.update({
                "patient_data": None,
                "protocols": [],
                "hybrid_search_completed": False,
                "search_error": str(e)
            })
            
            return state
    
    def _parallel_search(self, query: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Executa buscas MCP e ChromaDB em paralelo usando ThreadPoolExecutor.
        
        Args:
            query: Query do usuário
            
        Returns:
            Tuple: (dados_paciente, protocolos)
        """
        patient_data = None
        protocols = []
        
        # 🔥 EXECUÇÃO PARALELA COM ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            
            # Submete ambas as tarefas simultaneamente
            mcp_future = executor.submit(self._search_patient, query)
            vector_future = executor.submit(self._search_protocols, query)
            
            # Coleta resultados conforme completam
            for future in as_completed([mcp_future, vector_future], timeout=30):
                try:
                    if future == mcp_future:
                        patient_data = future.result()
                        log.info("✅ Busca MCP concluída")
                    elif future == vector_future:
                        protocols = future.result()
                        log.info("✅ Busca vetorial concluída")
                        
                except Exception as e:
                    if future == mcp_future:
                        log.error(f"Erro na busca MCP: {e}")
                    else:
                        log.error(f"Erro na busca vetorial: {e}")
        
        return patient_data, protocols
    
    def _search_patient(self, query: str) -> Dict[str, Any]:
        """
        Busca informações de paciente via MCP Agent.
        
        Args:
            query: Query do usuário
            
        Returns:
            Dict: Dados do paciente ou None se não encontrado
        """
        try:
            log.info("🔍 Iniciando busca de paciente via MCP Agent")
            
            # Usa o MCP Agent para buscar paciente
            result = self.mcp_agent.execute(query)
            
            if result and "erro" not in result.lower():
                return {
                    "found": True,
                    "data": result,
                    "source": "mcp_agent"
                }
            else:
                return None
                
        except Exception as e:
            log.error(f"Erro na busca de paciente: {e}")
            return None
    
    def _search_protocols(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca protocolos médicos via ChromaDB.
        
        Args:
            query: Query do usuário
            
        Returns:
            List: Lista de protocolos relevantes
        """
        try:
            log.info("📋 Iniciando busca de protocolos via ChromaDB")
            
            # Busca protocolos relevantes no ChromaDB
            results = self.chroma_db.search(
                query_text=query,
                limit=5,
                threshold=0.7
            )
            
            if results:
                protocols = []
                for result in results:
                    protocols.append({
                        "content": result.get("content", ""),
                        "metadata": result.get("metadata", {}),
                        "score": result.get("score", 0.0),
                        "source": result.get("source", ""),
                        "source": "chromadb"
                    })
                return protocols
            else:
                return []
                
        except Exception as e:
            log.error(f"Erro na busca de protocolos: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check do nó híbrido.
        
        Returns:
            Dict: Status dos componentes
        """
        try:
            mcp_status = self.mcp_agent.health_check()
            chroma_status = self.chroma_db.health_check() if hasattr(self.chroma_db, 'health_check') else {"status": "unknown"}
            
            return {
                "hybrid_search_node": "healthy",
                "mcp_agent": mcp_status.get("status", "unknown"),
                "chromadb": chroma_status.get("status", "unknown"),
                "parallel_execution": "enabled"
            }
            
        except Exception as e:
            return {
                "hybrid_search_node": "error",
                "error": str(e),
                "parallel_execution": "disabled"
            }

# Versão assíncrona alternativa (se preferir async/await)
class AsyncHybridSearchNode:
    """Versão assíncrona do HybridSearchNode."""
    
    def __init__(self, mcp_agent: MCPAgent, chroma_db: ChromaDatabase):
        self.mcp_agent = mcp_agent
        self.chroma_db = chroma_db
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executa busca híbrida assíncrona."""
        try:
            query = state.get("query", "")
            
            log.info("Iniciando busca híbrida assíncrona")
            
            # 🚀 EXECUÇÃO ASSÍNCRONA PARALELA
            patient_task = asyncio.create_task(self._async_search_patient(query))
            protocol_task = asyncio.create_task(self._async_search_protocols(query))
            
            # Aguarda ambas as tarefas
            patient_data, protocols = await asyncio.gather(
                patient_task, 
                protocol_task, 
                return_exceptions=True
            )
            
            # Trata exceções
            if isinstance(patient_data, Exception):
                log.error(f"Erro na busca MCP: {patient_data}")
                patient_data = None
                
            if isinstance(protocols, Exception):
                log.error(f"Erro na busca vetorial: {protocols}")
                protocols = []
            
            state.update({
                "patient_data": patient_data,
                "protocols": protocols,
                "hybrid_search_completed": True
            })
            
            return state
            
        except Exception as e:
            log.error(f"Erro na busca híbrida assíncrona: {e}")
            state.update({
                "patient_data": None,
                "protocols": [],
                "hybrid_search_completed": False,
                "search_error": str(e)
            })
            return state
    
    async def _async_search_patient(self, query: str) -> Dict[str, Any]:
        """Busca assíncrona de paciente."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_patient, query)
    
    async def _async_search_protocols(self, query: str) -> List[Dict[str, Any]]:
        """Busca assíncrona de protocolos."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_protocols, query)
    
    def _search_patient(self, query: str) -> Dict[str, Any]:
        """Método sincronizado para busca de paciente."""
        try:
            result = self.mcp_agent.execute(query)
            if result:
                return {"found": True, "data": result, "source": "mcp_agent"}
            return None
        except Exception:
            return None
    
    def _search_protocols(self, query: str) -> List[Dict[str, Any]]:
        """Método sincronizado para busca de protocolos."""
        try:
            results = self.chroma_db.search(query_text=query, limit=5)
            return [{"content": r.get("content", ""), "score": r.get("score", 0.0), "source": r.get("source", "")} for r in results]
        except Exception:
            return []