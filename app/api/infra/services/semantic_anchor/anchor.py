import numpy as np
from typing import Tuple
from langchain_ollama import OllamaEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
from api.infra.config.env import ConfigEnvs
from api.infra.utils.logger import log
from api.infra.utils.query_normalizer import query_normalizer 


class SemanticAnchor:
    """
    Router semântico simples: decide se busca MCP ou faz busca vetorial.
    """
    
    def __init__(self, host: str = None):
        self.host = host or ConfigEnvs.HOST_OLLAMA
        self.embeddings_model = None
        self.anchor_vectors = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Inicializa âncoras no startup."""
        try:
            log.info("Inicializando router semântico...")
            
            self.embeddings_model = OllamaEmbeddings(
                base_url=self.host,
                model=ConfigEnvs.EMBEDDING_MODEL
            )
            
            patient_anchors = query_normalizer.get_intent_patterns()

            anchor_embeddings = self.embeddings_model.embed_documents(patient_anchors)
            self.anchor_vectors = np.array(anchor_embeddings)
            
            self._initialized = True
            log.info("Router semântico inicializado")
            return True
            
        except Exception as e:
            log.error(f"Erro ao inicializar router: {e}")
            return False
    
    def route(self, query: str, threshold: float = 0.6) -> str:
        if not self._initialized:
            log.warning("Router não inicializado, usando vector_search")
            return "vector_search"
        
        try:
            query_embedding = self.embeddings_model.embed_query(query)
            query_vector = np.array([query_embedding])
            
            # Compara com âncoras de paciente
            similarities = cosine_similarity(query_vector, self.anchor_vectors)[0]
            max_similarity = np.max(similarities)
            best_pattern_idx = np.argmax(similarities)
            
            # Log detalhado das similaridades
            patient_anchors = query_normalizer.get_intent_patterns()
            
            # Log top 3 similaridades
            top_3_indices = np.argsort(similarities)[-3:][::-1]
            for i, idx in enumerate(top_3_indices):
                log.info(f"  {i+1}. {similarities[idx]:.3f} - '{patient_anchors[idx]}'")
            
            if max_similarity > threshold:
                log.info(f"DECISÃO: hybrid_search (similaridade {max_similarity:.3f} > {threshold})")
                return "hybrid_search"  # Precisa buscar paciente no MCP
            else:
                log.info(f"DECISÃO: vector_search (similaridade {max_similarity:.3f} <= {threshold})")
                return "vector_search"   
                
        except Exception as e:
            log.error(f"Erro no roteamento: {e}")
            return "vector_search" 