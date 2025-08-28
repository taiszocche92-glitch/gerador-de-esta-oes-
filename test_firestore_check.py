import json
from main import db

if db:
    try:
        # Buscar pela estação no Firestore usando o ID do Firestore
        firestore_id = 'oVsSJf1bjTpEnlTaT3dt'
        doc_ref = db.collection('estacoes_clinicas').document(firestore_id)
        doc = doc_ref.get()
        
        if doc.exists:
            print('✅ ESTAÇÃO ENCONTRADA NO FIRESTORE!')
            print(f'🆔 Firestore ID: {firestore_id}')
            data = doc.to_dict()
            print(f'📝 Título: {data.get("tituloEstacao", "N/A")}')
            print(f'🏥 Especialidade: {data.get("especialidade", "N/A")}')
            print(f'🔗 Tem firestore_id nos dados: {"firestore_id" in data}')
            if 'id' in data:
                print(f'📋 ID local salvo: {data["id"]}')
            print('')
            print('🔍 VERIFICANDO IDs:')
            print(f'   - Firestore ID (real): {firestore_id}')
            print(f'   - UUID local: {data.get("id", "N/A")}')
        else:
            print(f'❌ Estação não encontrada no Firestore com ID: {firestore_id}')
            
    except Exception as e:
        print(f'💥 Erro ao buscar: {e}')
else:
    print('❌ Firebase não conectado')
