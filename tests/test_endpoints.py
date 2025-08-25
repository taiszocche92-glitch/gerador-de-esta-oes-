# test_endpoints.py
"""
Testes automatizados dos principais endpoints do backend.
Execute em um terminal separado para não afetar o backend principal.
"""
import requests

BASE_URL = 'http://localhost:8080'

def test_start_creation():
    url = f"{BASE_URL}/api/agent/start-creation"
    payload = {
        "tema": "Cardiologia",
        "especialidade": "Clínica Médica"
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    print('start-creation OK:', response.json())

def test_generate_final_station():
    url = f"{BASE_URL}/api/agent/generate-final-station"
    payload = {
        "resumo_clinico": "Paciente com dor torácica...",
        "proposta_escolhida": "Proposta 1",
        "tema": "Cardiologia",
        "especialidade": "Clínica Médica"
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    print('generate-final-station OK:', response.json())

def test_analyze_station():
    url = f"{BASE_URL}/api/agent/analyze-station"
    payload = {
        "station_json": {"campo": "valor"}
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    print('analyze-station OK:', response.json())

def test_apply_audit():
    url = f"{BASE_URL}/api/agent/apply-audit"
    payload = {
        "station_json": {"campo": "valor"}
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    print('apply-audit OK:', response.json())

def test_test_gemini():
    url = f"{BASE_URL}/api/test-gemini"
    response = requests.get(url)
    assert response.status_code == 200
    print('test-gemini OK:', response.json())

if __name__ == "__main__":
    test_start_creation()
    test_generate_final_station()
    test_analyze_station()
    test_apply_audit()
    test_test_gemini()
