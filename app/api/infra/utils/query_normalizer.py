import re
from typing import Dict, List, Pattern

class QueryNormalizer:
    
    def __init__(self):
        # Padrões para remoção de dados específicos
        self.patterns: Dict[str, Pattern] = {
            'names': re.compile(r'\b[A-Z][a-zçãõáéíóúâêîôûàèìòù]+(?:\s+[A-Z][a-zçãõáéíóúâêîôûàèìòù]+)*\b'),
            
            # CPF (XXX.XXX.XXX-XX ou apenas números)
            'cpf': re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2}\b'),
            
            # RG (formatos variados)
            'rg': re.compile(r'\b[A-Z]{2}[-\.]?\d{2}\.?\d{3}\.?\d{3}\b|\b\d{2}\.?\d{3}\.?\d{3}[-\.]?[A-Z]{1,2}\b'),
            
            # IDs de pacientes (PAC-XXXXX, ID-XXXXX, etc.)
            'patient_ids': re.compile(r'\b(?:PAC|ID|PACIENTE)[-_]?\d+\b', re.IGNORECASE),
            
            # Números de prontuário
            'medical_record': re.compile(r'\bprontu[aá]rio\s+n[°º]?\s*\d+\b', re.IGNORECASE),
            
            # Datas (DD/MM/AAAA, DD-MM-AAAA, etc.)
            'dates': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
            
            # Horários (HH:MM)
            'times': re.compile(r'\b\d{1,2}:\d{2}\b'),
            
            # Valores numéricos específicos (dosagens, idades, etc.)
            'specific_numbers': re.compile(r'\b\d+(?:\.\d+)?\s*(?:mg|ml|g|kg|anos?|dias?|horas?|minutos?)\b', re.IGNORECASE),
            
            # Medicamentos específicos (começam com maiúscula + números/símbolos)
            'medications': re.compile(r'\b[A-Z][a-z]+(?:[A-Z][a-z]*)*\s*\d*(?:mg|ml)?\b'),
            
            # Códigos médicos (CID, etc.)
            'medical_codes': re.compile(r'\b(?:CID|ICD)[-\s]*[A-Z]?\d+(?:\.\d+)?\b', re.IGNORECASE),
            
            # Números de leitos/quartos
            'room_numbers': re.compile(r'\b(?:leito|quarto|sala)\s+\d+\b', re.IGNORECASE),
        }
        
        # Substituições para manter a estrutura semântica
        self.replacements: Dict[str, str] = {
            'names': '[NOME]',
            'cpf': '[CPF]',
            'rg': '[RG]', 
            'patient_ids': '[ID]',
            'medical_record': 'prontuário [NUMERO]',
            'dates': '[DATA]',
            'times': '[HORA]',
            'specific_numbers': '[VALOR]',
            'medications': '[MEDICAMENTO]',
            'medical_codes': '[CODIGO]',
            'room_numbers': '[LEITO]',
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
        
        # Aplica todas as substituições
        for pattern_name, pattern in self.patterns.items():
            replacement = self.replacements.get(pattern_name, '')
            normalized = pattern.sub(replacement, normalized)
        
        # Remove espaços duplos e limpa a string
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def get_intent_patterns(self) -> List[str]:

        return [
            "dados do paciente [NOME]",
            "informações do paciente com cpf [CPF]",
            "paciente com id [ID]",
            "buscar paciente [NOME]",
            "encontrar paciente com rg [RG]",
            "alergias do paciente",
            "histórico médico do paciente", 
            "medicamentos do paciente",
            "diagnóstico do paciente",
            "paciente apresenta sintomas",
        ]

# Singleton instance
query_normalizer = QueryNormalizer()