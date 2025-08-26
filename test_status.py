#!/usr/bin/env python3
"""
Teste simples para verificar status do backend
"""
import requests
import json

def test_backend():
    try:
        print("🧪 Testando backend Python...")
        
        # Teste 1: Health check
        response = requests.get("http://127.0.0.1:8080/health", timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        
        # Teste 2: Verificar se regras estão carregadas
        test_data = {
            "tema": "Teste",
            "especialidade": "Clínica Médica",
            "enable_web_search": "0"
        }
        
        response = requests.post(
            "http://127.0.0.1:8080/api/agent/start-creation",
            data=test_data,
            timeout=10
        )
        
        print(f"Agent test: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            print("✅ Sistema funcionando!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_backend()
