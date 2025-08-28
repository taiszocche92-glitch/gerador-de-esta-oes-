#!/usr/bin/env python3
"""
Teste do endpoint restaurado de geração individual
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append('.')

async def test_individual_generation():
    """Testa a função generate_single_station_internal diretamente"""
    try:
        print("🔥 TESTE: Endpoint de Geração Individual Restaurado")
        print("="*50)
        
        # Importar após adicionar ao path
        from main import generate_single_station_internal
        
        # Parâmetros de teste
        tema = "Hipertensão Arterial"
        especialidade = "Cardiologia"
        abordagem_id = "caso_clinico"
        enable_web_search = False
        
        print(f"📋 Tema: {tema}")
        print(f"🏥 Especialidade: {especialidade}")
        print(f"🔬 Abordagem: {abordagem_id}")
        print(f"🌐 Web Search: {enable_web_search}")
        print()
        
        # Executar geração
        print("⏳ Executando geração...")
        start_time = datetime.now()
        
        success, result, error_msg = await generate_single_station_internal(
            tema=tema,
            especialidade=especialidade,
            abordagem_id=abordagem_id,
            enable_web_search=enable_web_search
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Tempo total: {duration:.2f} segundos")
        print()
        
        if success:
            print("✅ GERAÇÃO BEM-SUCEDIDA!")
            print("-" * 30)
            print(f"🆔 Station ID: {result.get('station_id', 'N/A')}")
            print(f"✔️ Status de Validação: {result.get('validation_status', 'N/A')}")
            print(f"📁 Arquivo Local: {result.get('local_file', 'N/A')}")
            print(f"☁️ Firestore Sincronizado: {result.get('firestore_synced', False)}")
            
            # Verificar arquivo local
            local_file = result.get('local_file')
            if local_file and os.path.exists(local_file):
                print(f"\n📂 VERIFICAÇÃO DO ARQUIVO LOCAL:")
                print(f"   📄 Caminho: {local_file}")
                
                with open(local_file, 'r', encoding='utf-8') as f:
                    station_data = json.load(f)
                
                print(f"   📝 Título: {station_data.get('titulo', 'N/A')}")
                print(f"   🔗 Sync Status: {station_data.get('sync_status', 'N/A')}")
                print(f"   📅 Criado em: {station_data.get('created_at', 'N/A')}")
                print(f"   👤 Criado por: {station_data.get('created_by', 'N/A')}")
                print(f"   🔗 ID Firestore: {station_data.get('firestore_id', 'N/A')}")
                
                # Verificar estrutura da estação
                print(f"\n📊 ESTRUTURA DA ESTAÇÃO:")
                for key, value in station_data.items():
                    if key not in ['id', 'created_at', 'created_by', 'source', 'tema_original', 'especialidade_original', 'sync_status', 'firestore_id']:
                        if isinstance(value, (dict, list)):
                            print(f"   📦 {key}: {type(value).__name__} ({len(value)} itens)")
                        else:
                            print(f"   📄 {key}: {type(value).__name__}")
                
                print(f"\n💾 Tamanho do arquivo: {os.path.getsize(local_file)} bytes")
            else:
                print("❌ ARQUIVO LOCAL NÃO ENCONTRADO!")
            
            # Listar arquivos na pasta estacoes_geradas
            print(f"\n📁 ARQUIVOS EM estacoes_geradas/:")
            estacoes_dir = "estacoes_geradas"
            if os.path.exists(estacoes_dir):
                files = [f for f in os.listdir(estacoes_dir) if f.endswith('.json')]
                print(f"   📊 Total de arquivos: {len(files)}")
                for i, file in enumerate(files[-5:], 1):  # Últimos 5 arquivos
                    print(f"   {i}. {file}")
                if len(files) > 5:
                    print(f"   ... e mais {len(files) - 5} arquivos")
            else:
                print("   ❌ Pasta estacoes_geradas não encontrada!")
            
        else:
            print("❌ FALHA NA GERAÇÃO!")
            print("-" * 30)
            print(f"💥 Erro: {error_msg}")
            
    except Exception as e:
        print(f"💥 ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Iniciando teste...")
    asyncio.run(test_individual_generation())
    print("\nTeste concluído!")
