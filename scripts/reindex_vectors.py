"""
Script de reindexação de embeddings para o repositório.

O que faz:
- Lê `memoria/vectors/metadata.jsonl` para obter documentos e textos.
- Gera embeddings usando a API configurada por `gemini_client` + `google.generativeai` (tenta vários métodos públicos).
- Salva `embeddings.npy`, `id_map.json` e `config.json` em `memoria/vectors/`.
- Faz backup do `embeddings.npy` anterior.

Uso:
    python scripts/reindex_vectors.py --model models/text-embedding-004 --batch 16

Notas:
- Requer chaves configuradas nas variáveis de ambiente (KEY_SLOTS no `gemini_client`).
- Se preferir outro provedor, modifique a função `generate_embedding`.
"""

import os
import json
import time
import argparse
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent.parent
VECTORS_DIR = BASE / 'memoria' / 'vectors'
METADATA_FILE = VECTORS_DIR / 'metadata.jsonl'
EMB_FILE = VECTORS_DIR / 'embeddings.npy'
ID_MAP_FILE = VECTORS_DIR / 'id_map.json'
CFG_FILE = VECTORS_DIR / 'config.json'

# Try to import clients
try:
    import sys
    sys.path.insert(0, str(BASE))  # Adicionar diretório raiz ao path
    from gemini_client import configure_first_available
except Exception as e:
    print(f"⚠️ Falha ao importar gemini_client: {e}")
    configure_first_available = None

try:
    import google.generativeai as genai
except Exception:
    genai = None


def load_metadata():
    docs = []
    if not METADATA_FILE.exists():
        print(f"Arquivo de metadata não encontrado: {METADATA_FILE}")
        return docs
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                docs.append(obj)
            except Exception as e:
                print(f"⚠️ Falha ao ler linha {i} do metadata.jsonl: {e}")
    print(f"📚 Carregados {len(docs)} documentos do metadata.jsonl")
    return docs


def extract_text_from_meta(md):
    # Priorizar campos text/text_preview; senão tentar meta.path
    text = None
    if not md:
        return ''
    if isinstance(md, dict):
        text = md.get('text') or md.get('text_preview')
        if text:
            return str(text)
        meta = md.get('meta') or {}
        path = meta.get('path') or meta.get('source')
        if path:
            p = Path(path)
            if not p.is_absolute():
                p = (BASE / path).resolve()
            try:
                if p.exists() and p.suffix.lower() in ['.txt', '.md', '.json']:
                    return p.read_text(encoding='utf-8')
            except Exception:
                pass
    return ''


def configure_api():
    used = None
    if configure_first_available:
        try:
            used = configure_first_available()
            print(f"🔑 Chave configurada via gemini_client: {used}")
        except Exception as e:
            print(f"⚠️ gemini_client.configure_first_available falhou: {e}")
    else:
        print("ℹ️ gemini_client não disponível; tentativa de usar google.generativeai diretamente se instalado.")
        # tentar configurar genai diretamente a partir de variáveis de ambiente comuns
        try:
            if genai is None:
                print("⚠️ google.generativeai não encontrado no ambiente (não instalado).")
                # listar possíveis variáveis de ambiente que podem conter chaves para ajudar o diagnóstico
                candidates = ['GEMINI_API_KEY_4'] + [f'GEMINI_API_KEY_{i}' for i in range(1,9) if i != 4] + ['GOOGLE_API_KEY', 'OPENAI_API_KEY']
                found = [k for k in candidates if os.getenv(k)]
                if found:
                    print(f"ℹ️ Variáveis de ambiente potencialmente presentes: {found}")
                else:
                    print("ℹ️ Nenhuma variável de ambiente de chave encontrada entre opções comuns.")
                return None
            # se genai instalado, tentar configurar com a primeira variável de ambiente disponível
            candidates = ['GEMINI_API_KEY_4'] + [f'GEMINI_API_KEY_{i}' for i in range(1,9) if i != 4] + ['GOOGLE_API_KEY', 'OPENAI_API_KEY']
            for var in candidates:
                val = os.getenv(var)
                if not val:
                    continue
                try:
                    if hasattr(genai, 'configure'):
                        getattr(genai, 'configure')(api_key=val)
                        print(f"🔑 Chave configurada via variável de ambiente: {var}")
                        return var
                except Exception as e:
                    print(f"⚠️ Falha ao configurar genai com {var}: {e}")
                    continue
        except Exception as e:
            print(f"⚠️ Erro ao tentar configurar google.generativeai diretamente: {e}")
    return used


def generate_embedding_text(text, model_name=None):
    """Gera embedding para um texto. Retorna numpy array ou None."""
    # Tenta funções comuns do genai na ordem
    if genai is None:
        return None
    
    # 1) Tentativa principal: genai.embed_content (sabemos que funciona)
    try:
        # Usar getattr para evitar warning do linter sobre função não exportada
        embed_fn = getattr(genai, 'embed_content', None)
        if embed_fn:
            resp = embed_fn(model=model_name, content=text)
            if isinstance(resp, dict) and 'embedding' in resp:
                emb = resp['embedding']
                arr = np.array(emb, dtype=float)
                return arr
    except Exception as e:
        print(f"ℹ️ tentativa via genai.embed_content falhou: {e}")

    # 2) Tentativa alternativa: genai.embeddings.create
    try:
        emb_mod = getattr(genai, 'embeddings', None)
        if emb_mod:
            # muitos SDKs aceitam embeddings.create(model=..., input=[...])
            if hasattr(emb_mod, 'create'):
                try:
                    resp = emb_mod.create(model=model_name, input=[text])
                except TypeError:
                    try:
                        resp = emb_mod.create(input=[text], model=model_name)
                    except Exception:
                        resp = emb_mod.create(text)
                # extrair embedding da resposta
                emb = None
                # resposta pode ser um dict com 'data'
                if isinstance(resp, dict):
                    if 'data' in resp and resp['data']:
                        first = resp['data'][0]
                        if isinstance(first, dict):
                            emb = first.get('embedding') or first.get('embeddings')
                elif hasattr(resp, 'data'):
                    try:
                        first = resp.data[0]
                        if hasattr(first, 'embedding'):
                            emb = getattr(first, 'embedding')
                    except Exception:
                        pass
                if emb is not None:
                    arr = np.array(emb, dtype=float)
                    return arr
    except Exception as e:
        print(f"ℹ️ tentativa via genai.embeddings.create falhou: {e}")

    # 3) Tentativas por nomes de função antigos/comuns
    fn_names = ['get_embeddings', 'get_embedding', 'embed_text', 'embed', 'embeddings']
    for name in fn_names:
        fn = getattr(genai, name, None)
        if not fn:
            continue
        try:
            # algumas APIs aceitam lista de inputs; aqui enviamos single
            try:
                resp = fn(model=model_name, input=text)
            except TypeError:
                # fallback argumentos alternativos
                try:
                    resp = fn(text, model=model_name)
                except Exception:
                    resp = fn(text)
            # extrair embedding
            emb = None
            if isinstance(resp, dict):
                if 'data' in resp and resp['data']:
                    first = resp['data'][0]
                    emb = first.get('embedding') if isinstance(first, dict) else None
                elif 'embedding' in resp:
                    emb = resp.get('embedding')
            elif hasattr(resp, 'embedding'):
                emb = getattr(resp, 'embedding')
            else:
                # última tentativa: converter diretamente
                try:
                    arr = np.array(resp, dtype=float)
                    if arr.ndim == 1:
                        emb = arr.tolist()
                except Exception:
                    emb = None
            if emb is not None:
                arr = np.array(emb, dtype=float)
                return arr
        except Exception as e:
            # tentar próxima função
            print(f"ℹ️ tentativa de {name} falhou: {e}")
            continue
    return None


def check_api_available(model_name=None, sample_text="teste de disponibilidade"):
    """Tenta gerar um embedding curto para verificar se a API de embeddings está disponível.
    Retorna (ok: bool, info: str).
    """
    try:
        used = configure_api()
        emb = generate_embedding_text(sample_text, model_name=model_name)
        if emb is None:
            return False, "Nenhuma resposta de embedding retornada (verifique chaves/quota)."
        if isinstance(emb, np.ndarray) and emb.size > 0:
            return True, f"Embedding de teste gerado (dim={emb.shape[0]}) usando slot {used}"
        return False, "Resposta de embedding inválida"
    except Exception as e:
        return False, str(e)


def backup_existing():
    if EMB_FILE.exists():
        ts = int(time.time())
        target = VECTORS_DIR / f"embeddings_backup_{ts}.npy"
        try:
            EMB_FILE.replace(target)
            print(f"🔁 Backup criado: {target}")
        except Exception as e:
            print(f"⚠️ Falha ao criar backup do embeddings: {e}")


def main(args):
    docs = load_metadata()
    if not docs:
        print("❌ Nenhum documento para reindexar. Verifique memoria/vectors/metadata.jsonl")
        return

    used_slot = configure_api()

    # Preparar lista de documentos a indexar (suporta incremental)
    existing_ids = []
    if args.incremental and ID_MAP_FILE.exists():
        try:
            with open(ID_MAP_FILE, 'r', encoding='utf-8') as f:
                j = json.load(f)
                existing_ids = j.get('ids', []) if isinstance(j, dict) else j
            print(f"ℹ️ Modo incremental: {len(existing_ids)} ids existentes carregados")
        except Exception as e:
            print(f"⚠️ Falha ao carregar id_map existente: {e}")

    to_index = []
    for idx, md in enumerate(docs):
        doc_id = md.get('id') or md.get('meta', {}).get('path') or md.get('meta', {}).get('id') or str(idx)
        if args.incremental and doc_id in existing_ids:
            continue
        txt = extract_text_from_meta(md)
        to_index.append((doc_id, txt))

    if args.limit and args.limit > 0:
        to_index = to_index[:args.limit]

    if not to_index:
        print("ℹ️ Nenhum documento novo para indexar (modo incremental ou limite aplicado). Saindo.")
        return

    # Gerar embeddings iterativamente (batched simples)
    embeddings = []
    failed = []
    total = len(to_index)
    print(f"🚀 Iniciando geração de embeddings para {total} documentos (modelo={args.model})")
    new_ids = []
    for i, (doc_id, txt) in enumerate(to_index):
        if not txt:
            print(f"⚠️ Documento {doc_id} tem texto vazio — pulando")
            failed.append(doc_id)
            continue
        emb = generate_embedding_text(txt, model_name=args.model)
        if emb is None:
            print(f"⚠️ Falha ao gerar embedding para documento {doc_id}")
            failed.append(doc_id)
            time.sleep(0.1)
            continue
        embeddings.append(emb)
        new_ids.append(doc_id)
        if (i+1) % args.progress == 0 or i+1 == total:
            print(f"   ✅ {i+1}/{total} embeddings gerados")
        if args.sleep_between > 0:
            time.sleep(args.sleep_between)

    if not embeddings:
        print("❌ Nenhum embedding gerado — verifique credenciais/API.")
        return

    # Converter para array 2D
    try:
        new_emb_array = np.vstack([e.reshape(1, -1) for e in embeddings])
    except Exception as e:
        print(f"❌ Erro ao empilhar embeddings: {e}")
        return

    # Backup e salvar (se incremental, tentar anexar ao existente)
    try:
        if args.incremental and EMB_FILE.exists():
            existing = np.load(str(EMB_FILE))
            # checar compatibilidade de dimensão
            if existing.shape[1] != new_emb_array.shape[1]:
                print(f"❌ Dimensão incompatível: existing={existing.shape}, new={new_emb_array.shape}. Reindex completo necessário.")
                return
            combined = np.vstack([existing, new_emb_array])
            backup_existing()
            np.save(str(EMB_FILE), combined)
            print(f"✅ Embeddings anexados em: {EMB_FILE} (shape={combined.shape})")
            # atualizar id_map
            try:
                with open(ID_MAP_FILE, 'r', encoding='utf-8') as f:
                    j = json.load(f)
                    existing_ids_file = j.get('ids', []) if isinstance(j, dict) else j
            except Exception:
                existing_ids_file = []
            merged_ids = existing_ids_file + new_ids
            with open(ID_MAP_FILE, 'w', encoding='utf-8') as f:
                json.dump({'ids': merged_ids}, f, ensure_ascii=False, indent=2)
            print(f"✅ id_map atualizado em: {ID_MAP_FILE}")
        else:
            backup_existing()
            np.save(str(EMB_FILE), new_emb_array)
            print(f"✅ Embeddings salvos em: {EMB_FILE} (shape={new_emb_array.shape})")
            # Salvar id_map (os indices correspondem às linhas do embeddings.npy)
            try:
                with open(ID_MAP_FILE, 'w', encoding='utf-8') as f:
                    json.dump({'ids': new_ids}, f, ensure_ascii=False, indent=2)
                print(f"✅ id_map salvo em: {ID_MAP_FILE}")
            except Exception as e:
                print(f"⚠️ Falha ao salvar id_map: {e}")
    except Exception as e:
        print(f"❌ Falha ao salvar embeddings: {e}")
        return

    # Salvar config simples
    # determinar tamanho final salvo
    try:
        final_count = None
        if args.incremental and EMB_FILE.exists():
            # recarregar para obter shape final
            final_arr = np.load(str(EMB_FILE))
            final_count = int(final_arr.shape[0])
        else:
            final_count = int(new_emb_array.shape[0])
    except Exception:
        final_count = None

    cfg = {
        'model': args.model,
        'generated_at': int(time.time()),
        'count': final_count
    }
    try:
        with open(CFG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print(f"✅ config salvo em: {CFG_FILE}")
    except Exception as e:
        print(f"⚠️ Falha ao salvar config: {e}")

    if failed:
        print(f"⚠️ Alguns documentos falharam ao gerar embedding: {len(failed)} itens. Exemplos de índices: {failed[:10]}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reindexar vetores em memoria/vectors')
    parser.add_argument('--model', type=str, default=os.getenv('EMBEDDING_MODEL', 'models/text-embedding-004'), help='Nome do modelo de embeddings')
    parser.add_argument('--batch', type=int, default=1, help='Batch size (não usado intensamente; chamado por item)')
    parser.add_argument('--sleep-between', type=float, default=0.0, help='Delay entre requisições (s)')
    parser.add_argument('--progress', type=int, default=10, help='Intervalo para logs de progresso')
    parser.add_argument('--skip-api-check', action='store_true', help='Pular verificação de disponibilidade da API')
    parser.add_argument('--incremental', action='store_true', help='Modo incremental: apenas novos documentos serão indexados e anexados')
    parser.add_argument('--limit', type=int, default=0, help='Limitar número de documentos a indexar (0 = sem limite)')
    args = parser.parse_args()
    if not args.skip_api_check:
        ok, info = check_api_available(args.model)
        if not ok:
            print(f"❌ Verificação de API falhou: {info}")
            print("Dica: rode com --skip-api-check se tiver certeza das credenciais ou corrija as chaves.")
            raise SystemExit(1)
        else:
            print(f"✅ Verificação de API: {info}")
    main(args)
