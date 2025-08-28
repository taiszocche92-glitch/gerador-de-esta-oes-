#!/usr/bin/env python3
"""
Teste simples para verificar as variáveis de ambiente do Gemini
"""
import os

print("🔍 Verificando variáveis de ambiente do Gemini...")
print("=" * 50)

# Lista de variáveis para verificar
env_vars = [
    "GOOGLE_API_KEY",
    "GOOGLE_API_KEY_1", 
    "GOOGLE_API_KEY_2",
    "GOOGLE_API_KEY_3", 
    "GOOGLE_API_KEY_4",
    "GOOGLE_API_KEY_5",
    "GEMINI_API_KEY_1",
    "GEMINI_API_KEY_2",
    "GEMINI_API_KEY_3",
    "GEMINI_API_KEY_4"
]

valid_keys = []

for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mascarar a chave para segurança 
        masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***CURTA***"
        print(f"✅ {var}: {masked}")
        valid_keys.append(var)
    else:
        print(f"❌ {var}: NÃO CONFIGURADA")

print("=" * 50)
print(f"📊 RESUMO: {len(valid_keys)} chaves válidas encontradas")

if valid_keys:
    print("✅ Chaves disponíveis:", valid_keys)
else:
    print("❌ NENHUMA CHAVE CONFIGURADA!")
    print("💡 Configure as variáveis de ambiente GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.")

# Testar também a configuração do Gemini
print("\n🧪 Testando configuração do Gemini...")
try:
    from main import GEMINI_CONFIGS, configure_gemini_keys
    
    print("🔧 Configurando chaves do Gemini...")
    configure_gemini_keys()
    
    print(f"📋 GEMINI_CONFIGS keys: {list(GEMINI_CONFIGS.keys())}")
    
    for model_type, configs in GEMINI_CONFIGS.items():
        print(f"🔑 {model_type}: {len(configs)} configurações")
        
    if GEMINI_CONFIGS.get('all'):
        print("✅ Sistema Gemini configurado corretamente!")
    else:
        print("❌ Sistema Gemini NÃO configurado!")
        
except Exception as e:
    print(f"❌ Erro ao testar configuração: {e}")
    import traceback
    traceback.print_exc()
