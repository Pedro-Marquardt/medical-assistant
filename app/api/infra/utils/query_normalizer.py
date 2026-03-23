import re
from typing import Dict, List, Pattern

class QueryNormalizer:
    
    def __init__(self):
        # Padrões para remoção de dados específicos
        self.patterns: Dict[str, Pattern] = {
            # Nomes próprios (apenas em contexto de paciente)
            'names': re.compile(r'\b(?:paciente|sr\.?|sra\.?|dr\.?|dra\.?)\s+([A-Z][a-zçãõáéíóúâêîôûàèìòù]+(?:\s+[A-Z][a-zçãõáéíóúâêîôûàèìòù]+)*)\b', re.IGNORECASE),
            
            # CPF (XXX.XXX.XXX-XX ou apenas números)
            'cpf': re.compile(r'\bcpf\s*:?\s*\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2}\b', re.IGNORECASE),
            
            # RG (formatos variados)  
            'rg': re.compile(r'\brg\s*:?\s*[A-Z]{2}[-\.]?\d{2}\.?\d{3}\.?\d{3}\b|\brg\s*:?\s*\d{2}\.?\d{3}\.?\d{3}[-\.]?[A-Z]{1,2}\b', re.IGNORECASE),
            
            # IDs de pacientes (PAC-XXXXX, ID-XXXXX, etc.)
            'patient_ids': re.compile(r'\b(?:pac|id|paciente)[-_\s]*\d+\b', re.IGNORECASE),
            
            # Diagnósticos e condições médicas
            'diagnoses': re.compile(r'\b(?:dor\s+torácica|cetoacidose\s+diabética|diabetes|hipertensão|asma|anafilaxia|choque\s+anafilático|infarto|iam|angina|pneumonia|covid|bronquite|avc|derrame|crise\s+hipertensiva|arritmia|taquicardia|bradicardia|fibrilação|insuficiência\s+cardíaca|edema\s+pulmonar)\b', re.IGNORECASE),
            
            # Números de prontuário
            'medical_record': re.compile(r'\bprontu[aá]rio\s+n[°º]?\s*\d+\b', re.IGNORECASE),
            
            # Datas (DD/MM/AAAA, DD-MM-AAAA, etc.)
            'dates': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
            
            # Horários (HH:MM)
            'times': re.compile(r'\b\d{1,2}:\d{2}\b'),
            
            # Valores numéricos específicos (dosagens, idades, etc.)
            'specific_numbers': re.compile(r'\b\d+(?:\.\d+)?\s*(?:mg|ml|g|kg|anos?|dias?|horas?|minutos?)\b', re.IGNORECASE),
            
            # Medicamentos específicos (apenas com contexto claro)
            'medications': re.compile(r'\b(?:medicamento|remedio|droga)\s+([A-Z][a-z]+(?:[A-Z][a-z]*)*\s*\d*(?:mg|ml)?)\b', re.IGNORECASE),
            
            # Códigos médicos (CID, etc.)
            'medical_codes': re.compile(r'\b(?:CID|ICD)[-\s]*[A-Z]?\d+(?:\.\d+)?\b', re.IGNORECASE),
            
            # Números de leitos/quartos
            'room_numbers': re.compile(r'\b(?:leito|quarto|sala)\s+\d+\b', re.IGNORECASE),
        }
        
        # Substituições para manter a estrutura semântica
        self.replacements: Dict[str, str] = {
            'names': 'paciente [NOME]',
            'cpf': 'cpf [CPF]',
            'rg': 'rg [RG]', 
            'patient_ids': 'paciente [ID]',
            'diagnoses': '[DIAGNOSTICO]',
            'medical_record': 'prontuário [NUMERO]',
            'dates': '[DATA]',
            'times': '[HORA]',
            'specific_numbers': '[VALOR]',
            'medications': 'medicamento [MEDICAMENTO]',
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
        """Padrões que indicam necessidade de busca híbrida (paciente + protocolo)"""
        return [
            # Padrões com identificadores específicos (foco principal)
            "dados do paciente [NOME]",
            "informações do paciente com cpf [CPF]", 
            "paciente com id [ID]",
            "buscar paciente [NOME]",
            "encontrar paciente com rg [RG]",
            "o paciente com cpf [CPF]",
            "paciente [NOME] tem",
            "orientações para o paciente [NOME]",
            "tratamento do paciente [ID]",
            
            # Padrões médicos específicos do paciente (apenas com identificadores)
            "alergias do paciente [NOME]",
            "histórico médico do paciente [ID]", 
            "medicamentos do paciente [CPF]",
            "diagnóstico do paciente [NOME]",
            "condições do paciente [RG]",
            "exames do paciente [ID]",
            
            # Padrões contextuais (referências específicas)
            "este paciente [NOME]",
            "o paciente em questão [ID]",
            "conforme dados do paciente [CPF]",
            "baseado no perfil do paciente [NOME]",
            "considerando o histórico do paciente [RG]",
            "protocolo para o paciente [NOME]",
            
            # Padrões de busca direta por paciente
            "quem é o paciente [NOME]",
            "mostrar paciente [CPF]",
            "localizar paciente [RG]",
            "verificar paciente [ID]",
        ]

# Singleton instance
query_normalizer = QueryNormalizer()