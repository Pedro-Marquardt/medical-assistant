"""
Agente MCP inteligente que usa LangChain para seleção automática de ferramentas.
A LLM analisa a query e seleciona automaticamente as ferramentas MCP adequadas.
"""

import json
from typing import Any, Dict, List, Optional, Union
from langchain_ollama import ChatOllama
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from pydantic import create_model, Field
from api.infra.services.mcp.client import MCPClient
from api.infra.config.env import ConfigEnvs
from api.infra.utils.logger import log

class MCPAgent:
    """
    Agente inteligente para interação com MCP Server usando LangChain.
    A LLM automaticamente seleciona e executa as ferramentas adequadas baseada na query.
    """
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.available_tools = []
        self.langchain_tools = []
        self.llm = ChatOllama(
            model=ConfigEnvs.LLM_MODEL or "llama3.1",
            base_url=ConfigEnvs.HOST_OLLAMA,
            temperature=0.1
        )
        self._load_tools()
        self._convert_tools_to_langchain()
    
    def _load_tools(self):
        """Carrega as ferramentas disponíveis do servidor MCP."""
        try:
            self.available_tools = self.mcp_client.list_tools()
            log.info(f"🛠️ MCP Agent carregado com {len(self.available_tools)} ferramentas")
        except Exception as e:
            log.error(f"Erro ao carregar ferramentas MCP: {e}")
            self.available_tools = []
    
    def _convert_tools_to_langchain(self):
        """Converte ferramentas MCP para formato LangChain StructuredTool."""
        self.langchain_tools = []
        
        for mcp_tool in self.available_tools:
            try:
                langchain_tool = self._convert_mcp_tool_to_langchain(mcp_tool)
                self.langchain_tools.append(langchain_tool)
                log.info(f"✅ Ferramenta convertida: {mcp_tool.get('name')}")
            except Exception as e:
                log.warning(f"Erro ao converter ferramenta {mcp_tool.get('name')}: {e}")
        
        log.info(f"🔧 {len(self.langchain_tools)} ferramentas LangChain prontas")
    
    def _convert_mcp_tool_to_langchain(self, mcp_tool: Dict[str, Any]) -> StructuredTool:
        """Converte uma ferramenta MCP para LangChain StructuredTool."""
        name = mcp_tool.get("name", "")
        description = mcp_tool.get("description", "")
        input_schema = mcp_tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # Função que será chamada pela LLM
        def call_mcp_tool(**kwargs):
            log.info(f"🚀 LLM chamando ferramenta '{name}' com args: {kwargs}")
            result = self.mcp_client.call_tool(name, kwargs)
            log.info(f"📤 Resultado de '{name}': {result}")
            return result
        
        # Cria campos Pydantic baseados no schema MCP
        fields = {}
        for prop_name, prop_schema in properties.items():
            prop_type = str  # default
            
            if prop_schema.get("type") == "integer":
                prop_type = int
            elif prop_schema.get("type") == "number":
                prop_type = float
            elif prop_schema.get("type") == "boolean":
                prop_type = bool
            
            field_default = ... if prop_name in required else None
            field_description = prop_schema.get("description", "")
            
            fields[prop_name] = (
                prop_type,
                Field(description=field_description, default=field_default)
            )
        
        # Cria modelo Pydantic dinâmico
        ToolInput = create_model(f"{name}Input", **fields)
        
        # Cria StructuredTool
        return StructuredTool.from_function(
            func=call_mcp_tool,
            name=name,
            description=description,
            args_schema=ToolInput
        )
    
    def _build_system_prompt(self) -> str:
        """Cria prompt do sistema para o agente."""
        return """
Você é um assistente médico especializado em busca de pacientes.

INSTRUÇÕES CRÍTICAS:
- SEMPRE use as ferramentas disponíveis para buscar informações de pacientes
- NUNCA responda com informações inventadas
- Analise a query do usuário e identifique o tipo de busca necessária
- Execute a ferramenta mais apropriada baseada nos dados fornecidos

TIPOS DE BUSCA DISPONÍVEIS:
- Por nome: quando mencionado "paciente [Nome]"
- Por CPF: quando mencionado número de CPF
- Por RG: quando mencionado número de RG
- Por ID: quando mencionado ID/PAC-XXX

FLUXO OBRIGATÓRIO:
1. Analise a query do usuário
2. Identifique qual ferramenta usar
3. Execute a ferramenta com os parâmetros corretos
4. Retorne os resultados encontrados

Se nenhum paciente for encontrado, informe claramente que não foram encontrados dados.
"""
    
    def search_patient(self, query: str, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Busca paciente usando seleção automática de ferramentas pela LLM.
        
        Args:
            query: Query de busca do paciente
            max_iterations: Máximo de iterações
            
        Returns:
            Dict: Dados do paciente encontrado
        """
        try:
            if not self.langchain_tools:
                return {
                    "found": False,
                    "error": "Nenhuma ferramenta disponível",
                    "query": query
                }
            
            log.info(f"🤖 MCP Agent iniciando busca inteligente: '{query}'")
            
            # Conecta ferramentas à LLM
            model_with_tools = self.llm.bind_tools(self.langchain_tools)
            
            # Mensagens iniciais
            messages = [
                SystemMessage(content=self._build_system_prompt()),
                HumanMessage(content=query)
            ]
            
            tools_called = []
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                log.info(f"🔄 Iteração {iteration}/{max_iterations}")
                
                # LLM decide qual ferramenta usar
                response = model_with_tools.invoke(messages)
                
                # Se não há tool calls, LLM terminou
                if not (hasattr(response, "tool_calls") and response.tool_calls):
                    log.info("✅ LLM finalizou sem mais ferramentas")
                    break
                
                messages.append(response)
                
                # Executa cada tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call.get("args", {})
                    tool_call_id = tool_call.get("id", f"call_{iteration}")
                    
                    log.info(f"🛠️ Executando: {tool_name} com {tool_args}")
                    
                    try:
                        # Executa ferramenta
                        result = self.mcp_client.call_tool(tool_name, tool_args)
                        
                        tools_called.append({
                            "name": tool_name,
                            "args": tool_args,
                            "result": result,
                            "iteration": iteration
                        })
                        
                        # Processa resultado
                        result_content = self._format_tool_result(result)
                        
                        # Adiciona resultado às mensagens
                        tool_message = ToolMessage(
                            content=result_content,
                            tool_call_id=tool_call_id
                        )
                        messages.append(tool_message)
                        
                        log.info(f"✅ Ferramenta '{tool_name}' executada com sucesso")
                        
                    except Exception as e:
                        log.error(f"❌ Erro executando {tool_name}: {e}")
                        
                        # Adiciona erro às mensagens
                        error_message = ToolMessage(
                            content=f"Erro ao executar {tool_name}: {str(e)}",
                            tool_call_id=tool_call_id
                        )
                        messages.append(error_message)
                        
                        tools_called.append({
                            "name": tool_name,
                            "args": tool_args,
                            "error": str(e),
                            "iteration": iteration
                        })
            
            # Resposta final da LLM
            final_response = model_with_tools.invoke(messages)
            final_content = final_response.content if hasattr(final_response, "content") else str(final_response)
            
            log.info(f"🎯 Busca concluída após {iteration} iterações")
            log.info(f"📋 Ferramentas chamadas: {[t['name'] for t in tools_called]}")
            
            # Determina se paciente foi encontrado
            patient_found = self._determine_if_patient_found(tools_called, final_content)
            
            return {
                "found": patient_found,
                "data": final_content,
                "tools_called": tools_called,
                "iterations": iteration,
                "query": query
            }
            
        except Exception as e:
            log.error(f"❌ Erro na busca inteligente: {e}")
            return {
                "found": False,
                "error": str(e),
                "query": query
            }
    
    def _format_tool_result(self, result: Any) -> str:
        """Formata resultado da ferramenta para a LLM."""
        if isinstance(result, dict):
            if "content" in result:
                return str(result["content"])
            return json.dumps(result, indent=2, ensure_ascii=False)
        return str(result)
    
    def _determine_if_patient_found(self, tools_called: List[Dict], final_content: str) -> bool:
        """Determina se um paciente foi encontrado baseado nos resultados."""
        if not tools_called:
            return False
        
        # Verifica se alguma ferramenta retornou dados de paciente
        for tool_call in tools_called:
            if "error" in tool_call:
                continue
                
            result = tool_call.get("result", {})
            
            # Se é dict e tem campos de paciente
            if isinstance(result, dict):
                if any(key in result for key in ["id", "nome", "cpf", "rg"]):
                    return True
                    
                # Verifica content
                content = result.get("content", "")
                if isinstance(content, str):
                    not_found_indicators = [
                        "nenhum paciente encontrado",
                        "paciente não encontrado",
                        "não localizado"
                    ]
                    if not any(indicator in content.lower() for indicator in not_found_indicators):
                        # Se não tem indicadores de "não encontrado", pode ser positivo
                        if any(word in content.lower() for word in ["paciente", "nome", "id", "dados"]):
                            return True
        
        # Verifica resposta final
        if final_content:
            not_found_phrases = [
                "nenhum paciente",
                "não encontrado",
                "não foram encontrados",
                "não localizado"
            ]
            return not any(phrase in final_content.lower() for phrase in not_found_phrases)
        
        return False
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Retorna lista de ferramentas disponíveis."""
        return self.available_tools
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente MCP."""
        try:
            tools_count = len(self.available_tools)
            langchain_tools_count = len(self.langchain_tools)
            
            return {
                "status": "healthy",
                "tools_available": tools_count,
                "langchain_tools": langchain_tools_count,
                "mcp_connection": "active"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "tools_available": 0,
                "mcp_connection": "failed"
            }