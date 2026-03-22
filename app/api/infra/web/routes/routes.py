from fastapi import APIRouter, Depends
from typing import Annotated
from dependency_injector.wiring import Provide, inject

from api.infra.container.dependecies import Container
from api.application.database.chroma.connection_interface import ChromaDatabaseInterface
from api.application.services.mcp.client import MCPClientInterface

router = APIRouter()

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
