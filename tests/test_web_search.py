import os
import json
import importlib.util
import importlib
from types import ModuleType
from unittest.mock import patch, Mock
import pytest

def load_module_with_env(tmp_env_vars, module_path):
    # set env for this process before loading module
    for k, v in tmp_env_vars.items():
        os.environ[k] = v
    spec = importlib.util.spec_from_file_location("web_search_test_mod", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def make_mock_resp(json_data, status_code=200):
    m = Mock()
    m.status_code = status_code
    m.json = Mock(return_value=json_data)
    m.raise_for_status = Mock()
    return m

def test_sanitize_preserves_clinical_and_redacts_pii():
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web_search.py"))
    mod = load_module_with_env({"WEB_SEARCH_REDACT_PII": "1", "WEB_SEARCH_REDACT_EXCEPT_CLINICAL": "1"}, module_path)
    text = "Paciente: joao@example.com, CPF 123.456.789-10, tel +55 (11) 91234-5678, PA 120 mmHg, peso 70 kg"
    out = mod._sanitize_text(text)
    assert "[REDACTED_EMAIL]" in out
    assert "[REDACTED_CPF]" in out
    assert "[REDACTED_PHONE]" in out or "[REDACTED_NUMBER]" in out
    assert "120 mmHg" in out
    assert "70 kg" in out

def test_search_web_parses_serpapi_response(tmp_path):
    cache_file = tmp_path / "cache.json"
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web_search.py"))
    env = {"SERPAPI_KEY": "fake", "WEB_SEARCH_CACHE_PATH": str(cache_file)}
    mod = load_module_with_env(env, module_path)
    fake_json = {"organic_results": [{"title": "Diretriz X", "snippet": "Texto com email test@x.com", "link": "https://ex.com/doc"}]}
    mock_resp = make_mock_resp(fake_json, 200)
    with patch("requests.get", return_value=mock_resp):
        results = mod.search_web("diretrizes X", max_results=1, use_cache=True)
    assert isinstance(results, list)
    assert results[0]["title"] == "Diretriz X"
    assert "[REDACTED_EMAIL]" in results[0]["snippet"]
    assert results[0]["link"] == "https://ex.com/doc"

def test_search_web_returns_cached_on_failure(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_key = "serp::diretrizes X::1"
    cache_data = {cache_key: {"ts": 9999999999, "results": [{"title": "Cached", "snippet": "cached snippet", "link": "https://cached/"}]}}
    cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web_search.py"))
    env = {"SERPAPI_KEY": "fake", "WEB_SEARCH_CACHE_PATH": str(cache_file)}
    mod = load_module_with_env(env, module_path)
    # simulate network failure
    with patch("requests.get", side_effect=Exception("network")):
        results = mod.search_web("diretrizes X", max_results=1, use_cache=True)
    assert results[0]["title"] == "Cached"

if __name__ == "__main__":
    pytest.main([__file__])
