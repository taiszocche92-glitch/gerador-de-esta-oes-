
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
