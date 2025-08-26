
def initialize_firebase_robust():
    """Inicialização robusta com fallback automático"""
    global db, firebase_mock_mode
    
    try:
        # Tentar múltiplas estratégias de inicialização
        service_account_paths = [
            os.path.join('memoria', 'serviceAccountKey.json'),
            'memoria/serviceAccountKey.json',
            './serviceAccountKey.json'
        ]
        
        for path in service_account_paths:
            if os.path.exists(path):
                try:
                    print(f"🔧 Tentando inicializar Firebase com {path}...")
                    
                    # Limpar apps existentes
                    for app in list(firebase_admin._apps.values()):
                        firebase_admin.delete_app(app)
                    
                    cred = credentials.Certificate(path)
                    
                    # Configuração com timeout reduzido
                    app = firebase_admin.initialize_app(cred, {
                        'projectId': 'revalida-companion'
                    })
                    
                    # Teste de conectividade com timeout curto
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("Timeout na conexão")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(10)  # 10 segundos timeout
                    
                    try:
                        db = firestore.client()
                        # Teste rápido
                        test_doc = db.collection('_test').document('ping')
                        test_doc.set({'ping': 'ok'}, merge=True)
                        signal.alarm(0)  # Cancelar timeout
                        
                        print(f"✅ Firebase conectado com sucesso!")
                        return True
                        
                    except TimeoutError:
                        signal.alarm(0)
                        print(f"⚠️ Timeout na conexão - continuando em modo local")
                        raise
                        
                except Exception as e:
                    error_str = str(e).lower()
                    if 'invalid jwt' in error_str:
                        print(f"⚠️ Problema de autenticação: {e}")
                        print(f"🔄 Continuando com sistema local...")
                    else:
                        print(f"⚠️ Erro Firebase: {e}")
                    continue
        
        # Se chegou aqui, todas as tentativas falharam
        raise Exception("Todas as tentativas de conexão falharam")
        
    except Exception as e:
        print(f"🔄 Ativando modo híbrido local (sem Firestore)")
        print(f"   Motivo: {e}")
        firebase_mock_mode = True
        db = None
        return False
