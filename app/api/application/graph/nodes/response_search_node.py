"""
Nó responsável por gerar respostas baseadas nos protocolos médicos encontrados.
Inclui guardrails para não prescrever medicamentos e sempre citar fontes.
"""

from typing import Dict, Any, List, Generator
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from api.infra.config.env import ConfigEnvs
from api.infra.utils.logger import log

class ResponseSearchNode:
    """
    Nó responsável por gerar respostas médicas baseadas nos protocolos encontrados.
    Inclui guardrails de segurança e citação obrigatória de fontes.
    """
    
    def __init__(self, llm_model: str = None):
        self.llm = ChatOllama(
            model=llm_model or ConfigEnvs.LLM_MODEL or "llama3.1",
            base_url=ConfigEnvs.HOST_OLLAMA,
            temperature=0.1  # Baixa temperatura para respostas consistentes
        )
        self.prompt_template = self._create_prompt_template()
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera resposta final baseada nos protocolos encontrados.
        
        Args:
            state: Estado atual do grafo com protocolos e dados de pacientes
            
        Returns:
            Dict: Estado atualizado com resposta final
        """
        try:
            query = state.get("query", "")
            protocols = state.get("protocols", [])
            patient_data = state.get("patient_data")
            search_type = state.get("search_type", "vector_search")
            
            log.info(f"Gerando resposta médica - Protocolos: {len(protocols)}, Paciente: {patient_data is not None}")
            
            # Gera resposta em streaming usando LLM com guardrails
            response_stream = self._generate_medical_response(query, protocols, patient_data, search_type)
            
            # Atualiza estado
            state.update({
                "response_stream": response_stream,
                "response_type": "vector_search",
                "response_generated": True,
                "protocols_used": len(protocols),
                "has_patient_context": patient_data is not None
            })
            
            log.info("Resposta médica gerada com sucesso")
            
            return state
            
        except Exception as e:
            log.error(f"Erro na geração de resposta: {e}")
            
            # Fallback com resposta padrão em streaming
            state.update({
                "response_stream": self._generate_fallback_stream(),
                "response_type": "fallback",
                "response_generated": False,
                "response_error": str(e)
            })
            
            return state
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Cria template de prompt com guardrails médicos."""
        
        template = """
Você é um assistente médico especializado que fornece informações baseadas em protocolos hospitalares.

🚨 GUARDRAILS OBRIGATÓRIOS:
- NUNCA prescreva medicamentos específicos
- NUNCA dê dosagens ou posologias
- NUNCA substitua consulta médica presencial
- SEMPRE cite as fontes dos protocolos utilizados
- SEMPRE recomende avaliação médica presencial para casos específicos

CONTEXTO DA CONSULTA:
Pergunta: {query}
Tipo de busca: {search_type}

{patient_context}

PROTOCOLOS ENCONTRADOS:
{protocols_context}

INSTRUÇÕES:
1. Analise os protocolos fornecidos
2. Forneça orientações gerais baseadas nos protocolos
3. SEMPRE cite a fonte de cada protocolo mencionado
4. Recomende avaliação médica quando apropriado
5. Use linguagem clara e profissional

FORMATO DA RESPOSTA:
**Orientações baseadas nos protocolos:**
[Orientações gerais baseadas nos protocolos]

**Protocolos consultados:**
[Liste os protocolos com suas fontes]

**⚠️ Importante:**
Esta informação é baseada em protocolos hospitalares e não substitui avaliação médica presencial. Sempre procure um profissional de saúde qualificado para avaliação específica.

RESPOSTA:
"""
        
        return PromptTemplate(
            input_variables=["query", "search_type", "patient_context", "protocols_context"],
            template=template
        )
    
    def _generate_medical_response(
        self, 
        query: str, 
        protocols: List[Dict[str, Any]], 
        patient_data: Dict[str, Any], 
        search_type: str
    ) -> Generator[str, None, None]:
        """
        Gera resposta médica usando LLM com guardrails em streaming.
        
        Args:
            query: Consulta original do usuário
            protocols: Lista de protocolos encontrados
            patient_data: Dados do paciente (se disponível)
            search_type: Tipo de busca realizada
            
        Yields:
            str: Chunks da resposta em streaming
        """
        try:
            # Prepara contexto do paciente
            patient_context = self._format_patient_context(patient_data)
            
            # Prepara contexto dos protocolos
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
            log.error(f"Erro na geração de resposta LLM: {e}")
            yield from self._generate_fallback_stream()
    
    def _format_patient_context(self, patient_data: Dict[str, Any]) -> str:
        """Formata contexto do paciente para o prompt."""
        
        if not patient_data:
            return "CONTEXTO DO PACIENTE:\nNenhum dado específico de paciente fornecido."
        
        context = ["CONTEXTO DO PACIENTE:"]
        
        if patient_data.get("found"):
            context.append("✅ Dados de paciente encontrados no sistema")
            context.append("⚠️ Informações do paciente disponíveis para contexto (dados sensíveis omitidos)")
        else:
            context.append("ℹ️ Consulta geral - sem dados específicos de paciente")
        
        return "\n".join(context)
    
    def _format_protocols_context(self, protocols: List[Dict[str, Any]]) -> str:
        """Formata contexto dos protocolos para o prompt."""
        
        if not protocols:
            return "Nenhum protocolo específico encontrado. Responda com orientações gerais e recomende consulta médica."
        
        context = []
        
        for i, protocol in enumerate(protocols, 1):
            content = protocol.get("content", "")
            source = protocol.get("source", "Fonte não identificada")
            score = protocol.get("score", 0.0)
            
            context.append(f"PROTOCOLO {i}:")
            context.append(f"Conteúdo: {content[:500]}...")  # Limita tamanho
            context.append(f"Fonte: {source}")
            context.append(f"Relevância: {score:.2f}")
            context.append("---")
        
        return "\n".join(context)
    
    def _generate_fallback_stream(self) -> Generator[str, None, None]:
        """Gera resposta padrão em streaming para casos de erro."""
        
        fallback_parts = [
            "**⚠️ Sistema temporariamente indisponível**\n\n",
            "Não foi possível consultar os protocolos médicos no momento.\n\n",
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
    
    def _add_safety_footer(self, response: str) -> str:
        """Adiciona rodapé de segurança à resposta."""
        
        safety_footer = """

---
**🔒 Aviso de Segurança:**
- Esta informação é baseada em protocolos hospitalares
- Não substitui avaliação médica presencial
- Em emergências, procure atendimento médico imediatamente
- Sempre consulte um profissional de saúde qualificado
---
"""
        
        return response + safety_footer
    
    def get_guardrails_info(self) -> Dict[str, Any]:
        """Retorna informações sobre os guardrails implementados."""
        
        return {
            "guardrails_active": True,
            "restrictions": [
                "Não prescreve medicamentos",
                "Não fornece dosagens",
                "Não substitui consulta médica",
                "Sempre cita fontes",
                "Recomenda avaliação presencial"
            ],
            "safety_measures": [
                "Temperatura baixa (0.1) para consistência",
                "Template com instruções explícitas",
                "Rodapé de segurança obrigatório",
                "Fallback para respostas padrão"
            ]
        }
