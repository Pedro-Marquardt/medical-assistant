from dependency_injector import containers, providers
from api.infra.database.chroma.connection import ChromaDatabase
from api.infra.services.mcp.client import MCPClient
from api.application.services.graph_service import GraphService
from api.application.graph.graph_manager import MedicalAssistantGraph
from api.infra.services.semantic_anchor.anchor import SemanticAnchor
from api.infra.config.env import ConfigEnvs
import os


class Container(containers.DeclarativeContainer):
    
    # Database providers
    chroma_database = providers.Singleton(
        ChromaDatabase
    )
    
    # MCP Client provider
    mcp_client = providers.Singleton(
        MCPClient,
        host=ConfigEnvs.MCP_API_HOST,
        port=8000  # Porta do MCP server
    )
    
    # Graph Service provider
    graph_service = providers.Singleton(
        GraphService,
        mcp_client=mcp_client,
        chroma_db=chroma_database
    )
    
    # Semantic Anchor provider
    semantic_anchor = providers.Singleton(
        SemanticAnchor
    )
    
    # Medical Assistant Graph provider
    medical_graph = providers.Singleton(
        MedicalAssistantGraph,
        mcp_client=mcp_client,
        chroma_db=chroma_database,
        semantic_anchor=semantic_anchor
    )