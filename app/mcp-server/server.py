"""
Servidor MCP para gerenciamento de dados de pacientes médicos.
Implementa HTTP simples usando o protocolo MCP, similar ao StreamableHTTPServerTransport do Node.js.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from mcp.server import Server
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

# Cria a aplicação FastAPI
app = FastAPI(
    title="Medical Patient MCP Server",
    description="Servidor MCP para gerenciamento de dados de pacientes médicos",
    version="1.0.0"
)

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Endpoint MCP principal - similar ao Node.js StreamableHTTPServerTransport."""
    try:
        # Obtém o payload JSON-RPC
        payload = await request.json()
        
        # Cria uma nova instância do servidor para cada request (sem estado)
        request_server = Server("medical-patient-server")
        
        # Registra as ferramentas dinamicamente
        @request_server.list_tools()
        async def list_tools() -> List[Tool]:
            tools = [
                get_patient_by_name_tool(),
                get_patient_by_cpf_tool(),
                get_patient_by_rg_tool(),
                get_patient_by_id_tool()
            ]
            return tools
        
        @request_server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            return await handle_tool_call(name, arguments)
        
        # Processa a requisição JSON-RPC
        method = payload.get("method")
        params = payload.get("params", {})
        request_id = payload.get("id", 1)
        
        if method == "tools/list":
            tools = await list_tools()
            tools_dict = []
            for tool in tools:
                tools_dict.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_dict}
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "Tool name is required"}
                }
            
            result = await handle_tool_call(tool_name, arguments)
            
            # Converte TextContent para formato esperado
            content = []
            for text_content in result:
                content.append({
                    "type": text_content.type,
                    "text": text_content.text
                })
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": content}
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            }
            
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": payload.get("id", 1) if 'payload' in locals() else 1,
            "error": {"code": -32603, "message": str(e)}
        }

async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
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


@app.get("/")
async def root():
    """Endpoint raiz com informações do servidor."""
    return {
        "name": "Medical Patient MCP Server",
        "version": "1.0.0",
        "description": "Servidor MCP para gerenciamento de dados de pacientes médicos",
        "endpoints": {
            "mcp": "/mcp - POST endpoint para requisições MCP (JSON-RPC)",
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
    logger.info("  - POST /mcp: Endpoint principal MCP (JSON-RPC)")
    logger.info("  - GET /tools: Lista ferramentas disponíveis")
    logger.info("  - GET /health: Verificação de saúde")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()