from dependency_injector import containers, providers
from api.infra.database.chroma.connection import ChromaDatabase
from api.infra.services.mcp.client import MCPClient
from api.application.services.graph_service import GraphService
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
        host=ConfigEnvs.MCP_API_HOST
    )
    
    # Graph Service provider
    graph_service = providers.Singleton(
        GraphService,
        mcp_client=mcp_client,
        chroma_db=chroma_database
    )