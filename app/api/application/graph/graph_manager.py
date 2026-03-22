from typing import Dict, Any
from langgraph.graph import StateGraph, END
from dependency_injector.wiring import inject, Provide

from api.infra.services.mcp.client import MCPClient
from api.infra.database.chroma.connection import ChromaDatabase
from api.infra.services.semantic_anchor.anchor import SemanticAnchor

from .nodes.semantic_router import SemanticRouterNode
from .nodes.vector_search_node import VectorSearchNode
from .nodes.hybrid_search_node import HybridSearchNode
from .nodes.response_search_node import ResponseSearchNode
from .nodes.response_hybrid_node import ResponseHybridNode

class MedicalAssistantGraph:
    """
    Grafo principal do assistente médico.
    Coordena o fluxo de processamento das consultas médicas.
    """
    
    @inject
    def __init__(
        self,
        mcp_client: MCPClient,
        chroma_db: ChromaDatabase,
        semantic_anchor: SemanticAnchor
    ):
        self.mcp_client = mcp_client
        self.chroma_db = chroma_db
        self.semantic_anchor = semantic_anchor
        
        # Inicializa nós
        self.semantic_router = SemanticRouterNode(semantic_anchor)
        self.vector_search = VectorSearchNode(chroma_db)
        self.hybrid_search = HybridSearchNode(mcp_client, chroma_db)
        self.response_search = ResponseSearchNode()
        self.response_hybrid = ResponseHybridNode()
        
        # Constrói o grafo
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de estados."""
        
        # Define o grafo
        workflow = StateGraph(dict)
        
        # Adiciona nós
        workflow.add_node("semantic_routing", self.semantic_router.execute)
        workflow.add_node("vector_search", self.vector_search.execute)
        workflow.add_node("hybrid_search", self.hybrid_search.execute)
        workflow.add_node("response_search", self.response_search.execute)
        workflow.add_node("response_hybrid", self.response_hybrid.execute)
        
        # Define ponto de entrada
        workflow.set_entry_point("semantic_routing")
        
        # Define fluxos condicionais
        workflow.add_conditional_edges(
            "semantic_routing",
            self._route_after_semantic,
            {
                "hybrid_search": "hybrid_search",
                "vector_search": "vector_search"
            }
        )
        
        # Fluxos após busca
        workflow.add_edge("hybrid_search", "response_hybrid")
        workflow.add_edge("vector_search", "response_search")
        
        # Fluxos finais
        workflow.add_edge("response_hybrid", END)
        workflow.add_edge("response_search", END)
        
        return workflow.compile()
    
    def _route_after_semantic(self, state: Dict[str, Any]) -> str:
        """Decide o próximo nó após roteamento semântico."""
        search_type = state.get("search_type", "vector_search")
        
        if search_type == "hybrid_search":
            return "hybrid_search"  # Vai para hybrid search
        else:
            return "vector_search"  # Vai para vector search
    
    def process_query_stream(self, query: str, user_id: str = "anonymous"):
        """
        Processa uma consulta médica através do grafo com streaming.
        
        Args:
            query: Consulta do usuário
            user_id: ID do usuário
            
        Yields:
            str: Chunks da resposta em streaming
        """
        try:
            # Estado inicial
            initial_state = {
                "query": query,
                "user_id": user_id,
                "search_type": None,
                "patient_data": None,
                "protocols": [],
                "response_stream": None,
                "response_generated": False
            }
            
            # Executa o grafo
            result = self.graph.invoke(initial_state)
            
            response_stream = result.get("response_stream")
            
            if response_stream:
                for chunk in response_stream:
                    yield chunk
            else:
                yield "Erro: Resposta em streaming não disponível"
                
        except Exception as e:
            # Stream de erro em caso de falha
            yield from self._generate_error_stream(str(e))
    
    def process_query(self, query: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Processa uma consulta médica através do grafo.
        
        Args:
            query: Consulta do usuário
            user_id: ID do usuário
            
        Returns:
            Dict: Resposta processada com streaming
        """
        try:
            # Estado inicial
            initial_state = {
                "query": query,
                "user_id": user_id,
                "search_type": None,
                "patient_data": None,
                "protocols": [],
                "response_stream": None,
                "response_generated": False
            }
            
            # Executa o grafo
            result = self.graph.invoke(initial_state)
            
            return {
                "response_stream": result.get("response_stream"),
                "response_type": result.get("response_type"),
                "search_type": result.get("search_type"),
                "success": result.get("response_generated", False),
                "protocols_used": result.get("protocols_used", 0),
                "has_patient_context": result.get("has_patient_context", False)
            }
            
        except Exception as e:
            return {
                "response_stream": self._generate_error_stream(str(e)),
                "response_type": "error",
                "search_type": "error",
                "success": False
            }
    
    def _generate_error_stream(self, error_msg: str):
        """Gera stream de erro para casos de falha do grafo."""
        
        error_parts = [
            "**⚠️ Erro no sistema médico**\n\n",
            f"Ocorreu um erro durante o processamento: {error_msg}\n\n",
            "**Recomendação:**\n",
            "- Procure atendimento médico presencial\n",
            "- Em emergências, dirija-se ao pronto-socorro\n\n",
            "**Importante:**\n",
            "Este sistema não substitui avaliação médica profissional."
        ]
        
        for part in error_parts:
            yield part