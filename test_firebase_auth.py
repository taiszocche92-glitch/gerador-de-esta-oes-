#!/usr/bin/env python3
"""
Script para diagnosticar problemas de autenticação Firebase
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import sys

def test_firebase_connection():
    """Testa a conexão com Firebase e diagnóstica problemas"""
    
    print("🔍 DIAGNÓSTICO DE AUTENTICAÇÃO FIREBASE")
    print("=" * 50)
    
    # 1. Verificar arquivo de credenciais
    credentials_path = r"D:\Site arquivos\Projeto vs code\meuapp\backend-python-agent\memoria\serviceAccountKey.json"
    
    print(f"📄 Verificando arquivo de credenciais...")
    print(f"   Caminho: {credentials_path}")
    
    if not os.path.exists(credentials_path):
        print(f"❌ Arquivo de credenciais não encontrado!")
        return False
    
    print(f"✅ Arquivo encontrado")
    
    # 2. Verificar estrutura do JSON
    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            cred_data = json.load(f)
        
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        print(f"🔧 Verificando estrutura do JSON...")
        for field in required_fields:
            if field in cred_data:
                if field == 'private_key':
                    print(f"   ✅ {field}: [PRESENTE - {len(cred_data[field])} caracteres]")
                else:
                    print(f"   ✅ {field}: {cred_data[field]}")
            else:
                print(f"   ❌ {field}: AUSENTE")
                
        # 3. Verificar project_id
        project_id = cred_data.get('project_id')
        if project_id:
            print(f"📊 Project ID: {project_id}")
        
        # 4. Verificar chave privada
        private_key = cred_data.get('private_key', '')
        if private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print(f"🔑 Chave privada parece válida")
        else:
            print(f"❌ Chave privada tem formato inválido")
            
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False
    
    # 5. Testar inicialização do Firebase
    print(f"\n🚀 Testando inicialização do Firebase...")
    
    try:
        # Limpar apps existentes
        for app in firebase_admin._apps.values():
            firebase_admin.delete_app(app)
        
        # Inicializar com credenciais
        cred = credentials.Certificate(credentials_path)
        app = firebase_admin.initialize_app(cred)
        
        print(f"✅ Firebase inicializado com sucesso!")
        print(f"   App name: {app.name}")
        print(f"   Project ID: {app.project_id}")
        
        # 6. Testar conexão com Firestore
        print(f"\n💾 Testando conexão com Firestore...")
        
        db = firestore.client()
        
        # Tentar uma operação simples
        test_doc = db.collection('_test').document('connection_test')
        test_doc.set({
            'timestamp': datetime.now().isoformat(),
            'test': 'Firebase connection successful',
            'status': 'ok'
        })
        
        print(f"✅ Conexão com Firestore OK!")
        
        # Limpar documento de teste
        test_doc.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        
        # Diagnósticos específicos
        error_str = str(e).lower()
        if 'invalid jwt signature' in error_str:
            print(f"\n🔍 DIAGNÓSTICO ESPECÍFICO - Invalid JWT Signature:")
            print(f"   - Possível relógio do sistema dessincronizado")
            print(f"   - Chave privada pode estar corrompida")
            print(f"   - Credenciais podem ter sido revogadas")
            print(f"   - Problema de conectividade com servidores Google")
            
        elif 'permission denied' in error_str:
            print(f"\n🔍 DIAGNÓSTICO ESPECÍFICO - Permission Denied:")
            print(f"   - Service account pode não ter permissões adequadas")
            print(f"   - Project ID pode estar incorreto")
            
        elif 'project not found' in error_str:
            print(f"\n🔍 DIAGNÓSTICO ESPECÍFICO - Project Not Found:")
            print(f"   - Project ID incorreto: {project_id}")
            print(f"   - Projeto pode ter sido deletado")
            
        return False

def suggest_solutions():
    """Sugere soluções para problemas comuns"""
    print(f"\n💡 SOLUÇÕES RECOMENDADAS:")
    print(f"=" * 30)
    print(f"1. 🔄 Gerar novas credenciais:")
    print(f"   - Acesse Google Cloud Console")
    print(f"   - IAM & Admin > Service Accounts")
    print(f"   - Gere uma nova chave JSON")
    print(f"")
    print(f"2. ⏰ Verificar relógio do sistema:")
    print(f"   - Sincronize a data/hora do sistema")
    print(f"   - Verifique fuso horário")
    print(f"")
    print(f"3. 🌐 Verificar conectividade:")
    print(f"   - Teste conexão com internet")
    print(f"   - Verifique proxy/firewall")
    print(f"")
    print(f"4. 📋 Verificar permissões:")
    print(f"   - Service account deve ter acesso ao Firestore")
    print(f"   - Roles: Firestore Admin ou Cloud Datastore Owner")

if __name__ == "__main__":
    print(f"🕒 Hora atual do sistema: {datetime.now()}")
    print(f"🌍 Timezone: {datetime.now().astimezone().tzinfo}")
    print(f"")
    
    success = test_firebase_connection()
    
    if not success:
        suggest_solutions()
        sys.exit(1)
    else:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print(f"✅ Firebase está funcionando corretamente")
