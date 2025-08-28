import os
from dotenv import load_dotenv

print('🔍 Testando carregamento de variáveis de ambiente...')
print('')

# Carregar como no main.py
load_dotenv()  # Carrega .env da pasta atual (se existir)
load_dotenv('../.env')  # Carrega .env da pasta pai (projeto principal)

print('📋 Verificando chaves do Gemini:')
for i in range(1, 6):
    key_name = f'GOOGLE_API_KEY_{i}'
    key_value = os.getenv(key_name)
    if key_value:
        print(f'  ✅ {key_name}: {key_value[:20]}...')
    else:
        print(f'  ❌ {key_name}: Não encontrada')

print('')
print('🚀 Testando configuração do Gemini:')

# Simular a configuração como no main.py
GEMINI_CONFIGS = {
    'api_keys': [],
    'current_key_index': 0,
    'all': []
}

gemini_keys = []
for i in range(1, 6):
    key = os.getenv(f'GOOGLE_API_KEY_{i}')
    if key and key.strip():
        gemini_keys.append(key.strip())

GEMINI_CONFIGS['api_keys'] = gemini_keys
GEMINI_CONFIGS['all'] = gemini_keys

print(f'📊 Total de chaves carregadas: {len(GEMINI_CONFIGS["api_keys"])}')
if len(GEMINI_CONFIGS['api_keys']) > 0:
    print(f'🔑 Primeira chave: {GEMINI_CONFIGS["api_keys"][0][:20]}...')

if GEMINI_CONFIGS.get('all'):
    print('✅ GEMINI_CONFIGS["all"] está populado!')
else:
    print('❌ GEMINI_CONFIGS["all"] está vazio!')
