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
Você é um assistente médico especializado que integra protocolos hospitalares com dados específicos do paciente para fornecer orientações clínicas contextualizadas.

🎯 DIRETRIZES CLÍNICAS:
- ANALISE SEMPRE o histórico médico e alergias do paciente
- CONSIDERE contraindicações baseadas no perfil do paciente
- MENCIONE medicamentos e tratamentos conforme protocolos quando relevante
- DESTAQUE fatores de risco específicos do paciente
- CONTEXTUALIZE recomendações com dados disponíveis
- CITE fontes dos protocolos utilizados
- RECOMENDE acompanhamento médico apropriado

CONTEXTO DA CONSULTA:
Pergunta: {query}
Tipo de busca: {search_type}

{patient_context}

PROTOCOLOS ENCONTRADOS:
{protocols_context}

INSTRUÇÕES ESPECÍFICAS PARA ANÁLISE:
1. **PRIMEIRO**: Extraia e destaque dados importantes do paciente (alergias, histórico familiar, comorbidades, medicamentos em uso)
2. **SEGUNDO**: Correlacione os protocolos com o perfil específico do paciente
3. **TERCEIRO**: Identifique contraindicações ou cuidados especiais baseados no histórico
4. **QUARTO**: Forneça orientações clínicas contextualizadas mencionando medicamentos/tratamentos quando apropriado
5. **QUINTO**: Recomende próximos passos considerando o contexto individual

FORMATO DA RESPOSTA:
**👤 PERFIL CLÍNICO DO PACIENTE:**
[Extraia e organize dados importantes: alergias, histórico familiar, comorbidades, medicamentos atuais, fatores de risco]

**🩺 ANÁLISE CONTEXTUALIZADA:**
[Correlacione protocolos com perfil do paciente, mencione medicamentos/tratamentos conforme protocolos, destaque contraindicações]

**📋 PROTOCOLOS CONSULTADOS:**
[Liste protocolos com fontes]

**⚠️ CONSIDERAÇÕES ESPECIAIS:**
[Cuidados específicos baseados no perfil do paciente]

**🔄 PRÓXIMOS PASSOS:**
[Recomendações de acompanhamento médico considerando o contexto]

**📌 Importante:** Esta análise integra protocolos hospitalares com dados específicos do paciente. Para prescrições e dosagens precisas, consulte médico responsável.

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
        """Formata contexto do paciente destacando dados clínicos importantes."""
        
        if not patient_data:
            return "DADOS DO PACIENTE:\n⚠️ Dados não disponíveis."
        
        if patient_data.get("found") and patient_data.get("data", {}).get("content"):
            content = patient_data["data"]["content"]
            return f"DADOS DO PACIENTE:\n{content}"
        else:
            return "DADOS DO PACIENTE:\n❌ Paciente não encontrado."
    
    def _format_protocols_context(self, protocols: List[Dict[str, Any]]) -> str:
        """Formata contexto dos protocolos de forma genérica."""
        
        if not protocols:
            return "Nenhum protocolo específico encontrado."
        
        context = []
        
        for i, protocol in enumerate(protocols, 1):
            content = protocol.get("content", "")
            source = protocol.get("source", "Fonte não identificada")
            context.append(f"PROTOCOLO {i}: {content} (Fonte: {source})")
        
        return "\n\n".join(context)
    
    def _has_patient_data(self, patient_data: Dict[str, Any]) -> bool:
        """Verifica se há dados do paciente de forma genérica."""
        return patient_data is not None
    
    def _generate_fallback_stream(self) -> Generator[str, None, None]:
        """Gera resposta informativa em streaming para casos de erro."""
        
        fallback_parts = [
            "**🔍 Análise temporariamente limitada**\n\n",
            "**SITUAÇÃO ATUAL:**\n",
            "- Sistema de protocolos médicos temporariamente indisponível\n",
            "- Dados do paciente podem não estar acessíveis\n\n",
            "**ORIENTAÇÕES GERAIS:**\n",
            "Para consultas sobre medicamentos e tratamentos:\n",
            "- Consulte o prontuário médico do paciente\n",
            "- Verifique alergias medicamentosas conhecidas\n",
            "- Considere histórico familiar e comorbidades\n",
            "- Avalie interações medicamentosas\n\n",
            "**EM EMERGÊNCIAS:**\n",
            "- Pronto-socorro para avaliação imediata\n",
            "- Protocolos de emergência da instituição\n\n",
            "**PRÓXIMOS PASSOS:**\n",
            "- Tente novamente em alguns instantes\n",
            "- Consulte protocolos institucionais físicos\n",
            "- Entre em contato com médico responsável\n\n",
            "📋 Lembre-se: Sempre correlacione orientações com o perfil específico do paciente."
        ]
        
        for part in fallback_parts:
            yield part
    
    def get_hybrid_info(self) -> Dict[str, Any]:
        """Retorna informações sobre as capacidades híbridas aprimoradas."""
        
        return {
            "node_type": "hybrid_response_enhanced",
            "patient_data_integration": True,
            "clinical_contextualization": True,
            "streaming_enabled": True,
            "features": [
                "Extração de dados clínicos importantes",
                "Correlação protocolos + perfil paciente", 
                "Identificação de contraindicações",
                "Menção contextualizada de medicamentos",
                "Análise de fatores de risco",
                "Streaming em tempo real",
                "Orientações personalizadas"
            ],
            "clinical_focus": [
                "Alergias medicamentosas",
                "Histórico familiar",
                "Comorbidades",
                "Medicamentos em uso",
                "Fatores de risco específicos",
                "Contraindicações"
            ],
            "safety_measures": [
                "Temperatura controlada (0.1)",
                "Template clínico especializado",
                "Análise contextualizada",
                "Fallback informativo",
                "Recomendação de acompanhamento médico"
            ]
        }
