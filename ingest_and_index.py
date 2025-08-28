r"""Ingestão e indexação (Fase 1)

- Varre a pasta `downloads/` procurando arquivos PDF (recursivo).
- Ignora PDFs que estiverem dentro de qualquer pasta cujo nome seja 'flashcards' ou 'slides'.
- Extrai texto dos PDFs (PyMuPDF), faz chunking e gera embeddings via Gemini/Gemma.
- Também lê a coleção Firestore `estacoes_clinicas` (se as credenciais estiverem
  disponíveis) e indexa cada estação como um documento adicional.
- Salva embeddings numpy em `memoria/vectors/embeddings.npy` e metadados em
  `memoria/vectors/metadata.jsonl` e `memoria/vectors/id_map.json`.

Como usar (PowerShell):
    py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python ingest_and_index.py --base-dir downloads --out-dir memoria/vectors --rebuild --model gemma-3-n4

"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

try:
    import fitz  # PyMuPDF
except Exception as e:
    print("Erro ao importar PyMuPDF (fitz). Instale 'PyMuPDF' antes de executar.")
    raise

try:
    import google.generativeai as genai
except Exception:
    genai = None

import numpy as np

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:
    firebase_admin = None

IGNORED_DIR_NAMES = {"flashcards", "slides"}


def is_ignored_path(path: Path) -> bool:
    """Retorna True se algum componente do caminho (exceto o arquivo) for uma pasta ignorada."""
    for part in path.parent.parts:
        if part.lower() in IGNORED_DIR_NAMES:
            return True
    return False


def find_pdfs(base_dir: Path):
    """Gera caminhos de arquivos PDF, ignorando subpastas especificadas."""
    for p in base_dir.rglob("*.pdf"):
        if is_ignored_path(p):
            continue
        yield p


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrai texto simples do PDF usando PyMuPDF (fitz)."""
    text_parts = []
    doc = fitz.open(str(pdf_path))
    for page in doc:
        try:
            # PyMuPDF: get_text é o método correto; fallback para extrair texto bruto se não existir
            text = getattr(page, "get_text", lambda: "")()
        except Exception:
            text = ""
        if text:
            text_parts.append(text)
    doc.close()
    return "\n\n".join(text_parts)


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200):
    """Chunk de texto por caracteres (rápido)."""
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = max(start + chunk_size - overlap, end)
        if end == text_len:
            break
    return chunks


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


from typing import Optional

def init_firebase(service_account_path: Optional[Path] = None):
    if firebase_admin is None:
        print("firebase_admin não instalado; pulando ingestão de estações do Firestore.")
        return None
    try:
        if not firebase_admin._apps:
            if isinstance(service_account_path, Path) and service_account_path and service_account_path.exists():
                cred = credentials.Certificate(str(service_account_path))
                firebase_admin.initialize_app(cred)
            else:
                if not firebase_admin._apps:
                    firebase_admin.initialize_app()
        db = firestore.client()
        return db
    except Exception as e:
        print(f"Falha ao inicializar Firebase: {e}")
        return None


def index_documents(items, model_name, out_dir: Path, rebuild=False):
    """Gera embeddings via API (google.generativeai) e salva embeddings numpy + metadados.

    A função tenta o `model_name` recebido e, se falhar, testa uma lista de candidatos.
    """
    ensure_dir(out_dir)
    embeddings_file = out_dir / "embeddings.npy"
    meta_file = out_dir / "metadata.jsonl"
    id_map_file = out_dir / "id_map.json"
    config_file = out_dir / "config.json"

    texts = [it['text'] for it in items]
    ids = [it['id'] for it in items]

    if not texts:
        print("Nenhum texto para indexar.")
        return

    # configurar chave (procura GEMINI_API_KEY_* no .env)
    api_key = None
    for i in range(1, 6):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k:
            api_key = k
            break
    if not api_key and os.getenv('GEMINI_API_KEY'):
        api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("Nenhuma GEMINI_API_KEY encontrada no ambiente. Defina GEMINI_API_KEY or GEMINI_API_KEY_1..5 no .env")
        return

    if genai is None:
        print("google.generativeai não disponível. Instale 'google-generativeai' e tente novamente.")
        return

    # configurar cliente
    try:
        getattr(genai, "configure")(api_key=api_key)
    except Exception:
        print("Erro ao configurar a chave da API do Gemini.")

    print("Gerando embeddings via API — isso consome créditos do Google Cloud.")

    # candidatos de modelo (começa pelo solicitado)
    candidates = []
    if model_name:
        candidates.append(model_name)
    # adicionar candidatos conhecidos; 'gemma-3-n4' está incluído
    extras = ["gemma-3-n4", "gemma-3-nano", "gemma-3-large", "models/embedding-001", "textembedding-gecko-001", "gemini-1.5", "embedding-001"]
    for e in extras:
        if e not in candidates:
            candidates.append(e)

    # testar modelos em ordem até encontrar um compatível
    chosen_model = None
    test_input = ["teste de compatibilidade de embeddings"]
    # configurar chave (usa GEMINI_API_KEY_1..8 na ordem)
    try:
        from gemini_client import configure_first_available
        used = configure_first_available()
        print(f"Chave usada para teste de embeddings: {used}")
    except Exception:
        used = None

    for cand in candidates:
        try:
            print(f"Testando modelo de embeddings: {cand}")
            resp_test = getattr(genai, "embed_content")(model=cand, content=test_input)
            if isinstance(resp_test, dict) and resp_test.get('embedding'):
                chosen_model = cand
                break
            if hasattr(resp_test, 'embedding'):
                chosen_model = cand
                break
        except Exception as e:
            print(f"Modelo {cand} não é compatível: {e}")
            continue

    if not chosen_model:
        print("Nenhum modelo de embeddings compatível encontrado. Ajuste o parâmetro --model ou verifique a chave/API.")
        return

    print(f"Usando modelo de embeddings: {chosen_model}")

    batch_size = 16
    all_embs = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Chamando API de embeddings"):
        batch = texts[i:i+batch_size]
        try:
            resp = getattr(genai, "embed_content")(model=chosen_model, content=batch)
            if isinstance(resp, dict) and 'embedding' in resp:
                emb_vectors = resp['embedding']
            elif hasattr(resp, 'embedding'):
                emb_vectors = resp.get('embedding', [])
            else:
                emb_vectors = list(resp)
        except Exception as e:
            print(f"Erro ao chamar API de embeddings com {chosen_model}: {e}")
            return

        for v in emb_vectors:
            all_embs.append(np.array(v, dtype=np.float32))

    if not all_embs:
        print("Nenhum embedding gerado.")
        return

    embeddings = np.vstack(all_embs)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    np.save(str(embeddings_file), embeddings)

    mode = 'w'
    if meta_file.exists() and not rebuild:
        mode = 'a'

    with open(meta_file, mode, encoding='utf-8') as f:
        for i, doc_id in enumerate(ids):
            meta = {
                'id': doc_id,
                'meta': items[i].get('meta', {}),
                'text_preview': items[i]['text'][:500].replace('\n', ' ') + ("..." if len(items[i]['text'])>500 else ''),
                'indexed_at': datetime.utcnow().isoformat()
            }
            f.write(json.dumps(meta, ensure_ascii=False, default=str) + "\n")

    id_map = {str(i): ids[i] for i in range(len(ids))}
    with open(id_map_file, 'w', encoding='utf-8') as f:
        json.dump(id_map, f, ensure_ascii=False)

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump({'model': chosen_model, 'indexed_at': datetime.utcnow().isoformat(), 'items_count': len(ids), 'embeddings_file': str(embeddings_file.name)}, f, ensure_ascii=False)

    print(f"Embeddings salvos em: {embeddings_file}\nMetadados em: {meta_file}\nID map em: {id_map_file}")


def main(base_dir: str = "downloads", out_dir: str = "memoria/vectors", rebuild: bool = False, service_account: str = "serviceAccountKey.json", model_name: str = "gemini-embedding-1.0"):
    base = Path(base_dir)
    out = Path(out_dir)
    ensure_dir(out)

    items = []

    # 0) Indexar estações locais (provas INEP) se existir
    local_stations_dir = Path("provas inep")
    if local_stations_dir.exists():
        print(f"Procurando estações locais em: {local_stations_dir.resolve()}")
        local_count = 0
        for j in local_stations_dir.rglob("*.json"):
            try:
                with open(j, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                text_parts = []
                for key in ['titulo', 'title', 'enunciado', 'resumo', 'questao', 'descricao', 'conteudo']:
                    if isinstance(data.get(key), str):
                        text_parts.append(data.get(key))
                if not text_parts:
                    text_parts.append(json.dumps(data, ensure_ascii=False, default=str))
                full_text = "\n\n".join(text_parts)
                doc_id = f"localprova::{j.relative_to(local_stations_dir)}"
                items.append({'id': doc_id, 'text': full_text, 'meta': {'source': 'local_prova', 'path': str(j)}})
                local_count += 1
            except Exception as e:
                print(f"Falha ao ler estação local {j}: {e}")
        print(f"Estações locais indexadas (provas inep): {local_count}")

    # 1) Indexar PDFs locais
    print(f"Procurando PDFs em: {base.resolve()}")
    pdf_paths = list(find_pdfs(base))
    print(f"PDFs encontrados (após filtro): {len(pdf_paths)}")
    for p in tqdm(pdf_paths, desc="Processando PDFs"):
        try:
            text = extract_text_from_pdf(p)
            if not text or len(text.strip()) < 100:
                continue
            chunks = chunk_text(text)
            for idx, chunk in enumerate(chunks):
                doc_id = f"pdf::{p.relative_to(base)}::chunk{idx}"
                items.append({'id': doc_id, 'text': chunk, 'meta': {'source': 'pdf', 'path': str(p), 'chunk_index': idx}})
        except Exception as e:
            print(f"Falha ao processar {p}: {e}")

    # 2) Indexar estações do Firestore (se possível)
    db = init_firebase(Path(service_account))
    if db:
        try:
            docs = db.collection('estacoes_clinicas').stream()
            count = 0
            for d in docs:
                data = d.to_dict() or {}
                text_parts = []
                for key in ['titulo', 'resumo', 'conteudo', 'descricao']:
                    if key in data and isinstance(data[key], str):
                        text_parts.append(data[key])
                if not text_parts:
                    text_parts.append(json.dumps(data, ensure_ascii=False, default=str))
                full_text = "\n\n".join(text_parts)
                doc_id = f"estacao::{d.id}"
                items.append({'id': doc_id, 'text': full_text, 'meta': {'source': 'firestore', 'doc_id': d.id}})
                count += 1
            print(f"Estações indexadas do Firestore: {count}")
        except Exception as e:
            print(f"Erro ao ler estacoes_clinicas do Firestore: {e}")

    # 3) Gerar embeddings e salvar índice
    if items:
        index_documents(items, model_name=model_name, out_dir=out, rebuild=rebuild)
    else:
        print("Nenhum item para indexar.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingestão e indexação de PDFs + estações (Firestore)")
    parser.add_argument("--base-dir", type=str, default="downloads")
    parser.add_argument("--out-dir", type=str, default="memoria/vectors")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--model", type=str, default="gemini-embedding-1.0", help="Modelo de embedding para tentar primeiro (p.ex. 'gemini-embedding-1.0', 'gemma-3-n4' ou 'gemma-3-nano')")
    parser.add_argument("--service-account", type=str, default="serviceAccountKey.json")
    args = parser.parse_args()

    main(base_dir=args.base_dir, out_dir=args.out_dir, rebuild=args.rebuild, service_account=args.service_account, model_name=args.model)
