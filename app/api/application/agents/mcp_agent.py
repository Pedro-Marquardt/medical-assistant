"""
Agente MCP para interação com ferramentas do servidor MCP.
Utiliza o MCPClient para executar ferramentas de busca de pacientes.
"""

from typing import Any, Dict, List, Optional, Union
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from api.infra.services.mcp.client import MCPClient
from api.infra.config.env import ConfigEnvs
from api.infra.utils.logger import log


class MCPAgent:
    """
    Agente MCP que utiliza ferramentas do servidor MCP para busca de pacientes.
    Integrado com LangChain para processamento inteligente de consultas.
    """

    def __init__(self, mcp_client: MCPClient, llm_model: str = "mistral:7b"):
        self.mcp_client = mcp_client
        self.llm = ChatOllama(
            model=llm_model,
            base_url=ConfigEnvs.HOST_OLLAMA,
            temperature=0.1
        )
        self.tools = []
        self.agent_executor = None
        self._initialize_tools()
        self._create_agent()

    def _initialize_tools(self) -> None:
        """Inicializa as ferramentas baseadas no servidor MCP."""
        try:
            log.info("Inicializando ferramentas MCP")
            
            # Obtém as ferramentas disponíveis do servidor MCP
            mcp_tools = self.mcp_client.list_tools()
            
            # Converte ferramentas MCP para ferramentas LangChain
            langchain_tools = []
            
            for tool_info in mcp_tools:
                tool_name = tool_info["name"]
                tool_description = tool_info["description"]
                
                # Cria uma função wrapper para cada ferramenta MCP
                def create_tool_func(name: str):
                    def tool_func(query: str) -> str:
                        return self._execute_mcp_tool(name, query)
                    return tool_func
                
                # Cria ferramenta LangChain
                langchain_tool = Tool(
                    name=tool_name,
                    description=tool_description,
                    func=create_tool_func(tool_name)
                )
                
                langchain_tools.append(langchain_tool)
            
            self.tools = langchain_tools
            log.info(f"Inicializadas {len(self.tools)} ferramentas MCP")
            
        except Exception as e:
            log.error(f"Erro ao inicializar ferramentas MCP: {e}")
            self.tools = []

    def _execute_mcp_tool(self, tool_name: str, query: str) -> str:
        """
        Executa uma ferramenta MCP específica.
        
        Args:
            tool_name (str): Nome da ferramenta MCP
            query (str): Consulta/parâmetros para a ferramenta
            
        Returns:
            str: Resultado da execução da ferramenta
        """
        try:
            log.info(f"Executando ferramenta MCP: {tool_name} com query: {query}")
            
            # Mapeia argumentos baseado no tipo de ferramenta
            arguments = self._parse_tool_arguments(tool_name, query)
            
            # Executa a ferramenta via MCP Client
            result = self.mcp_client.call_tool(tool_name, arguments)
            
            # Formata o resultado como string
            if isinstance(result, dict):
                return str(result)
            elif isinstance(result, list):
                return "\n".join([str(item) for item in result])
            else:
                return str(result)
                
        except Exception as e:
            log.error(f"Erro ao executar ferramenta MCP {tool_name}: {e}")
            return f"Erro ao executar {tool_name}: {str(e)}"

    def _parse_tool_arguments(self, tool_name: str, query: str) -> Dict[str, Any]:
        """
        Analisa a consulta e extrai argumentos para a ferramenta específica.
        
        Args:
            tool_name (str): Nome da ferramenta
            query (str): Consulta do usuário
            
        Returns:
            Dict[str, Any]: Argumentos estruturados para a ferramenta
        """
        query_lower = query.lower().strip()
        
        # Mapeamento de ferramentas para argumentos
        if tool_name == "get_patient_by_cpf":
            # Extrai CPF da consulta
            # Busca por padrões de CPF: XXX.XXX.XXX-XX ou XXXXXXXXXXX
            import re
            cpf_pattern = r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})'
            match = re.search(cpf_pattern, query)
            if match:
                return {"cpf": match.group(1)}
            else:
                # Se não encontrar padrão, usa a query completa
                return {"cpf": query}
                
        elif tool_name == "get_patient_by_name":
            # Para nome, remove palavras-chave comuns
            keywords = ["buscar", "paciente", "nome", "por", "pelo", "pela"]
            words = query_lower.split()
            filtered_words = [w for w in words if w not in keywords]
            name = " ".join(filtered_words) if filtered_words else query
            return {"nome": name}
            
        elif tool_name == "get_patient_by_rg":
            # Extrai RG da consulta
            import re
            rg_pattern = r'([A-Z]{2}-?\d+\.?\d+\.?\d+|\d+\.?\d+\.?\d+)'
            match = re.search(rg_pattern, query.upper())
            if match:
                return {"rg": match.group(1)}
            else:
                return {"rg": query}
                
        elif tool_name == "get_patient_by_id":
            # Extrai ID no formato PAC-XXX
            import re
            id_pattern = r'(PAC-\d{3})'
            match = re.search(id_pattern, query.upper())
            if match:
                return {"id": match.group(1)}
            else:
                # Se não encontrar padrão PAC-XXX, procura por números
                num_pattern = r'(\d+)'
                num_match = re.search(num_pattern, query)
                if num_match:
                    return {"id": f"PAC-{num_match.group(1).zfill(3)}"}
                else:
                    return {"id": query}
        
        # Fallback: retorna a query como está
        return {"query": query}

    def _create_agent(self) -> None:
        """Cria o agente LangChain com as ferramentas MCP."""
        try:
            if not self.tools:
                log.warning("Nenhuma ferramenta disponível para criar o agente")
                return
            
            # Template de prompt para o agente médico
            prompt_template = """
Você é um assistente médico especializado em busca de informações de pacientes.
Você tem acesso a ferramentas para buscar pacientes por CPF, nome, RG ou ID.

Sua função é apenas buscar e retornar as informações dos pacientes solicitados.
Seja direto e objetivo, retornando apenas os dados encontrados.

Ferramentas disponíveis:
{tools}

Use o seguinte formato:

Pergunta: a pergunta de entrada que você deve responder
Pensamento: você deve sempre pensar sobre o que fazer
Ação: a ação a ser tomada, deve ser uma das [{tool_names}]
Entrada da Ação: a entrada para a ação
Observação: o resultado da ação
... (este processo Pensamento/Ação/Entrada da Ação/Observação pode ser repetido)
Pensamento: Agora eu sei a resposta final
Resposta Final: retorne apenas as informações dos pacientes encontrados

Pergunta: {input}
Pensamento: {agent_scratchpad}
"""

            prompt = PromptTemplate(
                input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
                template=prompt_template
            )

            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )

            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3
            )

            log.info("Agente MCP criado com sucesso")

        except Exception as e:
            log.error(f"Erro ao criar agente MCP: {e}")
            self.agent_executor = None

    def execute(self, query: str) -> str:

        try:
            if not self.agent_executor:
                return "Agente MCP não está disponível. Verifique as ferramentas MCP."
            
            log.info(f"Executando consulta no agente MCP: {query}")
            
            result = self.agent_executor.invoke({"input": query})
            
            if isinstance(result, dict) and "output" in result:
                response = result["output"]
            else:
                response = str(result)
            
            log.info("Consulta executada com sucesso pelo agente MCP")
            return response

        except Exception as e:
            log.error(f"Erro na execução do agente MCP: {e}")
            return f"Erro na execução: {str(e)}"

    def execute_direct_tool(self, tool_name: str, **kwargs) -> str:
        try:
            log.info(f"Executando ferramenta MCP diretamente: {tool_name}")
            
            result = self.mcp_client.call_tool(tool_name, kwargs)
            
            if isinstance(result, dict):
                return str(result)
            elif isinstance(result, list):
                return "\n".join([str(item) for item in result])
            else:
                return str(result)

        except Exception as e:
            log.error(f"Erro na execução direta da ferramenta {tool_name}: {e}")
            return f"Erro: {str(e)}"

    def get_available_tools(self) -> List[Dict[str, Any]]:
        try:
            return self.mcp_client.list_tools()
        except Exception as e:
            log.error(f"Erro ao listar ferramentas: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:

        try:
            tools = self.get_available_tools()
            agent_status = self.agent_executor is not None
            
            return {
                "agent_ready": agent_status,
                "tools_available": len(tools),
                "tools": [tool.get("name", "unknown") for tool in tools],
                "status": "healthy" if agent_status and tools else "degraded"
            }
            
        except Exception as e:
            log.error(f"Erro no health check do agente MCP: {e}")
            return {
                "agent_ready": False,
                "tools_available": 0,
                "tools": [],
                "status": "error",
                "error": str(e)
            }
