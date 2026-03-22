"""
Nó responsável por gerar respostas híbridas baseadas em protocolos médicos e dados de pacientes.
Inclui guardrails médicos e considera informações específicas do paciente.
"""

from typing import Dict, Any, List, Generator
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from api.infra.config.env import ConfigEnvs
from api.infra.utils.logger import log

class ResponseHybridNode:
    """
    Nó responsável por gerar respostas híbridas considerando protocolos médicos e dados de pacientes.
    Inclui guardrails de segurança e streaming de resposta.
    """
    
    def __init__(self, llm_model: str = None):
        self.llm = ChatOllama(
            model=llm_model or ConfigEnvs.LLM_MODEL or "llama3.1",
            base_url=ConfigEnvs.HOST_OLLAMA,
            temperature=0.1  # Baixa temperatura para respostas consistentes
        )
        self.prompt_template = self._create_hybrid_prompt_template()
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera resposta híbrida baseada em protocolos e dados de pacientes.
        
        Args:
            state: Estado atual do grafo com protocolos e dados de pacientes
            
        Returns:
            Dict: Estado atualizado com resposta em streaming
        """
        try:
            query = state.get("query", "")
            protocols = state.get("protocols", [])
            patient_data = state.get("patient_data")
            search_type = state.get("search_type", "hybrid_search")
            
            log.info(f"Gerando resposta híbrida - Protocolos: {len(protocols)}, Paciente: {patient_data is not None}")
            
            # Gera resposta em streaming com dados do paciente
            response_stream = self._generate_hybrid_response_stream(query, protocols, patient_data, search_type)
            
            # Atualiza estado
            state.update({
                "response_stream": response_stream,
                "response_type": "hybrid_with_patient_data",
                "response_generated": True,
                "protocols_used": len(protocols),
                "has_patient_context": patient_data is not None,
                "patient_considered": self._has_patient_data(patient_data)
            })
            
            log.info("Resposta híbrida em streaming gerada com sucesso")
            
            return state
            
        except Exception as e:
            log.error(f"Erro na geração de resposta híbrida: {e}")
            
            # Fallback com resposta padrão
            state.update({
                "response_stream": self._generate_fallback_stream(),
                "response_type": "fallback",
                "response_generated": False,
                "response_error": str(e)
            })
            
            return state
    
    def _create_hybrid_prompt_template(self) -> PromptTemplate:
        """Cria template de prompt híbrido com consideração de dados do paciente."""
        
        template = """
Você é um assistente médico especializado que integra protocolos hospitalares com dados específicos do paciente.

🚨 GUARDRAILS OBRIGATÓRIOS:
- NUNCA prescreva medicamentos específicos
- NUNCA dê dosagens ou posologias
- NUNCA substitua consulta médica presencial
- SEMPRE cite as fontes dos protocolos utilizados
- SEMPRE considere o contexto específico do paciente
- SEMPRE recomende avaliação médica presencial personalizada

CONTEXTO DA CONSULTA:
Pergunta: {query}
Tipo de busca: {search_type}

{patient_context}

PROTOCOLOS ENCONTRADOS:
{protocols_context}

INSTRUÇÕES ESPECÍFICAS PARA RESPOSTA HÍBRIDA:
1. Analise os protocolos em relação ao contexto específico do paciente
2. Forneça orientações personalizadas baseadas nos protocolos e dados disponíveis
3. SEMPRE cite a fonte de cada protocolo mencionado
4. Destaque recomendações específicas baseadas no perfil do paciente
5. Recomende avaliação médica considerando o contexto individual
6. Use linguagem clara, empática e profissional

FORMATO DA RESPOSTA:
**🏥 Análise baseada em protocolos e contexto do paciente:**
[Análise integrada considerando protocolos + dados do paciente]

**📋 Protocolos consultados:**
[Liste os protocolos com suas fontes]

**👤 Considerações específicas:**
[Recomendações baseadas no contexto do paciente]

**⚠️ Importante:**
Esta análise integra protocolos hospitalares com o contexto específico disponível, mas não substitui avaliação médica presencial personalizada. Procure um profissional de saúde para avaliação completa.

RESPOSTA:
"""
        
        return PromptTemplate(
            input_variables=["query", "search_type", "patient_context", "protocols_context"],
            template=template
        )
    
    def _generate_hybrid_response_stream(self, query: str, protocols: List[Dict[str, Any]], patient_data: Dict[str, Any], search_type: str) -> Generator[str, None, None]:
        """
        Gera resposta híbrida em streaming.
        
        Args:
            query: Consulta original do usuário
            protocols: Lista de protocolos encontrados
            patient_data: Dados do paciente
            search_type: Tipo de busca realizada
            
        Yields:
            str: Chunks da resposta em streaming
        """
        try:
            # Prepara contexto do paciente (genérico)
            patient_context = self._format_patient_context(patient_data)
            
            # Prepara contexto dos protocolos (genérico)
            protocols_context = self._format_protocols_context(protocols)
            
            # Gera prompt
            prompt = self.prompt_template.format(
                query=query,
                search_type=search_type,
                patient_context=patient_context,
                protocols_context=protocols_context
            )
            
            # Stream resposta do LLM
            for chunk in self.llm.stream(prompt):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)
                    
        except Exception as e:
            log.error(f"Erro no streaming de resposta híbrida: {e}")
            yield from self._generate_fallback_stream()
    
    def _format_patient_context(self, patient_data: Dict[str, Any]) -> str:
        """Formata contexto do paciente de forma genérica."""
        
        if not patient_data:
            return "CONTEXTO DO PACIENTE:\n⚠️ Dados de paciente não disponíveis."
        
        if patient_data.get("found") and patient_data.get("data", {}).get("content"):
            # Passa o conteúdo diretamente do MCP
            content = patient_data["data"]["content"]
            return f"CONTEXTO DO PACIENTE:\n{content}"
        else:
            return "CONTEXTO DO PACIENTE:\n❌ Paciente não encontrado no sistema."
    
    def _format_protocols_context(self, protocols: List[Dict[str, Any]]) -> str:
        """Formata contexto dos protocolos de forma genérica."""
        
        if not protocols:
            return "Nenhum protocolo específico encontrado."
        
        context = []
        
        for i, protocol in enumerate(protocols, 1):
            content = protocol.get("content", "")
            source = protocol.get("source", "Fonte não identificada")
            
            context.append(f"PROTOCOLO {i}:")
            context.append(f"Conteúdo: {content}")
            context.append(f"Fonte: {source}")
            context.append("---")
        
        return "\n".join(context)
    
    def _has_patient_data(self, patient_data: Dict[str, Any]) -> bool:
        """Verifica se há dados do paciente de forma genérica."""
        return patient_data is not None
    
    def _generate_fallback_stream(self) -> Generator[str, None, None]:
        """Gera resposta padrão em streaming para casos de erro."""
        
        fallback_parts = [
            "**⚠️ Sistema temporariamente indisponível**\n\n",
            "Não foi possível consultar os protocolos médicos ou dados do paciente no momento.\n\n",
            "**Recomendação:**\n",
            "- Procure avaliação médica presencial para sua consulta\n",
            "- Em caso de emergência, dirija-se ao pronto-socorro mais próximo\n",
            "- Tente novamente em alguns instantes\n\n",
            "**Importante:**\n",
            "Este sistema não substitui avaliação médica profissional. ",
            "Sempre procure um médico qualificado para orientações específicas sobre sua saúde."
        ]
        
        for part in fallback_parts:
            yield part
    
    def get_hybrid_info(self) -> Dict[str, Any]:
        """Retorna informações sobre as capacidades híbridas."""
        
        return {
            "node_type": "hybrid_response",
            "patient_data_integration": True,
            "streaming_enabled": True,
            "guardrails_active": True,
            "features": [
                "Integração protocolo + paciente",
                "Resposta personalizada",
                "Streaming em tempo real",
                "Guardrails médicos",
                "Contexto detalhado"
            ],
            "safety_measures": [
                "Temperatura baixa (0.1) para consistência",
                "Template híbrido especializado",
                "Consideração de dados do paciente",
                "Fallback com streaming"
            ]
        }
