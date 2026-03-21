"""
Tool para buscar dados de paciente por CPF.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.types import Tool


def get_patient_by_cpf_tool() -> Tool:
    """
    Define a tool para buscar paciente por CPF.
    
    Returns:
        Tool: Ferramenta configurada para busca por CPF
    """
    return Tool(
        name="get_patient_by_cpf",
        description="Busca dados de um paciente pelo CPF. "
                   "Aceita CPF com ou sem máscara (pontos e hífen). "
                   "Exemplo: '123.456.789-00' ou '12345678900'",
        inputSchema={
            "type": "object",
            "properties": {
                "cpf": {
                    "type": "string",
                    "description": "CPF do paciente. Pode ser informado com ou sem máscara. "
                                 "Exemplos: '123.456.789-00', '12345678900'"
                }
            },
            "required": ["cpf"]
        }
    )


def normalize_cpf(cpf: str) -> str:
    """
    Normaliza o CPF removendo caracteres não numéricos.
    
    Args:
        cpf (str): CPF com ou sem máscara
        
    Returns:
        str: CPF apenas com números
    """
    return re.sub(r'[^0-9]', '', cpf)


def format_cpf(cpf: str) -> str:
    """
    Formata o CPF com máscara.
    
    Args:
        cpf (str): CPF sem máscara
        
    Returns:
        str: CPF formatado (000.000.000-00)
    """
    if len(cpf) != 11:
        return cpf
    
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def validate_cpf(cpf: str) -> bool:
    """
    Valida se o CPF tem formato correto (11 dígitos numéricos).
    
    Args:
        cpf (str): CPF normalizado
        
    Returns:
        bool: True se válido, False caso contrário
    """
    return len(cpf) == 11 and cpf.isdigit()


def execute_get_patient_by_cpf(cpf: str) -> Optional[Dict[str, Any]]:
    """
    Executa a busca de paciente por CPF.
    
    Args:
        cpf (str): CPF do paciente (com ou sem máscara)
        
    Returns:
        Optional[Dict[str, Any]]: Dados do paciente encontrado ou None
        
    Raises:
        ValueError: Se o CPF for inválido
        FileNotFoundError: Se o arquivo de dados não for encontrado
        json.JSONDecodeError: Se o arquivo JSON for inválido
    """
    try:
        # Normaliza o CPF
        normalized_cpf = normalize_cpf(cpf)
        
        # Valida o CPF
        if not validate_cpf(normalized_cpf):
            raise ValueError("CPF deve conter exatamente 11 dígitos numéricos")
        
        # Caminho para o arquivo de dados
        data_path = Path(__file__).parent.parent / "data" / "mock_patients.json"
        
        # Carrega os dados dos pacientes
        with open(data_path, 'r', encoding='utf-8') as file:
            patients = json.load(file)
        
        # Busca pelo CPF
        for patient in patients:
            patient_cpf = normalize_cpf(patient.get('cpf', ''))
            if patient_cpf == normalized_cpf:
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


def format_patient_response(patient: Optional[Dict[str, Any]], cpf_searched: str) -> str:
    """
    Formata a resposta da busca de paciente.
    
    Args:
        patient (Optional[Dict[str, Any]]): Dados do paciente encontrado ou None
        cpf_searched (str): CPF que foi pesquisado
        
    Returns:
        str: Resposta formatada
    """
    if not patient:
        normalized_cpf = normalize_cpf(cpf_searched)
        formatted_cpf = format_cpf(normalized_cpf)
        return f"Nenhum paciente encontrado com o CPF: {formatted_cpf}"
    
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