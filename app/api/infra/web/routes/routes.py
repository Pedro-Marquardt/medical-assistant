from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Annotated
from dependency_injector.wiring import Provide, inject

from api.infra.container.dependecies import Container
from api.application.database.chroma.connection_interface import ChromaDatabaseInterface
from api.application.services.mcp.client import MCPClientInterface
from api.application.graph.graph_manager import MedicalAssistantGraph

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    user_id: str = "anonymous"

@router.get("/")
def read_root():
    return {"message": "API is running!"}

@router.get("/health/chroma")
@inject
async def check_chroma_health(
    chroma_db: Annotated[
        ChromaDatabaseInterface, 
        Depends(Provide[Container.chroma_database])
    ],
):
    try:
        client = chroma_db.get_client()
        collections = client.list_collections()
        return {
            "status": "healthy",
            "message": "ChromaDB connection successful",
            "collections_count": len(collections)
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "message": f"ChromaDB connection failed: {str(e)}"
        }
    


@router.get("/health/mcp")
@inject
async def check_mcp_health(
    mcp_client: Annotated[
        MCPClientInterface, 
        Depends(Provide[Container.mcp_client])
    ],
):
    try:
        tools = mcp_client.list_tools()
        return {
            "status": "healthy",
            "message": "MCP server connection successful",
            "tools_count": [tool.get("name", "unknown") for tool in tools]
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "message": f"MCP server connection failed: {str(e)}"
        }

@router.post("/medical/query")
@inject
async def medical_query_stream(
    request: QueryRequest,
    graph: Annotated[
        MedicalAssistantGraph, 
        Depends(Provide[Container.medical_graph])
    ],
):
    """
    Endpoint para consultas médicas com resposta em streaming.
    
    Args:
        request: Query e user_id do usuário
        graph: Instância do grafo médico
        
    Returns:
        StreamingResponse: Resposta em streaming
    """
    try:
        def generate_response():
            """Generator para streaming da resposta."""
            for chunk in graph.process_query_stream(request.query, request.user_id):
                # Formato Server-Sent Events
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except Exception as e:
        def error_stream():
            yield f"data: Erro no processamento: {str(e)}\n\n"
            yield f"data: Procure atendimento médico presencial\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/plain; charset=utf-8"
        )

@router.post("/medical/query/complete")
@inject
async def medical_query_complete(
    request: QueryRequest,
    graph: Annotated[
        MedicalAssistantGraph, 
        Depends(Provide[Container.medical_graph])
    ],
):
    """
    Endpoint para consultas médicas com resposta completa (sem streaming).
    
    Args:
        request: Query e user_id do usuário
        graph: Instância do grafo médico
        
    Returns:
        Dict: Resposta completa com metadados
    """
    try:
        result = graph.process_query(request.query, request.user_id)
        
        # Coleta toda a resposta do stream para retorno completo
        if result.get("response_stream"):
            full_response = "".join(list(result["response_stream"]))
            result["full_response"] = full_response
            del result["response_stream"]  # Remove o generator
        
        return {
            "success": result.get("success", False),
            "response": result.get("full_response", "Resposta não disponível"),
            "metadata": {
                "response_type": result.get("response_type"),
                "search_type": result.get("search_type"),
                "protocols_used": result.get("protocols_used", 0),
                "has_patient_context": result.get("has_patient_context", False)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": f"Erro no processamento: {str(e)}. Procure atendimento médico presencial.",
            "metadata": {
                "response_type": "error",
                "search_type": "error",
                "protocols_used": 0,
                "has_patient_context": False
            }
        }
