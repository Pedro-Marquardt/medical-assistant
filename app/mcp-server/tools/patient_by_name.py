"""
Tool para buscar dados de paciente por nome.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.types import Tool


def get_patient_by_name_tool() -> Tool:
    """
    Define a tool para buscar paciente por nome.
    
    Returns:
        Tool: Ferramenta configurada para busca por nome
    """
    return Tool(
        name="get_patient_by_name",
        description="Busca dados de um paciente pelo nome completo ou parcial. "
                   "A busca é case-insensitive e permite busca parcial.",
        inputSchema={
            "type": "object",
            "properties": {
                "nome": {
                    "type": "string",
                    "description": "Nome completo ou parcial do paciente para busca. "
                                 "A busca é case-insensitive e permite correspondência parcial."
                }
            },
            "required": ["nome"]
        }
    )


def execute_get_patient_by_name(nome: str) -> List[Dict[str, Any]]:
    """
    Executa a busca de paciente por nome.
    
    Args:
        nome (str): Nome do paciente (busca parcial case-insensitive)
        
    Returns:
        List[Dict[str, Any]]: Lista de pacientes encontrados
        
    Raises:
        FileNotFoundError: Se o arquivo de dados não for encontrado
        json.JSONDecodeError: Se o arquivo JSON for inválido
    """
    try:
        # Caminho para o arquivo de dados
        data_path = Path(__file__).parent.parent / "data" / "mock_patients.json"
        
        # Carrega os dados dos pacientes
        with open(data_path, 'r', encoding='utf-8') as file:
            patients = json.load(file)
        
        # Busca case-insensitive e permite busca parcial
        nome_lower = nome.lower()
        found_patients = []
        
        for patient in patients:
            patient_name = patient.get('nome', '').lower()
            if nome_lower in patient_name:
                found_patients.append(patient)
        
        return found_patients
        
    except FileNotFoundError:
        raise FileNotFoundError("Arquivo de dados de pacientes não encontrado")
    except json.JSONDecodeError:
        raise json.JSONDecodeError("Erro ao decodificar arquivo JSON de pacientes")
    except Exception as e:
        raise Exception(f"Erro inesperado ao buscar paciente: {str(e)}")


def format_patient_response(patients: List[Dict[str, Any]]) -> str:
    """
    Formata a resposta da busca de pacientes.
    
    Args:
        patients (List[Dict[str, Any]]): Lista de pacientes encontrados
        
    Returns:
        str: Resposta formatada
    """
    if not patients:
        return "Nenhum paciente encontrado com este nome."
    
    if len(patients) == 1:
        patient = patients[0]
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
    
    # Múltiplos pacientes encontrados
    response = f"**{len(patients)} Pacientes Encontrados:**\n\n"
    for i, patient in enumerate(patients, 1):
        response += f"**{i}. {patient.get('nome', 'N/A')}**\n"
        response += f"   - ID: {patient.get('id', 'N/A')}\n"
        response += f"   - CPF: {patient.get('cpf', 'N/A')}\n"
        response += f"   - Data de Nascimento: {patient.get('data_nascimento', 'N/A')}\n\n"
    
    return response