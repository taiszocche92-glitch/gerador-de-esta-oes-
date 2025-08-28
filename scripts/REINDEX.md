REINDEX — Reindexação de Embeddings

-------
Recriar `memoria/vectors/embeddings.npy` a partir de `memoria/vectors/metadata.jsonl` usando a API de embeddings configurada pelo `gemini_client` ou `google.generativeai`.

---------
1. Configure variáveis de ambiente com suas chaves Gemini (conforme `gemini_client.KEY_SLOTS`).
2. No ambiente virtual do projeto, rode:

```powershell
python scripts/reindex_vectors.py --model models/text-embedding-004 --sleep-between 0.1

Verificação prévia da API
-------------------------
O script agora testa se a API de embeddings está disponível antes de reindexar. Se quiser pular essa checagem (por exemplo em ambiente com quota já verificada), use:

```powershell
python scripts/reindex_vectors.py --skip-api-check --model models/text-embedding-004
```
```

- Se muitas entradas falharem, reveja chaves/API quota e rode novamente.

