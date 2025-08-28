import google.generativeai as genai
from google.generativeai.generative_models import GenerativeModel
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import numpy as np
import json
from typing import List
import re
import threading
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Lista de modelos permitidos (conforme MODELOS_GEMINI_ATUAIS.md)
ALLOWED_MODELS = {
    'models/gemini-1.5-pro-002',
    'models/gemini-1.5-pro',
    'models/gemini-1.5-flash',
    'models/gemini-1.5-flash-002',
    'models/gemini-1.5-flash-8b',
    'models/gemini-1.5-flash-8b-001',
    'models/gemini-2.5-flash',
    'models/gemini-2.5-flash-lite',
    'models/gemini-2.0-flash-exp',
    'models/gemini-2.5-pro',
    'models/gemini-2.0-flash',
    'models/gemini-2.0-flash-001',
    'models/gemini-2.0-flash-lite-001',
    'models/gemini-2.0-flash-lite',
    'models/gemini-2.0-flash-preview-image-generation',
    'models/embedding-001',
    'models/text-embedding-004',
}

router = APIRouter()

class RAGQuery(BaseModel):
    query: str
    top_k: int = 5
    generation_model: str = "pro"  # 'pro' or 'flash'
    max_output_tokens: int = 512

# Lazy-loaded globals
_vectors_lock = threading.Lock()
_embeddings = None
_metadata = None
_id_map = None
_config = None

def _load_vectors(base_path: Path):
    global _embeddings, _metadata, _id_map, _config
    with _vectors_lock:
        if _embeddings is not None:
            return
        vdir = base_path
        emb_file = vdir / 'embeddings.npy'
        meta_file = vdir / 'metadata.jsonl'
        id_file = vdir / 'id_map.json'
        cfg_file = vdir / 'config.json'

        if not emb_file.exists():
            raise FileNotFoundError(str(emb_file))

        _embeddings = np.load(str(emb_file))

        # load metadata
        _metadata = []
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    _metadata.append(json.loads(line))

        # load id_map
        try:
            if id_file.exists():
                with open(id_file, 'r', encoding='utf-8') as f:
                    _id_map = json.load(f)
        except Exception:
            _id_map = None

        # load config
        try:
            if cfg_file.exists():
                with open(cfg_file, 'r', encoding='utf-8') as f:
                    _config = json.load(f)
        except Exception:
            _config = None

def configure_gemini_keys():
    """Configuração simples das chaves Gemini para RAG"""
    try:
        # Usar a primeira chave disponível
        print(f"DEBUG: Tentando GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')}")
        print(f"DEBUG: Tentando GOOGLE_API_KEY_1: {os.getenv('GOOGLE_API_KEY_1')}")
        print(f"DEBUG: Tentando GOOGLE_API_KEY_2: {os.getenv('GOOGLE_API_KEY_2')}")
        print(f"DEBUG: Tentando GOOGLE_API_KEY_3: {os.getenv('GOOGLE_API_KEY_3')}")
        print(f"DEBUG: Tentando GOOGLE_API_KEY_4: {os.getenv('GOOGLE_API_KEY_4')}")
        print(f"DEBUG: Tentando GOOGLE_API_KEY_5: {os.getenv('GOOGLE_API_KEY_5')}")
        print(f"DEBUG: Tentando GEMINI_API_KEY_1: {os.getenv('GEMINI_API_KEY_1')}")
        print(f"DEBUG: Tentando GEMINI_API_KEY_2: {os.getenv('GEMINI_API_KEY_2')}")
        print(f"DEBUG: Tentando GEMINI_API_KEY_3: {os.getenv('GEMINI_API_KEY_3')}")
        print(f"DEBUG: Tentando GEMINI_API_KEY_4: {os.getenv('GEMINI_API_KEY_4')}")

        api_key = (os.getenv("GOOGLE_API_KEY") or
                   os.getenv("GOOGLE_API_KEY_1") or # Adicionado para corresponder ao .env
                   os.getenv("GOOGLE_API_KEY_2") or # Adicionado para corresponder ao .env
                   os.getenv("GOOGLE_API_KEY_3") or # Adicionado para corresponder ao .env
                   os.getenv("GOOGLE_API_KEY_4") or # Adicionado para corresponder ao .env
                   os.getenv("GOOGLE_API_KEY_5") or # Adicionado para corresponder ao .env
                   os.getenv("GEMINI_API_KEY_1") or
                   os.getenv("GEMINI_API_KEY_2") or
                   os.getenv("GEMINI_API_KEY_3") or
                   os.getenv("GEMINI_API_KEY_4"))
        
        if api_key:
            print("✅ Gemini configurado para RAG")
            return True
        else:
            print("⚠️ Nenhuma chave Gemini encontrada para RAG")
            return False
    except Exception as e:
        print(f"❌ Erro ao configurar Gemini para RAG: {e}")
        return False

def _cosine_similarity(a: np.ndarray, b: np.ndarray):
    # a: (d,), b: (n,d)
    if a.ndim==1:
        a = a.reshape(1, -1)
    # normalize
    an = a / np.linalg.norm(a, axis=1, keepdims=True)
    bn = b / np.linalg.norm(b, axis=1, keepdims=True)
    sims = (an @ bn.T).squeeze(0)
    return sims


@router.post('/rag/query')
async def rag_query(body: RAGQuery):
    """Retorna os top_k trechos mais similares à query usando embeddings salvos.

    Observação: usa embedding via cliente global configurado em `main.py`.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    import google.generativeai as genai
    # Usar helper centralizado para escolher a primeira chave disponível (prioriza GEMINI_API_KEY_4 conforme gemini_client)
    try:
        from gemini_client import configure_first_available
        chosen_slot = configure_first_available()
    except Exception:
        chosen_slot = None

    base = Path(__file__).parent / 'memoria' / 'vectors'
    # Lista de modelos permitidos (conforme MODELOS_GEMINI_ATUAIS.md)
    ALLOWED_MODELS = {
        'models/gemini-1.5-pro-002',
        'models/gemini-1.5-pro',
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-002',
        'models/gemini-1.5-flash-8b',
        'models/gemini-1.5-flash-8b-001',
        'models/gemini-2.5-flash',
        'models/gemini-2.5-flash-lite',
        'models/gemini-2.0-flash-exp',
        'models/gemini-2.5-pro',
        'models/gemini-2.0-flash',
        'models/gemini-2.0-flash-001',
        'models/gemini-2.0-flash-lite-001',
        'models/gemini-2.0-flash-lite',
        'models/gemini-2.0-flash-preview-image-generation',
        'models/embedding-001',
        'models/text-embedding-004',
    }
    try:
        _load_vectors(base)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f'Vectors not found: {e}')

    if _embeddings is None:
        raise HTTPException(status_code=500, detail='Embeddings not loaded')

    # determine model
    model_name = (_config or {}).get('model') if _config else None
    if not model_name:
        # fallback to a reasonable default used earlier
        model_name = 'models/embedding-001'

    # pick an API key via configure function if available
    try:
        configure_gemini_keys()
    except Exception:
        pass

    # Tentar gerar embedding da query usando genai configurado por gemini_client (se disponível).
    q_emb = None
    used_embed_slot = None
    target_dim = None
    try:
        if _embeddings is not None:
            try:
                target_dim = int(_embeddings.shape[1])
            except Exception:
                target_dim = None

        # Configure a primeira chave disponível via gemini_client (se existir)
        try:
            from gemini_client import configure_first_available
            slot = configure_first_available()
            if slot:
                used_embed_slot = slot
        except Exception:
            # fallback: try specific KEY_SLOTS later
            slot = None

        # Tentar diversos nomes públicos de função de embeddings no pacote genai
        emb_fn_names = ['get_embeddings', 'get_embedding', 'embed_text', 'embed', 'embeddings']
        emb_resp = None
        for name in emb_fn_names:
            fn = getattr(genai, name, None)
            if not fn:
                continue
            try:
                # tentar chamada comum (modelo, input)
                try:
                    emb_resp = fn(model=model_name, input=body.query)
                except TypeError:
                    # alguns wrappers esperam (input, model)
                    emb_resp = fn(body.query, model=model_name)
                except Exception:
                    emb_resp = fn(body.query)
                # extrair embedding de resposta
                def _extract_embedding(resp):
                    if resp is None:
                        return None
                    if isinstance(resp, dict):
                        if 'data' in resp and resp['data']:
                            first = resp['data'][0]
                            if isinstance(first, dict) and 'embedding' in first:
                                return np.array(first['embedding'], dtype=float)
                        if 'embedding' in resp:
                            return np.array(resp['embedding'], dtype=float)
                    if hasattr(resp, 'embedding'):
                        attr = getattr(resp, 'embedding')
                        try:
                            arr = np.array(attr, dtype=float)
                            if arr.ndim == 1:
                                return arr
                            if arr.ndim > 1:
                                return arr[0]
                        except Exception:
                            pass
                    # última tentativa: transformar em array direto
                    try:
                        arr = np.array(resp, dtype=float)
                        if arr.ndim == 1:
                            return arr
                        if arr.ndim > 1:
                            return arr[0]
                    except Exception:
                        return None

                candidate = _extract_embedding(emb_resp)
                if candidate is not None and candidate.size > 0:
                    q_emb = candidate.astype(float)
                    break
            except Exception:
                continue

    except Exception:
        q_emb = None

    # Se obtivemos embedding, validar dimensão contra o index
    if q_emb is not None and target_dim is not None:
        try:
            if q_emb.shape[0] != target_dim:
                # informar que é necessário reindexar com o modelo atual
                return {
                    'query': body.query,
                    'reindex_required': True,
                    'expected_dim': target_dim,
                    'got_dim': int(q_emb.shape[0]),
                    'generation_model': None,
                    'generation_key_slot': used_embed_slot,
                    'answer': None,
                    'evidence': [],
                    'generation_error': 'embedding_dimension_mismatch'
                }
        except Exception:
            pass

    # Se não conseguimos embedding via API, usar fallback por similaridade de tokens/strings
    if q_emb is None:
        def tokenize_text(t: str):
            if not t:
                return set()
            return set(re.findall(r"\w+", t.lower()))

        q_tokens = tokenize_text(body.query)
        sims_list = []
        for md in (_metadata or []):
            text_candidate = md.get('text_preview') or md.get('text') or json.dumps(md.get('meta', {}))
            doc_tokens = tokenize_text(text_candidate)
            if not q_tokens or not doc_tokens:
                score = 0.0
            else:
                overlap = q_tokens.intersection(doc_tokens)
                score = len(overlap) / (len(q_tokens) + 1)
            sims_list.append(score)
        sims = np.array(sims_list, dtype=float)
    else:
        sims = _cosine_similarity(q_emb, _embeddings)
    topk = int(body.top_k)
    if topk <=0: topk = 5
    sims = np.array(sims, dtype=float)
    idx = np.argsort(-sims)[:topk]

    results = []
    for i in idx:
        meta = _metadata[i] if _metadata and i < len(_metadata) else None
        score = float(sims[i])
        results.append({
            'index': int(i),
            'score': score,
            'metadata': meta
        })

    # Montar prompt/contexto para geração final (RAG)
    # Limitar tamanho do contexto concatenado
    contexts = []
    for r in results:
        txt = r['metadata'].get('text_preview') if r['metadata'] else ''
        contexts.append(f"[source: {r['metadata'].get('meta',{}).get('path','?')}]\n{txt}\n")

    context_combined = '\n---\n'.join(contexts[:body.top_k])
    # construir prompt de sistema/usuario simples
    prompt_system = (
        "Você é um assistente médico treinado para responder perguntas com base em trechos fornecidos."
    )
    prompt_user = (
        f"Contexto:\n{context_combined}\n\nPergunta: {body.query}\n\nResponda de forma concisa e cite as fontes entre colchetes.")

    # selecionar modelo de geração
    gen_model_map = {
        'pro': 'gemini-2.5-pro',
        'flash': 'gemini-2.5-flash'
    }
    chosen_gen = gen_model_map.get(body.generation_model, 'gemini-2.5-pro')

    # chamar gerador com rotação automática de chaves
    try:
        from gemini_client import KEY_SLOTS
        # Ajuste: configure_specific deve aceitar 'slot' como parâmetro
        def configure_specific(slot):
            try:
                import gemini_client as gc
                return gc.configure_specific(slot)
            except Exception:
                return None
    except Exception:
        # fallback para ordem simples
        KEY_SLOTS = ['GOOGLE_API_KEY_5', 'GOOGLE_API_KEY_4', 'GOOGLE_API_KEY_3', 'GOOGLE_API_KEY_2', 'GOOGLE_API_KEY_1']

        # Validação do modelo de geração
        if f"models/{chosen_gen}" not in ALLOWED_MODELS:
            raise HTTPException(status_code=400, detail=f"Modelo de geração '{chosen_gen}' não permitido. Consulte MODELOS_GEMINI_ATUAIS.md.")
        def configure_specific(slot):
            try:
                import gemini_client as gc
                return gc.configure_specific(slot)
            except Exception:
                return None

    import google.generativeai as genai

    def _try_generate_with_client():
        """Tenta geração usando genai.generate_content (método oficial)."""
        try:
            # Usar o método oficial generate_content
            model = GenerativeModel(chosen_gen)
            response = model.generate_content(prompt_system + "\n\n" + prompt_user)

            # Extrair texto da resposta
            if response and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    text = ''.join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                    return text, None
                elif hasattr(candidate, 'text'):
                    return candidate.text, None

            return None, Exception("Resposta inválida do modelo")
        except Exception as e:
            return None, e

    last_error = None
    used_slot = None
    generated_text = None

    for slot in KEY_SLOTS:
        # tentar configurar este slot
        try:
            configured = configure_specific(slot)
        except Exception:
            configured = None
        if not configured:
            continue
        used_slot = slot
        # tentar gerar
        try:
            text, err = _try_generate_with_client()
            if err is None and text:
                generated_text = text
                break
            else:
                last_error = err or Exception('no text returned')
                # se erro indicar escopo/quota/403, tentar próxima chave
                msg = str(last_error).lower() if last_error else ''
                if any(x in msg for x in ('403', 'permissiondenied', 'access_token_scope_insufficient', 'quota')):
                    # continue para próxima chave
                    continue
                else:
                    # para outros erros, também tentamos próxima chave
                    continue
        except Exception as e:
            last_error = e
            continue

    if not generated_text:
        err_msg = str(last_error) if last_error else 'Generation failed for all keys'
        return {
            'query': body.query,
            'generation_model': None,
            'generation_key_slot': used_slot,
            'answer': None,
            'evidence': results,
            'generation_error': err_msg,
        }

    return {
        'query': body.query,
        'generation_model': chosen_gen,
        'generation_key_slot': used_slot,
        'answer': generated_text,
        'evidence': results,
    }
