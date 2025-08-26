# test_endpoints.py
"""
Testes automatizados dos principais endpoints do backend.
Execute em um terminal separado para não afetar o backend principal.
"""
import requests
import time
import json

BASE_URL = 'http://localhost:8080'
TIMEOUT = 10  # segundos
MAX_RETRIES = 3

import requests
import time
import json

BASE_URL = 'http://localhost:8080'
TIMEOUT = 10  # segundos
MAX_RETRIES = 3

def check_server_ready():
    """Verifica se o servidor está respondendo antes dos testes."""
    for _ in range(MAX_RETRIES):
        try:
            response = requests.get(f"{BASE_URL}/docs", timeout=2)
            if response.status_code == 200:
                return True
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(2)
    return False

# --------------------------------------------------
# Testes da API de Criação de Estações
# --------------------------------------------------

def test_start_creation():
    """Testa o endpoint /api/agent/start-creation."""
    if not check_server_ready():
        raise ConnectionError("Servidor não está respondendo")
    
    url = f"{BASE_URL}/api/agent/start-creation"
    payload = {
        "tema": "Cardiologia",
        "especialidade": "Clínica Médica"
    }
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        assert 'process_id' in data, "Resposta deve conter process_id"
        print('✅ start-creation OK')
    except requests.exceptions.RequestException as e:
        print(f'❌ Erro em start-creation: {str(e)}')
        raise

# --------------------------------------------------
# Testes da API de Geração de Estações
# --------------------------------------------------

def validate_station_response(data):
    """Valida a estrutura básica da resposta da estação."""
    required_fields = {
        'resumo_clinico', 'proposta_escolhida',
        'tema', 'especialidade', 'elementos_estacao'
    }
    assert all(field in data for field in required_fields), "Campos obrigatórios faltando"
    assert isinstance(data['elementos_estacao'], list), "Elementos deve ser uma lista"

def test_generate_final_station():
    """Testa o endpoint /api/agent/generate-final-station."""
    url = f"{BASE_URL}/api/agent/generate-final-station"
    payload = {
        "resumo_clinico": "Paciente com dor torácica...",
        "proposta_escolhida": "Proposta 1",
        "tema": "Cardiologia",
        "especialidade": "Clínica Médica"
    }
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        validate_station_response(data)
        print('✅ generate-final-station OK')
    except requests.exceptions.RequestException as e:
        print(f'❌ Erro em generate-final-station: {str(e)}')
        raise

# --------------------------------------------------
# Testes da API de Análise de Estações
# --------------------------------------------------

def test_analyze_station():
    """Testa o endpoint /api/agent/analyze-station."""
    url = f"{BASE_URL}/api/agent/analyze-station"
    payload = {
        "station_json": {
            "tema": "Cardiologia",
            "elementos": ["anamnese", "exame_físico"]
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        assert 'analise' in data, "Resposta deve conter análise"
        assert 'sugestoes' in data, "Resposta deve conter sugestões"
        print('✅ analyze-station OK')
    except requests.exceptions.RequestException as e:
        print(f'❌ Erro em analyze-station: {str(e)}')
        raise

# --------------------------------------------------
# Testes da API de Auditoria de Estações
# --------------------------------------------------

def test_apply_audit():
    """Testa o endpoint /api/agent/apply-audit."""
    url = f"{BASE_URL}/api/agent/apply-audit"
    payload = {
        "station_json": {
            "tema": "Cardiologia",
            "elementos": ["anamnese", "exame_físico"]
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        assert 'auditoria' in data, "Resposta deve conter auditoria"
        assert 'pontos_melhoria' in data, "Resposta deve conter pontos de melhoria"
        print('✅ apply-audit OK')
    except requests.exceptions.RequestException as e:
        print(f'❌ Erro em apply-audit: {str(e)}')
        raise

# --------------------------------------------------
# Testes da API do Gemini
# --------------------------------------------------

def test_test_gemini():
    """Testa o endpoint /api/test-gemini."""
    url = f"{BASE_URL}/api/test-gemini"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        assert 'status' in data and data['status'] == 'operacional', "Status do Gemini inválido"
        print('✅ test-gemini OK')
    except requests.exceptions.RequestException as e:
        print(f'❌ Erro em test-gemini: {str(e)}')
        raise

# --------------------------------------------------
# Execução dos Testes
# --------------------------------------------------

if __name__ == "__main__":
    if check_server_ready():
        test_start_creation()
        test_generate_final_station()
        test_analyze_station()
        test_apply_audit()
        test_test_gemini()
    else:
        print("❌ Servidor não está respondendo. Execute o servidor primeiro.")
