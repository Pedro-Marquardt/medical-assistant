import numpy as np
from typing import Tuple, Optional, Dict
from langchain_ollama import OllamaEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from api.infra.config.env import ConfigEnvs
from api.infra.utils.logger import log
from api.infra.utils.query_normalizer import query_normalizer 
from api.application.services.semantic_anchor.anchor_interface import SemanticAnchorInterface

class SemanticAnchor(SemanticAnchorInterface):
    """
    Router semântico inteligente: decide se busca MCP ou faz busca vetorial.
    Sistema baseado em collections de âncoras com penalizações.
    """
    
    def __init__(self, host: Optional[str] = None) -> None:
        self.host = host or ConfigEnvs.HOST_OLLAMA
        self.embeddings_model = None
        self.hybrid_vectors = None
        self.penalty_vectors = None
        self._initialized = False
        
        # Collections de âncoras baseadas nos dados reais
        self.hybrid_anchors = [
            # Pacientes específicos com identificadores
            "dados do paciente João da Silva",
            "informações do paciente Maria Souza Oliveira", 
            "prontuário do Pedro Henrique de Almeida",
            "consultar ficha da Ana Beatriz Ferreira",
            "histórico médico do Carlos Roberto Gomes",
            "dados da paciente Luciana Mendes",
            "perfil do paciente Roberto Carlos Braga",
            
            # Padrões com CPF
            "paciente com CPF 123.456.789-00",
            "buscar CPF 987.654.321-11", 
            "dados do CPF 111.222.333-44",
            "informações CPF 555.666.777-88",
            "consultar CPF 444.555.666-77",
            "verificar CPF 222.333.444-55",
            "localizar CPF 333.444.555-66",
            
            # Padrões com IDs de paciente
            "paciente PAC-001",
            "dados do PAC-002",
            "informações do PAC-003", 
            "consultar PAC-004",
            "verificar PAC-005",
            "buscar PAC-006",
            "localizar PAC-007",
            
            # Contextos personalizados
            "orientações específicas para o paciente",
            "tratamento personalizado do paciente",
            "medicamentos atuais do paciente",
            "alergias conhecidas do paciente",
            "histórico familiar do paciente",
            "condições médicas do paciente específico",
            "dados cadastrais do paciente",
            "informações pessoais médicas",
            "consulta individual do paciente",
            "avaliação personalizada para",
            "protocolo direcionado ao paciente",
            "orientação médica individual"
        ]
        
        self.penalty_anchors = [
            # Protocolos gerais (baseados nos documentos reais)
            "protocolo geral para dor torácica",
            "diretriz padrão de infarto agudo do miocárdio",
            "tratamento padrão para cetoacidose diabética",
            "protocolo hospitalar para choque anafilático", 
            "manejo geral de crise de asma",
            "profilaxia padrão do tétano",
            
            # Sintomas e condições gerais
            "sintomas comuns de hipertensão",
            "sinais típicos de diabetes",
            "manifestações de asma leve",
            "sintomas de epilepsia",
            "sinais de insuficiência renal",
            "manifestações de hipotireoidismo",
            "sintomas de arritmia cardíaca",
            "sinais de osteoartrite",
            
            # Termos médicos genéricos
            "diagnóstico diferencial geral",
            "procedimento clínico padrão",
            "algoritmo diagnóstico hospitalar",
            "fluxograma de atendimento",
            "conduta médica de rotina",
            "protocolo de emergência geral",
            "diretrizes clínicas gerais",
            "tratamento hospitalar padrão",
            "procedimentos de urgência",
            "protocolos de atendimento",
            "algoritmos clínicos",
            "condutas médicas gerais",
            
            # Consultas genéricas sobre doenças
            "o que é hipertensão arterial",
            "como tratar diabetes tipo 2", 
            "sintomas de asma em geral",
            "tratamento para epilepsia",
            "causas de insuficiência renal",
            "diagnóstico de hipotireoidismo",
            "tipos de arritmia cardíaca",
            "prevenção de osteoartrite"
        ]
        
    def initialize(self) -> bool:
        """Inicializa âncoras no startup."""
        try:
            log.info("Inicializando router semântico inteligente...")
            
            self.embeddings_model = OllamaEmbeddings(
                base_url=self.host,
                model=ConfigEnvs.EMBEDDING_MODEL
            )
            
            # Gera embeddings para collections separadas
            hybrid_embeddings = self.embeddings_model.embed_documents(self.hybrid_anchors)
            penalty_embeddings = self.embeddings_model.embed_documents(self.penalty_anchors)
            
            self.hybrid_vectors = np.array(hybrid_embeddings)
            self.penalty_vectors = np.array(penalty_embeddings)
            
            self._initialized = True
            log.info(f"Router inicializado - {len(self.hybrid_anchors)} âncoras hybrid, {len(self.penalty_anchors)} âncoras penalty")
            return True
            
        except Exception as e:
            log.error(f"Erro ao inicializar router: {e}")
            return False
    
    
    def route(self, query: str, threshold: float = 0.6, penalty_weight: float = 0.15) -> str:
        if not self._initialized:
            log.warning("Router não inicializado, usando vector_search")
            return "vector_search"
        
        try:
            # Log da query original
            log.info(f"🔍 Query original: '{query}'")
            
            # Normaliza a query para análise adicional
            normalized_query = query_normalizer.normalize(query)
            log.info(f"🔍 Query normalizada: '{normalized_query}'")
            
            # Embedding da query
            query_embedding = self.embeddings_model.embed_query(query)
            query_vector = np.array([query_embedding])
            
            # Similaridade com âncoras hybrid (indicam busca específica de paciente)
            hybrid_similarities = cosine_similarity(query_vector, self.hybrid_vectors)[0]
            max_hybrid = np.max(hybrid_similarities)
            best_hybrid_idx = np.argmax(hybrid_similarities)
            
            # Similaridade com âncoras penalty (indicam busca genérica)
            penalty_similarities = cosine_similarity(query_vector, self.penalty_vectors)[0]
            max_penalty = np.max(penalty_similarities) 
            best_penalty_idx = np.argmax(penalty_similarities)
            
            # Score final = hybrid_score - (penalty_score * peso)
            final_score = max_hybrid - (max_penalty * penalty_weight)
            
            hybrid_boost = 0
            if max_hybrid > max_penalty:
                hybrid_boost = 0.10  
                final_score += hybrid_boost
                log.info(f"🚀 Boost hybrid aplicado: +{hybrid_boost:.3f} (hybrid {max_hybrid:.3f} > penalty {max_penalty:.3f})")
                

            # Logs detalhados das análises
            log.info(f"📊 Hybrid score: {max_hybrid:.3f}")
            log.info(f"📊 Penalty score: {max_penalty:.3f}") 
            log.info(f"📊 Final score: {final_score:.3f} (hybrid - penalty*{penalty_weight:.2f} + boost:{hybrid_boost:.3f})")
            
            # Log das melhores correspondências
            log.info(f"🎯 Melhor hybrid: '{self.hybrid_anchors[best_hybrid_idx]}' ({max_hybrid:.3f})")
            log.info(f"⚠️  Melhor penalty: '{self.penalty_anchors[best_penalty_idx]}' ({max_penalty:.3f})")
            
            additional_penalties = 0
            if "[diagnostico]" in normalized_query and not any(tag in normalized_query for tag in ["[nome]", "[cpf]", "[rg]", "[id]"]):
                additional_penalties += 0.02  # Penalização muito reduzida
                log.info(f"⚠️  Penalização adicional por [diagnostico] sem identificador: -{0.02:.3f}")
            
            # Score final com penalizações adicionais
            final_score_adjusted = final_score - additional_penalties
            log.info(f"📊 Score final ajustado: {final_score_adjusted:.3f}")
            
            # Decisão de roteamento
            if final_score_adjusted >= threshold:
                log.info(f"✅ DECISÃO: hybrid_search (score {final_score_adjusted:.3f} >= {threshold})")
                return "hybrid_search"
            else:
                log.info(f"📚 DECISÃO: vector_search (score {final_score_adjusted:.3f} < {threshold})")
                return "vector_search"
                
        except Exception as e:
            log.error(f"Erro no roteamento: {e}")
            return "vector_search" 