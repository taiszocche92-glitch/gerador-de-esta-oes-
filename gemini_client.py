import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Order of keys to try: prioriza GOOGLE_API_KEY_5 (chave principal), depois os demais GOOGLE_API_KEY_*
KEY_SLOTS = ['GOOGLE_API_KEY_5', 'GOOGLE_API_KEY_4', 'GOOGLE_API_KEY_3', 'GOOGLE_API_KEY_2', 'GOOGLE_API_KEY_1']

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
                # O método correto é genai.configure, mas se não existir, usar genai.configure se disponível
                if hasattr(genai, "configure"):
                    # Pylance não reconhece configure, mas é o método correto segundo a documentação oficial.
                    # Para evitar erro de linter, pode-se usar getattr.
                    getattr(genai, "configure")(api_key=key)
                else:
                    raise RuntimeError("Não foi possível configurar a chave da API: método 'configure' não encontrado em google.generativeai")
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
                if hasattr(genai, "configure"):
                    getattr(genai, "configure")(api_key=key)
                else:
                    raise RuntimeError("Não foi possível configurar a chave da API: método 'configure' não encontrado em google.generativeai")
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
        # Configuração única usando o método correto
        if hasattr(genai, "configure"):
            getattr(genai, "configure")(api_key=key)
            return slot_name
        else:
            raise RuntimeError("Não foi possível configurar a chave da API: método 'configure' não encontrado em google.generativeai")
    except Exception:
        return None


if __name__ == '__main__':
    used = configure_first_available()
    print('Usou slot:', used)
