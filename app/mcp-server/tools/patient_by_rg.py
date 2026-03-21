"""
Tool para buscar dados de paciente por RG.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.types import Tool


def get_patient_by_rg_tool() -> Tool:
    """
    Define a tool para buscar paciente por RG.
    
    Returns:
        Tool: Ferramenta configurada para busca por RG
    """
    return Tool(
        name="get_patient_by_rg",
        description="Busca dados de um paciente pelo RG (Registro Geral). "
                   "Aceita RG com ou sem máscara e diferentes formatos estaduais. "
                   "Exemplos: 'MG-12.345.678', '12345678', 'SP-98.765.432'",
        inputSchema={
            "type": "object",
            "properties": {
                "rg": {
                    "type": "string",
                    "description": "RG do paciente. Pode ser informado com ou sem máscara. "
                                 "Aceita diferentes formatos estaduais. "
                                 "Exemplos: 'MG-12.345.678', '12345678', 'SP-98.765.432'"
                }
            },
            "required": ["rg"]
        }
    )


def normalize_rg(rg: str) -> str:
    """
    Normaliza o RG removendo pontos, hífens e deixando apenas UF e números.
    
    Args:
        rg (str): RG com ou sem máscara
        
    Returns:
        str: RG normalizado (formato: UF + números)
    """
    # Remove pontos e hífens, mas mantém letras (UF)
    normalized = re.sub(r'[.\-]', '', rg.upper())
    return normalized


def validate_rg(rg: str) -> bool:
    """
    Valida se o RG tem formato básico correto.
    
    Args:
        rg (str): RG normalizado
        
    Returns:
        bool: True se tem formato válido, False caso contrário
    """
    # Verifica se tem pelo menos 2 letras (UF) seguidas de números
    pattern = r'^[A-Z]{2}[0-9]+$'
    return bool(re.match(pattern, rg)) and len(rg) >= 4


def execute_get_patient_by_rg(rg: str) -> Optional[Dict[str, Any]]:
    """
    Executa a busca de paciente por RG.
    
    Args:
        rg (str): RG do paciente (com ou sem máscara)
        
    Returns:
        Optional[Dict[str, Any]]: Dados do paciente encontrado ou None
        
    Raises:
        ValueError: Se o RG for inválido
        FileNotFoundError: Se o arquivo de dados não for encontrado
        json.JSONDecodeError: Se o arquivo JSON for inválido
    """
    try:
        # Normaliza o RG
        normalized_rg = normalize_rg(rg)
        
        # Valida o RG
        if not validate_rg(normalized_rg):
            raise ValueError("RG deve conter UF (2 letras) seguida de números. Exemplo: 'MG12345678'")
        
        # Caminho para o arquivo de dados
        data_path = Path(__file__).parent.parent / "data" / "mock_patients.json"
        
        # Carrega os dados dos pacientes
        with open(data_path, 'r', encoding='utf-8') as file:
            patients = json.load(file)
        
        # Busca pelo RG
        for patient in patients:
            patient_rg = normalize_rg(patient.get('rg', ''))
            if patient_rg == normalized_rg:
                return patient
        
        return None
        
    except ValueError:
        raise
    except FileNotFoundError:
        raise FileNotFoundError("Arquivo de dados de pacientes não encontrado")
    except json.JSONDecodeError:
        raise json.JSONDecodeError("Erro ao decodificar arquivo JSON de pacientes")
    except Exception as e:
        raise Exception(f"Erro inesperado ao buscar paciente: {str(e)}")


def format_patient_response(patient: Optional[Dict[str, Any]], rg_searched: str) -> str:
    """
    Formata a resposta da busca de paciente.
    
    Args:
        patient (Optional[Dict[str, Any]]): Dados do paciente encontrado ou None
        rg_searched (str): RG que foi pesquisado
        
    Returns:
        str: Resposta formatada
    """
    if not patient:
        return f"Nenhum paciente encontrado com o RG: {rg_searched}"
    
    return f"""**Paciente Encontrado:**

**Dados Pessoais:**
- ID: {patient.get('id', 'N/A')}
- Nome: {patient.get('nome', 'N/A')}
- CPF: {patient.get('cpf', 'N/A')}
- RG: {patient.get('rg', 'N/A')}
- Data de Nascimento: {patient.get('data_nascimento', 'N/A')}
- Tipo Sanguíneo: {patient.get('tipo_sanguineo', 'N/A')}

**Informações Médicas:**
- Alergias: {', '.join(patient.get('alergias', [])) or 'Nenhuma'}
- Doenças: {', '.join(patient.get('doenças', [])) or 'Nenhuma'}
- Medicamentos em Uso: {', '.join(patient.get('medicamentos_em_uso', [])) or 'Nenhum'}
- Histórico Familiar: {', '.join(patient.get('historico_familiar', [])) or 'Nenhum'}"""