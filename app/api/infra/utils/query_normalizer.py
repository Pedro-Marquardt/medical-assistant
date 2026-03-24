import re
from typing import Dict, List, Pattern

class QueryNormalizer:
    
    def __init__(self):
        # Padrões para remoção de dados específicos
        self.patterns: Dict[str, Pattern] = {
            # Nomes próprios (apenas em contexto de paciente) - aceita minúsculas também
            'names': re.compile(r'\b(?:paciente|sr\.?|sra\.?|dr\.?|dra\.?)\s+([A-Za-zçãõáéíóúâêîôûàèìòù]+(?:\s+[A-Za-zçãõáéíóúâêîôûàèìòù]+)*)\b', re.IGNORECASE),
            
            # CPF (XXX.XXX.XXX-XX ou apenas números)
            'cpf': re.compile(r'\bcpf\s*:?\s*\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2}\b', re.IGNORECASE),
            
            # RG (formatos variados)  
            'rg': re.compile(r'\brg\s*:?\s*[A-Z]{2}[-\.]?\d{2}\.?\d{3}\.?\d{3}\b|\brg\s*:?\s*\d{2}\.?\d{3}\.?\d{3}[-\.]?[A-Z]{1,2}\b', re.IGNORECASE),
            
            # IDs de pacientes (PAC-XXXXX, ID-XXXXX, etc.)
            'patient_ids': re.compile(r'\b(?:pac|id|paciente)[-_\s]*\d+\b', re.IGNORECASE),
            
            # Diagnósticos e condições médicas - ordem otimizada para capturar frases completas primeiro
            'diagnoses': re.compile(r'\b(?:dores?\s+(?:torácicas?|no\s+peito|de\s+cabeça|abdominais?|nas\s+costas|lombares?|musculares?|articulares?|de\s+garganta|de\s+ouvido|nos\s+dentes|de\s+dente|no\s+estômago|epigástricas?)|faltas?\s+de\s+ar|cetoacidose\s+diabética|choque\s+anafilático|crises?\s+hipertensivas?|insuficiência\s+cardíaca|edemas?\s+pulmonares?|sintomas?|tratamentos?|feridas?|cefaleia|enxaqueca|febre|náuseas?|vômitos?|tonturas?|vertigens?|fadiga|cansaço|dispneia|tosses?|coriza|espirros|coceira|prurido|erupções?|rash|inchaços?|edemas?|palpitações?|mal-estar|fraqueza|sonolência|insônia|ansiedade|estresse|depressão|diabetes|hipertensão|asma|anafilaxia|infarto|iam|angina|pneumonia|covid|bronquite|avc|derrame|arritmias?|taquicardias?|bradicardias?|fibrilações?)\b', re.IGNORECASE),  
        }
        
        # Substituições para manter a estrutura semântica
        self.replacements: Dict[str, str] = {
            'names': 'paciente [nome]',
            'cpf': 'cpf [cpf]',
            'rg': 'rg [rg]', 
            'patient_ids': 'paciente [id]',
            'diagnoses': '[diagnostico]',
        }
    
    def normalize(self, query: str) -> str:
        """
        Normaliza uma query removendo informações específicas.
        
        Args:
            query (str): Query original
            
        Returns:
            str: Query normalizada para análise semântica
        """
        normalized = query.strip()
        
        for pattern_name, pattern in self.patterns.items():
            replacement = self.replacements.get(pattern_name, '')
            normalized = pattern.sub(replacement, normalized)
        
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        normalized = normalized.lower()
        
        return normalized
    
    

# Singleton instance
query_normalizer = QueryNormalizer()