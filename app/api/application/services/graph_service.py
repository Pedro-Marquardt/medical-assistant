"""
Serviço para gerenciamento do grafo de assistência médica.
"""

from api.application.graph.graph_manager import MedicalAssistantGraph
from api.infra.services.mcp.client import MCPClient
from api.infra.database.chroma.connection import ChromaDatabase
from api.infra.utils.logger import log


class GraphService:
    """
    Serviço para interação com o grafo de assistência médica.
    """

    def __init__(self, mcp_client: MCPClient, chroma_db: ChromaDatabase):
        self.mcp_client = mcp_client
        self.chroma_db = chroma_db
        self.graph_manager = MedicalAssistantGraph(mcp_client, chroma_db)
        log.info("GraphService inicializado com sucesso")

    def process_medical_query(self, query: str, user_id: str = None) -> str:
        """
        Processa uma consulta médica através do grafo.
        
        Args:
            query (str): Consulta médica do usuário
            user_id (str): ID do usuário para contexto de sessão
            
        Returns:
            str: Resposta processada pelo grafo
        """
        try:
            thread_id = user_id or "default_session"
            log.info(f"Processando consulta médica para usuário: {thread_id}")
            
            response = self.graph_manager.process_query(query, thread_id)
            
            log.info("Consulta médica processada com sucesso")
            return response

        except Exception as e:
            log.error(f"Erro ao processar consulta médica: {e}")
            return f"❌ Erro ao processar sua consulta: {str(e)}"

    def get_available_tools(self) -> list:
        """
        Obtém lista de ferramentas disponíveis.
        
        Returns:
            list: Lista de ferramentas MCP disponíveis
        """
        try:
            return self.mcp_client.list_tools()
        except Exception as e:
            log.error(f"Erro ao listar ferramentas: {e}")
            return []

    def search_patient_directly(self, search_type: str, search_value: str) -> dict:
        """
        Busca paciente diretamente usando ferramentas MCP.
        
        Args:
            search_type (str): Tipo de busca ('cpf', 'name', 'rg', 'id')
            search_value (str): Valor a ser buscado
            
        Returns:
            dict: Informações do paciente encontrado
        """
        try:
            tool_mapping = {
                "cpf": "get_patient_by_cpf",
                "name": "get_patient_by_name",
                "rg": "get_patient_by_rg", 
                "id": "get_patient_by_id"
            }
            
            tool_name = tool_mapping.get(search_type)
            if not tool_name:
                raise ValueError(f"Tipo de busca não suportado: {search_type}")
            
            arg_mapping = {
                "cpf": {"cpf": search_value},
                "name": {"nome": search_value},
                "rg": {"rg": search_value},
                "id": {"id": search_value}
            }
            
            arguments = arg_mapping.get(search_type, {})
            result = self.mcp_client.call_tool(tool_name, arguments)
            
            log.info(f"Busca direta de paciente concluída - Tipo: {search_type}")
            return result

        except Exception as e:
            log.error(f"Erro na busca direta de paciente: {e}")
            return {"error": str(e)}

    def search_protocols(self, query: str, max_results: int = 5) -> list:
        """
        Busca protocolos médicos diretamente.
        
        Args:
            query (str): Consulta de busca
            max_results (int): Máximo de resultados
            
        Returns:
            list: Lista de protocolos encontrados
        """
        try:
            results = self.chroma_db.similarity_search(
                query_texts=[query],
                n_results=max_results
            )
            
            if results and "documents" in results:
                return results["documents"][0] if results["documents"] else []
            
            return []

        except Exception as e:
            log.error(f"Erro na busca de protocolos: {e}")
            return []

    def get_graph_info(self) -> dict:
        """
        Retorna informações sobre a estrutura do grafo.
        
        Returns:
            dict: Estrutura do grafo
        """
        return self.graph_manager.get_graph_structure()