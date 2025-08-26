# -*- coding: utf-8 -*-
"""
web_search.py - Busca web programática com SerpAPI + cache simples

Uso:
  export SERPAPI_KEY=...
  from web_search import search_web
  results = search_web("diretrizes hipertensão Brasil", max_results=5)
"""
import os
import time
import json
import requests
import re
import random
from typing import List, Dict, Optional

CACHE_PATH = os.getenv("WEB_SEARCH_CACHE_PATH", "memoria/web_search_cache.json")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TTL_SECONDS = int(os.getenv("WEB_SEARCH_CACHE_TTL", str(24*3600)))  # default 24h
SERPAPI_URL = "https://serpapi.com/search"

def _load_cache() -> Dict:
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache: Dict) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _sanitize_text(text: Optional[str]) -> str:
    """
    Sanitiza e (opcionalmente) redige PII de snippets:
    - colapsa espaços
    - redige emails, CPFs, telefones e sequências longas de dígitos
    - preserva números clínicos com unidades (ex: "120 mmHg", "80%", "3.5 mmol/L")
    - limita o comprimento (configurável via WEB_SEARCH_SNIPPET_MAX)
    - redaction pode ser desabilitado via WEB_SEARCH_REDACT_PII=0
    - proteger padrões clínicos pode ser controlado por WEB_SEARCH_REDACT_EXCEPT_CLINICAL=1 (padrão)
    """
    if not text:
        return ""
    txt = " ".join(text.split())
    # Verificar flags
    redact_flag = os.getenv("WEB_SEARCH_REDACT_PII", "1")
    redact = str(redact_flag).lower() not in ("0", "false", "no")
    protect_clinical_flag = os.getenv("WEB_SEARCH_REDACT_EXCEPT_CLINICAL", "1")
    protect_clinical = str(protect_clinical_flag).lower() not in ("0", "false", "no")

    # Protegendo padrões clínicos antes da redação
    protected_map = {}
    if protect_clinical and txt:
        clinical_patterns = [
            r'\b\d{1,3}\s?mmHg\b',
            r'\b\d{1,3}\s?%(\b|$)',
            r'\b\d+(\.\d+)?\s?(mg|g|kg|ml|l|µg|mcg)\b',
            r'\b\d+(\.\d+)?\s?(mmol\/l|mmol\/L|mmol|mmol\/L|mmol/L)\b',
            r'\b\d+(\.\d+)?\s?(cmH2O|cm H2O)\b',
            r'\b\d+(\.\d+)?\s?(bpm)\b'
        ]
        for i, pat in enumerate(clinical_patterns):
            for m in re.finditer(pat, txt, flags=re.IGNORECASE):
                key = f"__CLINICAL_{i}_{len(protected_map)}__"
                protected_map[key] = m.group(0)
                txt = txt.replace(m.group(0), key)

    if redact:
        try:
            # Emails
            txt = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', txt)
            # CPF (formato 000.000.000-00 ou somente dígitos)
            txt = re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '[REDACTED_CPF]', txt)
            # Telefones (variações)
            txt = re.sub(r'\b\+?\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{4,5}[\-]?\d{4}\b', '[REDACTED_PHONE]', txt)
            # Sequências longas de dígitos (possíveis IDs/CPFs sem formatação)
            txt = re.sub(r'\b\d{6,}\b', '[REDACTED_NUMBER]', txt)
        except Exception:
            # Em caso de erro na regex, fallback para versão curta sem redaction
            txt = " ".join(txt.split())

    # Restaurar padrões clínicos protegidos
    if protected_map:
        for k, v in protected_map.items():
            txt = txt.replace(k, v)

    # Limitar tamanho do snippet (padrão 800 caracteres)
    try:
        max_len = int(os.getenv("WEB_SEARCH_SNIPPET_MAX", "800"))
    except Exception:
        max_len = 800
    if len(txt) > max_len:
        truncated = txt[:max_len]
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        txt = truncated + "..."
    return txt

def search_web(query: str, max_results: int = 5, use_cache: bool = True) -> List[Dict]:
    """
    Perform a web search using SerpAPI and return a list of results:
    [{ 'title':..., 'snippet':..., 'link':... }, ...]
    Implements simple retry/backoff with jitter and returns cached results on persistent failure.
    Raises RuntimeError if SERPAPI_KEY not configured.
    """
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY not configured in environment")
 
    cache_key = f"serp::{query}::{max_results}"
    if use_cache:
        cache = _load_cache()
        entry = cache.get(cache_key)
        if entry and (time.time() - entry.get("ts", 0) < TTL_SECONDS):
            return entry.get("results", [])[:max_results]
 
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": max_results,
        "location": "Brazil",
        "hl": "pt"
    }
 
    # Retry/backoff configuration (env vars)
    try:
        max_retries = int(os.getenv("WEB_SEARCH_MAX_RETRIES", "3"))
    except Exception:
        max_retries = 3
    try:
        backoff_factor = float(os.getenv("WEB_SEARCH_BACKOFF_FACTOR", "0.5"))
    except Exception:
        backoff_factor = 0.5
    max_backoff = float(os.getenv("WEB_SEARCH_MAX_BACKOFF", "10"))
 
    last_error = None
    for attempt in range(0, max_retries + 1):
        try:
            resp = requests.get(SERPAPI_URL, params=params, timeout=10)
            # If we get a 429 or 5xx, treat as transient and retry
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                raise requests.HTTPError(f"Transient HTTP error: {resp.status_code}", response=resp)
            resp.raise_for_status()
            data = resp.json()
 
            results = []
            organic = data.get("organic_results") or data.get("organic", []) or []
            for r in organic[:max_results]:
                title = r.get("title") or ""
                snippet = _sanitize_text(r.get("snippet") or r.get("snippet_highlighted") or "")
                link = r.get("link") or r.get("source") or r.get("displayed_link") or ""
                results.append({"title": title, "snippet": snippet, "link": link})
 
            # fallback to top if empty
            if not results:
                top = data.get("top", {}) or data.get("knowledge_graph", {}) or {}
                if top:
                    title = top.get("title") or ""
                    snippet = _sanitize_text(top.get("snippet") or top.get("description"))
                    link = top.get("link") or top.get("source") or ""
                    if title or snippet:
                        results.append({"title": title, "snippet": snippet, "link": link})
 
            # save to cache
            if use_cache:
                try:
                    cache = _load_cache()
                    cache[cache_key] = {"ts": time.time(), "results": results}
                    _save_cache(cache)
                except Exception:
                    pass
 
            return results[:max_results]
 
        except Exception as e:
            last_error = e
            # On final attempt, if cache exists return cached results, otherwise raise
            if attempt == max_retries:
                if use_cache:
                    cache = _load_cache()
                    entry = cache.get(cache_key)
                    if entry:
                        return entry.get("results", [])[:max_results]
                # re-raise the last error
                raise
            # Otherwise sleep with exponential backoff + jitter
            sleep_seconds = min(max_backoff, backoff_factor * (2 ** attempt))
            # add jitter up to 20% of sleep_seconds
            jitter = random.uniform(0, 0.2 * sleep_seconds)
            sleep_time = sleep_seconds + jitter
            time.sleep(sleep_time)
            continue
