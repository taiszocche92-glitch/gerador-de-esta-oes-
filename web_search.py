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
    if not text:
        return ""
    # basic sanitization: strip, collapse whitespace, limit length
    txt = " ".join(text.split())
    if len(txt) > 2000:
        txt = txt[:2000] + "..."
    return txt

def search_web(query: str, max_results: int = 5, use_cache: bool = True) -> List[Dict]:
    """
    Perform a web search using SerpAPI and return a list of results:
    [{ 'title':..., 'snippet':..., 'link':... }, ...]
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

    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        # on failure, return cached if available otherwise raise
        if use_cache and 'cache' in locals() and cache.get(cache_key):
            return cache[cache_key].get("results", [])[:max_results]
        raise

    results = []
    organic = data.get("organic_results") or data.get("organic", []) or []
    for r in organic[:max_results]:
        title = r.get("title") or ""
        snippet = _sanitize_text(r.get("snippet") or r.get("snippet_highlighted") or "")
        link = r.get("link") or r.get("source") or r.get("displayed_link") or ""
        results.append({"title": title, "snippet": snippet, "link": link})

    # fallback to top ads or knowledge_graph?
    if not results:
        # try other fields
        top = data.get("top", {})
        if top:
            title = top.get("title")
            snippet = _sanitize_text(top.get("snippet"))
            link = top.get("link")
            if title or snippet:
                results.append({"title": title or "", "snippet": snippet or "", "link": link or ""})

    # save to cache
    if use_cache:
        try:
            cache = _load_cache()
            cache[cache_key] = {"ts": time.time(), "results": results}
            _save_cache(cache)
        except Exception:
            pass

    return results
