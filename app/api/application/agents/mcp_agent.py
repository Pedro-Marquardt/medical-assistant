"""
Agente MCP simplificado para interação com ferramentas do servidor MCP.
Utiliza o MCPClient para executar ferramentas de busca de pacientes.
"""

from typing import Any, Dict, List, Optional, Union
from api.infra.services.mcp.client import MCPClient
from api.infra.utils.logger import log

class MCPAgent:
    """
    Agente simplificado para interação com MCP Server.
    Gerencia a execução de ferramentas disponíveis no servidor MCP.
    """
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.available_tools = []
        self._load_tools()
    
    def _load_tools(self):
        """Carrega as ferramentas disponíveis do servidor MCP."""
        try:
            self.available_tools = self.mcp_client.list_tools()
            log.info(f"MCP Agent carregado com {len(self.available_tools)} ferramentas")
        except Exception as e:
            log.error(f"Erro ao carregar ferramentas MCP: {e}")
            self.available_tools = []
    
    def search_patient(self, query: str, search_type: str = "auto") -> Dict[str, Any]:
        """
        Busca paciente usando as ferramentas MCP disponíveis.
        
        Args:
            query: Query de busca do paciente
            search_type: Tipo de busca (auto, cpf, rg, name, id)
            
        Returns:
            Dict: Dados do paciente encontrado
        """
        try:
            # Determine qual ferramenta usar baseado na query ou tipo
            tool_name = self._select_search_tool(query, search_type)
            
            if not tool_name:
                return {
                    "found": False,
                    "error": "Nenhuma ferramenta adequada encontrada",
                    "query": query
                }
            
            # Execute a busca
            result = self._execute_tool(tool_name, {"query": query})
            
            return {
                "found": True,
                "data": result,
                "tool_used": tool_name,
                "query": query
            }
            
        except Exception as e:
            log.error(f"Erro na busca de paciente: {e}")
            return {
                "found": False,
                "error": str(e),
                "query": query
            }
    
    def _select_search_tool(self, query: str, search_type: str) -> Optional[str]:
        """Seleciona a ferramenta adequada baseada na query e tipo."""
        
        # Mapeamento de tipos para ferramentas
        tool_mapping = {
            "cpf": "patient_by_cpf",
            "rg": "patient_by_rg", 
            "name": "patient_by_name",
            "id": "patient_by_id"
        }
        
        # Se tipo específico foi fornecido
        if search_type != "auto" and search_type in tool_mapping:
            return tool_mapping[search_type]
        
        # Auto-detecção baseada na query
        query_lower = query.lower()
        
        if "cpf" in query_lower or len(query.replace(".", "").replace("-", "").replace(" ", "")) == 11:
            return "get_patient_by_cpf"
        elif "rg" in query_lower:
            return "get_patient_by_rg"
        elif any(char.isalpha() for char in query):
            return "get_patient_by_name"
        elif query.isdigit():
            return "get_patient_by_id"
        
        # Default para busca por nome
        return "get_patient_by_name"
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Executa uma ferramenta específica do MCP."""
        try:
            result = self.mcp_client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            log.error(f"Erro ao executar ferramenta {tool_name}: {e}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Retorna lista de ferramentas disponíveis."""
        return self.available_tools
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente MCP."""
        try:
            tools_count = len(self.available_tools)
            test_result = self.mcp_client.list_tools()  # Teste de conectividade
            
            return {
                "status": "healthy",
                "tools_available": tools_count,
                "mcp_connection": "active"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "tools_available": 0,
                "mcp_connection": "failed"
            }