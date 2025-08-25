import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Order of keys to try: prioriza GEMINI_API_KEY_4 (chave paga para geração), depois os demais
KEY_SLOTS = ['GEMINI_API_KEY_4'] + [f'GEMINI_API_KEY_{i}' for i in range(1,9) if i != 4]

# Heurística: keys que começam with 'AIza' são API keys (HTTP); preferi-las
def _is_api_key(val: str) -> bool:
    return isinstance(val, str) and val.startswith('AIza')

def configure_first_available():
    """Configura genai com a primeira chave disponível na ordem KEY_SLOTS.
    Retorna a chave usada ou None.
    """
    # tentar primeiro chaves do tipo API key (ex: começam com 'AIza')
    import google.generativeai as genai
    for slot in KEY_SLOTS:
        raw = os.getenv(slot)
        key = raw.strip() if isinstance(raw, str) else None
        if not key:
            continue
        if _is_api_key(key):
            try:
                # configurar diretamente como api_key (HTTP API)
                genai.api_key = key
                return slot
            except Exception:
                # se falhar, tentar métodos alternativos abaixo
                pass
    # se não encontrou API key ou falhou, tentar configurar por outros meios
    import google.generativeai as genai
    for slot in KEY_SLOTS:
        raw = os.getenv(slot)
        key = raw.strip() if isinstance(raw, str) else None
        if not key:
            continue
        try:
            # tentar configurar via client API
            try:
                genai.client.configure(api_key=key)
            except Exception:
                try:
                    genai.configure(api_key=key)
                except Exception:
                    genai.api_key = key
            return slot
        except Exception:
            # se falhar, continue para a próxima chave
            continue
    return None

def configure_specific(slot_name: str) -> Optional[str]:
    import google.generativeai as genai
    raw = os.getenv(slot_name)
    key = raw.strip() if isinstance(raw, str) else None
    if not key:
        return None
    try:
        # Se for API key HTTP (ex: começa com 'AIza'), setar genai.api_key diretamente
        if _is_api_key(key):
            try:
                genai.api_key = key
                return slot_name
            except Exception:
                pass
        try:
            genai.client.configure(api_key=key)
        except Exception:
            try:
                genai.configure(api_key=key)
            except Exception:
                genai.api_key = key
        return slot_name
    except Exception:
        return None


if __name__ == '__main__':
    used = configure_first_available()
    print('Usou slot:', used)
