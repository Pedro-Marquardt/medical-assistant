import asyncio
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.infra.services.mcp.client import MCPClient
from api.infra.database.chroma.connection import ChromaDatabase
from api.infra.utils.logger import log

class HybridSearchNode:
    """
    Nó responsável por executar busca híbrida paralela.
    Combina busca de pacientes via MCP Client + busca de protocolos via ChromaDB.
    """
    
    def __init__(self, mcp_client: MCPClient, chroma_db: ChromaDatabase):
        self.mcp_client = mcp_client
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
            
            # Fallback com estado seguro
            state.update({
                "patient_data": None,
                "protocols": [],
                "hybrid_search_completed": False,
                "hybrid_search_error": str(e)
            })
            
            return state
    
    def _parallel_search(self, query: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Executa busca paralela usando ThreadPoolExecutor.
        
        Args:
            query: Query do usuário
            
        Returns:
            Tuple: (dados_paciente, lista_protocolos)
        """
        patient_data = None
        protocols = []
        
        try:
            # 🚀 Execução paralela com ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="HybridSearch") as executor:
                # Submit both tasks
                future_patient = executor.submit(self._search_patient, query)
                future_protocols = executor.submit(self._search_protocols, query)
                
                # Process completed futures as they finish
                for future in as_completed([future_patient, future_protocols], timeout=30):
                    if future == future_patient:
                        log.info("✅ Busca MCP concluída")
                        patient_data = future.result()
                    elif future == future_protocols:
                        log.info("✅ Busca vetorial concluída")
                        protocols = future.result() or []
            
        except Exception as e:
            log.error(f"Erro na execução paralela: {e}")
            
        return patient_data, protocols
    
    def _search_patient(self, query: str) -> Dict[str, Any]:
        """
        Busca paciente via MCP Client.
        
        Args:
            query: Query do usuário
            
        Returns:
            Dict: Dados do paciente ou None se não encontrado
        """
        try:
            log.info("🔍 Iniciando busca de paciente via MCP Agent")
            
            # Log da query original
            log.info(f"🔹 Query para MCP: '{query}'")
            
            # Detecta tipo de busca baseado na query
            search_tool = self._detect_search_tool(query)
            
            if search_tool:
                # Extrai o valor de busca da query
                search_value = self._extract_search_value(query, search_tool)
                
                log.info(f"🔹 Tool: {search_tool}, Value: '{search_value}'")
                
                # Monta argumentos corretos baseados na ferramenta
                if search_tool == "get_patient_by_cpf":
                    arguments = {"cpf": search_value}
                elif search_tool == "get_patient_by_rg":
                    arguments = {"rg": search_value}
                elif search_tool == "get_patient_by_name":
                    arguments = {"nome": search_value}
                elif search_tool == "get_patient_by_id":
                    arguments = {"id": search_value}
                else:
                    arguments = {"query": search_value}
                
                log.info(f"🔹 Arguments: {arguments}")
                
                # Chama a ferramenta MCP adequada
                result = self.mcp_client.call_tool(search_tool, arguments)
                
                # Log do resultado MCP
                log.info(f"🔹 Resultado MCP: {result}")
                
                if result and not isinstance(result, str) or "erro" not in str(result).lower():
                    log.info("✅ Paciente encontrado via MCP")
                    return {
                        "found": True,
                        "data": result,
                        "source": "mcp_client"
                    }
            
            log.info("❌ Paciente não encontrado via MCP")
            return None
                
        except Exception as e:
            log.error(f"Erro na busca de paciente: {e}")
            return None
    
    def _detect_search_tool(self, query: str) -> str:
        """Detecta qual ferramenta MCP usar baseada na query."""
        query_lower = query.lower()
        
        if "cpf" in query_lower:
            return "get_patient_by_cpf"
        elif "rg" in query_lower:
            return "get_patient_by_rg"
        elif any(char.isalpha() for char in query):
            return "get_patient_by_name"
        elif query.strip().isdigit():
            return "get_patient_by_id"
        
        # Default para busca por nome
        return "get_patient_by_name"
    
    def _extract_search_value(self, query: str, search_tool: str) -> str:
        """Extrai o valor de busca da query baseado no tipo de ferramenta."""
        import re
        
        if search_tool == "get_patient_by_cpf":
            # Extrai CPF da query
            cpf_match = re.search(r'\b\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2}\b', query)
            if cpf_match:
                return cpf_match.group()
        
        elif search_tool == "get_patient_by_rg":
            # Extrai RG da query
            rg_match = re.search(r'\b[A-Z]{2}[-\.]?\d{2}\.?\d{3}\.?\d{3}\b|\b\d{2}\.?\d{3}\.?\d{3}[-\.]?[A-Z]{1,2}\b', query)
            if rg_match:
                return rg_match.group()
        
        elif search_tool == "get_patient_by_name":
            # Extrai nome da query
            name_match = re.search(r'\bpaciente\s+([A-Z][a-zçãõáéíóúâêîôûàèìòù]+(?:\s+[A-Z][a-zçãõáéíóúâêîôûàèìòù]+)*)', query, re.IGNORECASE)
            if name_match:
                return name_match.group(1)
        
        # Fallback: retorna a query original
        return query

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
            
            # Log da query
            log.info(f"🔹 Query para ChromaDB: '{query}'")
            
            # Usa o retriever do ChromaDB
            retriever = self.chroma_db.get_retriever(k=5)
            results = retriever.invoke(query)
            
            # Log dos resultados
            log.info(f"🔹 Resultados ChromaDB: {len(results)} documentos encontrados")
            
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
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do nó híbrido."""
        try:
            # Testa conectividade MCP
            mcp_tools = self.mcp_client.list_tools()
            
            # Testa conectividade ChromaDB
            chroma_client = self.chroma_db.get_client()
            
            return {
                "status": "healthy",
                "mcp_connection": "active",
                "mcp_tools_available": len(mcp_tools),
                "chroma_connection": "active",
                "vector_store": "ready"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "mcp_connection": "failed",
                "chroma_connection": "failed"
            }