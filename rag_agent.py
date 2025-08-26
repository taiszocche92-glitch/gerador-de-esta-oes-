import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import numpy as np
import json
from typing import List
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
        api_key = (os.getenv("GEMINI_API_KEY_1") or 
                  os.getenv("GEMINI_API_KEY_2") or 
                  os.getenv("GEMINI_API_KEY_3") or 
                  os.getenv("GEMINI_API_KEY_4"))
        
        if api_key:
            genai.configure(api_key=api_key)
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

    # generate embedding for the query using genai.embed_content with key rotation

        # Validação do modelo de embedding
        if model_name not in ALLOWED_MODELS:
            raise HTTPException(status_code=400, detail=f"Modelo de embedding '{model_name}' não permitido. Consulte MODELOS_GEMINI_ATUAIS.md.")
    try:
        from gemini_client import KEY_SLOTS, configure_specific
    except Exception:
        KEY_SLOTS = [f'GEMINI_API_KEY_{i}' for i in range(1,9)]
        def configure_specific(slot):
            try:
                import gemini_client as gc
                return gc.configure_specific(slot)
            except Exception:
                # attempt to set env variable fallback
                return None

    q_emb = None
    last_err = None
    used_embed_slot = None
    for slot in KEY_SLOTS:
        # try configure this slot
        try:
            configured = configure_specific(slot)
        except Exception:
            configured = None
        if not configured:
            continue
        try:
            resp = genai.embed_content(model=model_name, content=[body.query])
            emb_list = None
            if isinstance(resp, dict):
                if 'embedding' in resp:
                    val = resp['embedding']
                    if isinstance(val, list) and val and isinstance(val[0], list):
                        emb_list = val
                    else:
                        emb_list = [val]
                elif 'embedding' in resp.get('data', {}):
                    val = resp['data']['embedding']
                    if isinstance(val, list) and val and isinstance(val[0], list):
                        emb_list = val
                    else:
                        emb_list = [val]
            elif hasattr(resp, 'embedding'):
                attr = resp.embedding
                if isinstance(attr, list) and attr and isinstance(attr[0], list):
                    emb_list = attr
                else:
                    emb_list = [attr]
            else:
                emb_list = list(resp)

            q_emb = np.array(emb_list[0], dtype=float)
            used_embed_slot = slot
            break
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            # rotate on expired/invalid API key or permission errors
            if any(x in msg for x in ('api_key_invalid', 'api key expired', 'expired', 'access_token_scope_insufficient', 'permissiondenied', '403')):
                continue
            else:
                continue

    if q_emb is None:
        raise HTTPException(status_code=500, detail=f'Embedding error: {last_err}')

    sims = _cosine_similarity(q_emb, _embeddings)
    topk = int(body.top_k)
    if topk <=0: topk = 5
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
        from gemini_client import KEY_SLOTS, configure_specific
    except Exception:
        # fallback para ordem simples
        KEY_SLOTS = [f'GEMINI_API_KEY_{i}' for i in range(1,9)]

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
        """Tenta as várias camadas de geração e retorna (text, error)."""
        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user},
        ]
        # 1) genai.generate_answer
        try:
            gen_resp = genai.generate_answer(model=chosen_gen, messages=messages, max_output_tokens=body.max_output_tokens)
            if isinstance(gen_resp, dict):
                text = gen_resp.get('answer') or (gen_resp.get('candidates') and gen_resp['candidates'][0].get('content'))
            else:
                text = getattr(gen_resp, 'answer', None) or getattr(gen_resp, 'output', None) or str(gen_resp)
                if hasattr(text, 'text'):
                    text = text.text
            return text, None
        except Exception:
            pass

        # 2) genai.generate
        try:
            gen_resp = genai.generate(model=chosen_gen, prompt=[{"role": "system", "content": prompt_system}, {"role": "user", "content": prompt_user}], max_output_tokens=body.max_output_tokens)
            if isinstance(gen_resp, dict):
                text = gen_resp.get('candidates', [{}])[0].get('content') or str(gen_resp)
            else:
                text = getattr(gen_resp, 'output', None) or str(gen_resp)
            return text, None
        except Exception:
            pass

        # 3) TextServiceClient.generate_text
        try:
            from google.ai.generativelanguage import TextServiceClient, GenerateTextRequest, TextPrompt
            client = TextServiceClient()
            prompt = TextPrompt(text=prompt_system + "\n\n" + prompt_user)
            req = GenerateTextRequest(model=chosen_gen, prompt=prompt, max_output_tokens=body.max_output_tokens)
            gen_resp = client.generate_text(req)
            if hasattr(gen_resp, 'candidates') and gen_resp.candidates:
                text = gen_resp.candidates[0].content
            elif hasattr(gen_resp, 'output'):
                text = str(gen_resp.output)
            else:
                text = str(gen_resp)
            return text, None
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
