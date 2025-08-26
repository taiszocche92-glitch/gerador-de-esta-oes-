# TESTE: Provisionar SERPAPI_KEY e executar busca localmente

Arquivos relevantes:
- Sanitizador e cache: [`backend-python-agent/web_search.py`](backend-python-agent/web_search.py:1)
- Integração no fluxo: [`backend-python-agent/main.py`](backend-python-agent/main.py:1565)
- Exemplo de variáveis: [`backend-python-agent/.env.example`](backend-python-agent/.env.example:1)

Passos rápidos (Windows - cmd.exe)

1) Criar arquivo de ambiente (na pasta `backend-python-agent`) baseado em `.env.example`:
set SERPAPI_KEY=YOUR_SERPAPI_KEY_HERE
set WEB_SEARCH_CACHE_TTL=86400
set WEB_SEARCH_CACHE_PATH=memoria/web_search_cache.json

Ou crie `backend-python-agent/.env` com as mesmas chaves (o código usa python-dotenv).

2) Instalar dependências e rodar servidor (fora da pasta backend, no root do projeto):
python -m venv .venv
.venv\Scripts\activate
pip install -r backend-python-agent/requirements.txt
uvicorn backend-python-agent.main:app --host 127.0.0.1 --port 8080 --reload

3) Verificar health:
curl http://127.0.0.1:8080/health

Teste da rota de criação (envios por form)
Exemplo usando curl (Windows cmd / PowerShell compatível):
curl -v -X POST "http://127.0.0.1:8080/api/agent/start-creation" ^
  -F "tema=hipertensão" ^
  -F "especialidade=Clínica Médica" ^
  -F "enable_web_search=1" ^
  -F "pdf_reference=@C:\caminho\para\arquivo.pdf"

Observações importantes:
- A busca só roda se `SERPAPI_KEY` estiver presente e `enable_web_search=1` for enviada pelo frontend. Veja o toggle em [`src/pages/AdminView.vue`](src/pages/AdminView.vue:17).
- O cache padrão está em `memoria/web_search_cache.json` (configurável por `WEB_SEARCH_CACHE_PATH`).
- Se ocorrerem erros de quota/respostas 429, o módulo tentará retry com backoff (configurável via WEB_SEARCH_MAX_RETRIES, WEB_SEARCH_BACKOFF_FACTOR).
- Não comite chaves reais no repositório; use um secret manager em produção.

Se quiser, gero um script .bat para automatizar os passos de ativação do venv e execução do uvicorn.
