"""
Tool para buscar dados de paciente por ID.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.types import Tool


def get_patient_by_id_tool() -> Tool:
    """
    Define a tool para buscar paciente por ID.
    
    Returns:
        Tool: Ferramenta configurada para busca por ID
    """
    return Tool(
        name="get_patient_by_id",
        description="Busca dados de um paciente pelo ID único do sistema. "
                   "O ID é um identificador único no formato 'PAC-XXX' onde XXX são 3 dígitos. "
                   "Exemplo: 'PAC-001', 'PAC-002'",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID único do paciente no formato 'PAC-XXX'. "
                                 "Exemplo: 'PAC-001', 'PAC-002'"
                }
            },
            "required": ["id"]
        }
    )


def normalize_id(patient_id: str) -> str:
    """
    Normaliza o ID do paciente (converte para maiúsculo).
    
    Args:
        patient_id (str): ID do paciente
        
    Returns:
        str: ID normalizado
    """
    return patient_id.upper().strip()


def validate_id(patient_id: str) -> bool:
    """
    Valida se o ID tem formato correto (PAC-XXX).
    
    Args:
        patient_id (str): ID do paciente normalizado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    import re
    pattern = r'^PAC-\d{3}$'
    return bool(re.match(pattern, patient_id))


def execute_get_patient_by_id(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Executa a busca de paciente por ID.
    
    Args:
        patient_id (str): ID do paciente
        
    Returns:
        Optional[Dict[str, Any]]: Dados do paciente encontrado ou None
        
    Raises:
        ValueError: Se o ID for inválido
        FileNotFoundError: Se o arquivo de dados não for encontrado
        json.JSONDecodeError: Se o arquivo JSON for inválido
    """
    try:
        # Normaliza o ID
        normalized_id = normalize_id(patient_id)
        
        # Valida o ID
        if not validate_id(normalized_id):
            raise ValueError("ID deve estar no formato 'PAC-XXX' onde XXX são 3 dígitos. Exemplo: 'PAC-001'")
        
        # Caminho para o arquivo de dados
        data_path = Path(__file__).parent.parent / "data" / "mock_patients.json"
        
        # Carrega os dados dos pacientes
        with open(data_path, 'r', encoding='utf-8') as file:
            patients = json.load(file)
        
        # Busca pelo ID
        for patient in patients:
            if patient.get('id', '').upper() == normalized_id:
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


def format_patient_response(patient: Optional[Dict[str, Any]], id_searched: str) -> str:
    """
    Formata a resposta da busca de paciente.
    
    Args:
        patient (Optional[Dict[str, Any]]): Dados do paciente encontrado ou None
        id_searched (str): ID que foi pesquisado
        
    Returns:
        str: Resposta formatada
    """
    if not patient:
        return f"Nenhum paciente encontrado com o ID: {id_searched}"
    
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