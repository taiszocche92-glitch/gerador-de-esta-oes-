# Pasta pdf_referencias

Esta pasta deve ser utilizada para armazenar arquivos PDF que servirão como fonte de dados para o sistema de ingestão e indexação.

## Função
- Centralizar todos os documentos PDF que serão processados pelo script `ingest_and_index.py`.
- Permitir que novos dados sejam facilmente adicionados ao sistema de busca por similaridade e geração de estações.

## Como usar
1. Adicione os arquivos PDF desejados nesta pasta.
2. Execute o script de ingestão:
   ```
   python ingest_and_index.py --base-dir pdf_referencias --out-dir memoria/vectors --rebuild --model gemma-3-n4
   ```
3. Os dados dos PDFs serão processados e incorporados ao sistema.

## Observação
- O nome da pasta pode ser alterado no parâmetro `--base-dir` do script, caso necessário.
- Sempre mantenha esta pasta organizada para facilitar futuras ingestões.

---
*Documentação mantida pelo assistente de IA.*
