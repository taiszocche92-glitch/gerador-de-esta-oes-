import asyncio
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
load_dotenv('../.env')

async def test_skip_firestore():
    from main import generate_single_station_internal
    
    print('🧪 Testando geração com skip_firestore=True...')
    print('')
    
    # Testar com skip_firestore=True (como na geração múltipla)
    success, result, error_msg = await generate_single_station_internal(
        tema='Diabetes Mellitus Type 2',
        especialidade='Endocrinologia',
        abordagem_id='caso_clinico',
        enable_web_search=False,
        skip_firestore=True  # NOVO PARÂMETRO
    )
    
    if success:
        print('✅ SUCESSO na geração!')
        print(f'🆔 Station ID: {result.get("station_id", "N/A")}')
        print(f'📁 Arquivo local: {result.get("local_file", "N/A")}')
        print(f'☁️ Firestore sincronizado: {result.get("firestore_synced", "N/A")}')
        print(f'✔️ Status validação: {result.get("validation_status", "N/A")}')
        
        # Verificar se o arquivo local existe
        if 'local_file' in result and os.path.exists(result['local_file']):
            print(f'📂 Arquivo local confirmado!')
            
            # Verificar se foi salvo apenas localmente
            import json
            with open(result['local_file'], 'r', encoding='utf-8') as f:
                data = json.load(f)
                sync_status = data.get('sync_status', 'unknown')
                print(f'🔗 Sync Status: {sync_status}')
                
                if sync_status == 'local_only':
                    print('✅ PERFEITO! Firestore foi pulado como esperado.')
                else:
                    print('❌ ERRO! Deveria ser local_only mas foi:', sync_status)
        else:
            print('❌ Arquivo local não encontrado!')
    else:
        print(f'❌ ERRO na geração: {error_msg}')

if __name__ == "__main__":
    asyncio.run(test_skip_firestore())
