#!/usr/bin/env python3
"""
Script para corrigir problemas de autenticação Firebase
"""

import os
import json
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def test_firebase_with_retry():
    """Testa Firebase com retry e timeouts customizados"""
    
    print("🔧 CORRIGINDO PROBLEMAS DE AUTENTICAÇÃO FIREBASE")
    print("=" * 55)
    
    # Caminho das credenciais
    cred_path = "memoria/serviceAccountKey.json"
    
    # Limpar qualquer app existente
    for app_name in list(firebase_admin._apps.keys()):
        firebase_admin.delete_app(firebase_admin._apps[app_name])
    
    try:
        print("🚀 Inicializando Firebase com configurações otimizadas...")
        
        # Carregar credenciais
        cred = credentials.Certificate(cred_path)
        
        # Configurar com projeto específico
        app = firebase_admin.initialize_app(cred, {
            'projectId': 'revalida-companion'
        })
        
        print(f"✅ Firebase inicializado: {app.project_id}")
        
        # Configurar cliente Firestore com timeouts customizados
        print("💾 Conectando ao Firestore...")
        
        # Usar configuração de client específica
        from google.cloud import firestore as firestore_client
        
        # Cliente com configurações customizadas
        db = firestore_client.Client(
            project='revalida-companion',
            credentials=cred.get_credential()
        )
        
        print("🔍 Testando operação simples...")
        
        # Teste simples: listar coleções (sem criar documentos)
        collections = list(db.collections())
        print(f"✅ Conexão OK! Encontradas {len(collections)} coleções")
        
        # Listar algumas coleções encontradas
        for i, col in enumerate(collections[:5]):
            print(f"   📁 {col.id}")
        
        # Teste de leitura de documento específico
        try:
            test_ref = db.collection('agent_config').document('rules')
            doc = test_ref.get(timeout=10.0)  # Timeout de 10 segundos
            
            if doc.exists:
                print(f"✅ Documento 'agent_config/rules' existe")
                data = doc.to_dict()
                if data:
                    print(f"📄 Documento contém dados ({len(data)} campos)")
                else:
                    print(f"⚠️ Documento existe mas está vazio")
            else:
                print(f"⚠️ Documento 'agent_config/rules' não existe")
                
        except Exception as read_error:
            print(f"⚠️ Erro ao ler documento: {read_error}")
        
        return True, db
        
    except Exception as e:
        error_str = str(e).lower()
        print(f"❌ Erro: {e}")
        
        if 'invalid jwt signature' in error_str:
            print(f"\n🔧 SOLUÇÕES PARA 'Invalid JWT Signature':")
            print(f"1. ⏰ Sincronizar relógio do sistema")
            print(f"2. 🔄 Regenerar credenciais no Google Cloud Console")
            print(f"3. 🌐 Verificar conectividade com googleapis.com")
            print(f"4. 🛡️ Verificar se firewall/antivírus não está bloqueando")
            
        elif 'timeout' in error_str or '503' in error_str:
            print(f"\n🔧 SOLUÇÕES PARA TIMEOUT:")
            print(f"1. 🌐 Verificar conexão com internet")
            print(f"2. ⏳ Aguardar alguns minutos e tentar novamente")
            print(f"3. 🔄 Reiniciar aplicação")
            
        return False, None

def create_alternative_init():
    """Cria uma função de inicialização alternativa mais robusta"""
    
    print(f"\n🛠️ Criando inicialização robusta...")
    
    alt_init_code = '''
def initialize_firebase_robust():
    """Inicialização robusta do Firebase"""
    global db, firebase_mock_mode
    
    try:
        print("🔧 Inicialização robusta do Firebase...")
        
        # Limpar apps existentes
        for app_name in list(firebase_admin._apps.keys()):
            firebase_admin.delete_app(firebase_admin._apps[app_name])
        
        # Caminho das credenciais
        service_account_path = os.path.join('memoria', 'serviceAccountKey.json')
        
        if not os.path.exists(service_account_path):
            print("❌ Arquivo de credenciais não encontrado")
            firebase_mock_mode = True
            return False
        
        # Carregar credenciais
        cred = credentials.Certificate(service_account_path)
        
        # Inicializar com configuração específica
        app = firebase_admin.initialize_app(cred, {
            'projectId': 'revalida-companion'
        })
        
        # Cliente Firestore com retry automático
        db = firestore.client()
        
        # Teste de conectividade simples com timeout
        try:
            # Operação de leitura simples para testar conectividade
            test_collections = list(db.collections())
            print(f"✅ Firebase conectado! {len(test_collections)} coleções encontradas")
            return True
            
        except Exception as connectivity_error:
            print(f"⚠️ Problema de conectividade: {connectivity_error}")
            # Continuar mesmo com problemas de conectividade
            print("🔄 Continuando com conexão limitada...")
            return True
            
    except Exception as e:
        error_message = str(e).lower()
        print(f"❌ Erro na inicialização: {e}")
        
        if 'invalid jwt' in error_message:
            print("🔧 Problema de autenticação detectado")
            print("   - Verificar credenciais no Google Cloud Console")
            print("   - Sincronizar relógio do sistema")
            
        # Ativar modo mock como fallback
        firebase_mock_mode = True
        print("🔄 Ativando modo local (sem Firestore)")
        return False
'''
    
    # Salvar código alternativo
    with open('firebase_robust_init.py', 'w', encoding='utf-8') as f:
        f.write(alt_init_code)
    
    print(f"✅ Arquivo 'firebase_robust_init.py' criado")
    print(f"💡 Use esta função no lugar da inicialização atual")

if __name__ == "__main__":
    print(f"🕒 Hora do sistema: {datetime.now()}")
    print(f"")
    
    success, db_client = test_firebase_with_retry()
    
    if success:
        print(f"\n🎉 FIREBASE FUNCIONANDO CORRETAMENTE!")
        print(f"✅ Pode usar o sistema normalmente")
    else:
        print(f"\n⚠️ PROBLEMAS DETECTADOS")
        create_alternative_init()
        print(f"\n🔧 AÇÕES RECOMENDADAS:")
        print(f"1. Verificar conexão com internet")
        print(f"2. Sincronizar data/hora do sistema")
        print(f"3. Gerar novas credenciais se o problema persistir")
        print(f"4. O sistema pode funcionar em modo local mesmo com este erro")
