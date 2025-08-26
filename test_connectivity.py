
import requests
import time

def test_google_connectivity():
    """Testa conectividade com serviços Google"""
    urls = [
        'https://www.googleapis.com',
        'https://firestore.googleapis.com', 
        'https://oauth2.googleapis.com/token',
        'https://accounts.google.com'
    ]
    
    print("🌐 Testando conectividade...")
    
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")

if __name__ == "__main__":
    test_google_connectivity()
