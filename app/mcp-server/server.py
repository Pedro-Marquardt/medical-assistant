"""
Servidor MCP para gerenciamento de dados de pacientes médicos.
Implementa Server-Sent Events (SSE) via HTTP usando o protocolo MCP.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    Tool,
    TextContent,
)

# Importa as tools de busca de pacientes
from tools.patient_by_name import (
    get_patient_by_name_tool, 
    execute_get_patient_by_name, 
    format_patient_response as format_name_response
)
from tools.patient_by_cpf import (
    get_patient_by_cpf_tool, 
    execute_get_patient_by_cpf, 
    format_patient_response as format_cpf_response
)
from tools.patient_by_rg import (
    get_patient_by_rg_tool, 
    execute_get_patient_by_rg, 
    format_patient_response as format_rg_response
)
from tools.patient_by_id import (
    get_patient_by_id_tool, 
    execute_get_patient_by_id, 
    format_patient_response as format_id_response
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Cria o servidor MCP
server = Server("medical-patient-server")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Lista todas as ferramentas disponíveis."""
    tools = [
        get_patient_by_name_tool(),
        get_patient_by_cpf_tool(),
        get_patient_by_rg_tool(),
        get_patient_by_id_tool()
    ]
    logger.info(f"Listando {len(tools)} ferramentas disponíveis")
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Executa uma ferramenta específica."""
    try:
        logger.info(f"Executando ferramenta: {name} com argumentos: {arguments}")
        
        if name == "get_patient_by_name":
            nome = arguments.get("nome")
            if not nome:
                raise ValueError("Argumento 'nome' é obrigatório")
            
            patients = execute_get_patient_by_name(nome)
            response = format_name_response(patients)
            
        elif name == "get_patient_by_cpf":
            cpf = arguments.get("cpf")
            if not cpf:
                raise ValueError("Argumento 'cpf' é obrigatório")
            
            patient = execute_get_patient_by_cpf(cpf)
            response = format_cpf_response(patient, cpf)
            
        elif name == "get_patient_by_rg":
            rg = arguments.get("rg")
            if not rg:
                raise ValueError("Argumento 'rg' é obrigatório")
            
            patient = execute_get_patient_by_rg(rg)
            response = format_rg_response(patient, rg)
            
        elif name == "get_patient_by_id":
            patient_id = arguments.get("id")
            if not patient_id:
                raise ValueError("Argumento 'id' é obrigatório")
            
            patient = execute_get_patient_by_id(patient_id)
            response = format_id_response(patient, patient_id)
            
        else:
            raise ValueError(f"Ferramenta '{name}' não encontrada")
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        error_message = f"Erro ao executar ferramenta '{name}': {str(e)}"
        logger.error(error_message)
        return [TextContent(type="text", text=f"❌ {error_message}")]


# Cria a aplicação FastAPI
app = FastAPI(
    title="Medical Patient MCP Server",
    description="Servidor MCP para gerenciamento de dados de pacientes médicos",
    version="1.0.0"
)

# Inicializa o transporte SSE definindo a rota onde as MENSAGENS serão recebidas
sse = SseServerTransport("/messages")

async def handle_sse(request: Request):
    """Endpoint GET para estabelecer a conexão Server-Sent Events."""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        # Conecta os streams do transporte ao servidor MCP
        await server.run(streams[0], streams[1], server.create_initialization_options())

async def handle_messages(request: Request):
    """Endpoint POST para receber as mensagens/chamadas de tools."""
    await sse.handle_post_message(request.scope, request.receive, request._send)


# Registra as rotas no FastAPI (usando add_route para acessar o ASGI cru, que o MCP exige)
app.add_route("/sse", handle_sse, methods=["GET"])
app.add_route("/messages", handle_messages, methods=["POST"])


@app.get("/")
async def root():
    """Endpoint raiz com informações do servidor."""
    return {
        "name": "Medical Patient MCP Server",
        "version": "1.0.0",
        "description": "Servidor MCP para gerenciamento de dados de pacientes médicos",
        "endpoints": {
            "sse": "/sse - GET endpoint para estabelecer conexão SSE",
            "messages": "/messages - POST endpoint para enviar mensagens",
            "tools": "/tools - GET endpoint para listar ferramentas detalhadas",
            "health": "/health - Endpoint de saúde do servidor"
        },
        "tools": [
            "get_patient_by_name",
            "get_patient_by_cpf", 
            "get_patient_by_rg",
            "get_patient_by_id"
        ]
    }


@app.get("/tools")
async def get_tools():
    """Endpoint para obter detalhes completos das ferramentas."""
    tools = [
        get_patient_by_name_tool(),
        get_patient_by_cpf_tool(),
        get_patient_by_rg_tool(),
        get_patient_by_id_tool()
    ]
    
    # Converte Tool objects para dicionários
    tools_dict = []
    for tool in tools:
        tools_dict.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        })
    
    return {"tools": tools_dict}


@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde."""
    return {"status": "healthy"}


def main():
    """Função principal para executar o servidor."""
    logger.info("Iniciando servidor MCP para gerenciamento de pacientes médicos")
    logger.info("Ferramentas disponíveis:")
    logger.info("  - get_patient_by_name: Busca paciente por nome")
    logger.info("  - get_patient_by_cpf: Busca paciente por CPF")
    logger.info("  - get_patient_by_rg: Busca paciente por RG")
    logger.info("  - get_patient_by_id: Busca paciente por ID")
    logger.info("Endpoints disponíveis:")
    logger.info("  - GET /sse: Estabelece conexão SSE")
    logger.info("  - POST /messages: Recebe mensagens MCP")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()