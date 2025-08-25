# README do Backend - Gerador de Análise e Acompanhamento do Projeto

---
## 1. Como o Código "Pensa" e Utiliza os Dados de Referência

### 1.1. Ingestão dos PDFs (`pdf_referencias`)
- O script `ingest_and_index.py` executa as seguintes etapas:
  1. Varre a pasta `pdf_referencias` e identifica todos os arquivos PDF.
  2. Para cada PDF:
     - Extrai o texto completo e relevante, ignorando pastas como `flashcards` ou `slides`.
     - Realiza chunking (divide o texto em partes menores para facilitar o processamento).
     - Gera embeddings (vetores numéricos que representam o significado dos textos) usando modelos Gemini/Gemma.
     - Lê dados adicionais do Firestore, se disponível, e indexa como documentos extras.
  3. Salva os resultados em:
     - `memoria/vectors/embeddings.npy`: matriz de embeddings dos textos.
     - `memoria/vectors/metadata.jsonl`: metadados de cada trecho indexado.
     - `memoria/vectors/id_map.json`: mapa de IDs para rastreabilidade dos trechos.

### 1.2. Estrutura da pasta `memoria`
- **`memoria/vectors/`**: Armazena os embeddings e metadados usados para busca por similaridade.
- **`memoria/contexto_otimizado/`**: Contém arquivos markdown com contextos otimizados para cada fase do sistema (ex: análise, roteiros, impressos, checklist). Usados para enriquecer prompts e respostas.
- **`memoria/monitoring/`**: Guarda configurações e dados de monitoramento do sistema, como métricas e alertas.
- **`memoria/versoes/`**: Gerencia versões dos dados e configurações, permitindo histórico, rollback e rastreabilidade.
- **`memoria/aprendizados_usuario.jsonl`**: Registra aprendizados e regras que o sistema “aprendeu” durante o uso, permitindo adaptação e evolução.
- **`memoria/config_memoria.json`**: Configurações do sistema de memória, indicando caminhos, estrutura dos dados e arquivos base.

### 1.3. Lógica no `main.py`
- Ao inicializar, o backend:
  1. Carrega configurações e dados da pasta `memoria` usando funções como `load_local_memory_config` e `initialize_local_memory_system`.
  2. Lê arquivos de contexto otimizado, referências base e aprendizados do usuário.
  3. Mantém sistemas de versionamento e monitoramento ativos.
- Quando o usuário faz uma consulta ou solicita geração de estação:
  1. O sistema utiliza os embeddings para buscar trechos mais similares à pergunta ou contexto.
  2. Utiliza contextos otimizados, regras aprendidas e seções do `referencias.md` para enriquecer o prompt enviado ao modelo Gemini.
  3. O modelo Gemini processa o prompt e retorna uma resposta ou sugestão de estação.
  4. O backend retorna o resultado ao frontend, que exibe ao usuário.
  5. O sistema registra aprendizados, atualiza histórico e pode versionar dados conforme necessário.

### 1.4. Como o código "pensa"
- Todo PDF em `pdf_referencias` é tratado como fonte de conhecimento médico.
- O conhecimento é processado e transformado em vetores para busca rápida e inteligente.
- Contextos, regras e aprendizados enriquecem as respostas e adaptam o comportamento conforme o uso.
- Histórico, versões e monitoramento garantem evolução e segurança.

### 1.5. Fluxo detalhado de uma Consulta ou Geração de Estação
1. O usuário faz uma pergunta ou solicita a geração de uma estação via frontend.
2. O backend recebe a requisição e identifica o tipo de consulta (ex: busca por similaridade, geração de estação, análise).
3. O sistema consulta os embeddings em `memoria/vectors/` para encontrar os trechos mais relevantes dos PDFs processados.
4. Contextos otimizados, regras aprendidas e seções do `referencias.md` são usados para enriquecer o prompt enviado ao modelo Gemini ou para compor a resposta.
5. O modelo Gemini processa o prompt e retorna uma resposta ou sugestão de estação.
6. O backend retorna o resultado ao frontend, que exibe ao usuário.
7. O sistema registra aprendizados, atualiza histórico e pode versionar dados conforme necessário.

---
## 2. Estrutura Recomendada do Backend
- **Raiz:** Apenas arquivos essenciais: `main.py`, `rag.py`, `ingest_and_index.py`, `gemini_client.py`, `.env`, `requirements.txt`, `dockerfile`, `serviceAccountKey.json`, `gerador.md`, `referencias.md`, `MODELOS_GEMINI_ATUAIS.md`, `OTIMIZACAO_CONCLUIDA.md`, `gabaritoestacoes.json`.
- **Pastas:**
  - `memoria/`: Dados, embeddings, versões, contexto otimizado e monitoramento.
  - `provas inep/`: Provas e materiais do exame Revalida organizados por ano/semestre.
  - `tests/`: Testes automatizados e de validação do sistema.
  - `tests_essenciais/`: Scripts de diagnóstico rápido e validação de ambiente.
  - `scripts/`: Utilitários e scripts de troubleshooting.
  - `pdf_referencias/`: PDFs usados como fonte de dados para ingestão e indexação.
  - `.venv/`, `__pycache__/`: Ambientes e caches Python (não versionar).
  - `api_docs/`: Documentação dos endpoints da API.

---
## 3. Recomendações Técnicas
- Manter arquivos de teste e utilitários em suas respectivas pastas.
- Não versionar `.venv/` e `__pycache__/`.
- Revisar periodicamente a raiz para evitar poluição.
- Centralizar futuros scripts de teste em `tests_essenciais/` e automatizados em `tests/`.
- Expandir documentação dos endpoints.
- Padronizar tratamento de erros e mensagens.
- Avaliar separação de funções utilitárias em módulos.

---
## 4. Histórico Técnico
- Estrutura reorganizada: arquivos de teste e utilitários movidos para pastas adequadas.
- Arquivos desnecessários e duplicados removidos.
- Documentação e recomendações atualizadas para facilitar manutenção futura.

---
## 5. Tarefas Pendentes e Checklist

### Integração frontend-backend
- [x] Centralizar URLs de endpoints da API em um arquivo/config do frontend (`src/utils/api.js`).
- [x] Analisar o arquivo `AdminView.vue` para identificar chamadas aos endpoints do backend.
- [x] Listar e documentar os endpoints disponíveis no backend.
- [x] Relacionar cada chamada do frontend com o respectivo endpoint e fluxo de dados.
- [x] Relatar possíveis melhorias ou ajustes necessários na integração.
- [x] Expandir testes automatizados para cada endpoint, incluindo testes de integração frontend-backend (script `tests/test_endpoints.py` criado).

### Testes e Documentação
- [ ] Realizar testes de ponta a ponta nos endpoints da API.
- [x] Expandir documentação dos endpoints com exemplos de uso, parâmetros e retornos em `api_docs/endpoints.md`.
- [ ] Adicionar testes de depuração local para endpoints principais usando scripts em `backend-python-agent/tests/`.

### Organização e Segurança
- [x] Pasta `pdf_referencias` criada para centralizar os arquivos PDF usados como fonte de dados para ingestão e indexação.
- [x] Arquivo `README.md` criado na pasta, explicando sua função e como utilizar os PDFs no sistema.
- [x] Garantir que arquivos de configuração e credenciais estejam versionados corretamente e protegidos.
- [ ] Centralizar configurações sensíveis (paths, chaves, URLs) em um único arquivo/config.
- [ ] Padronizar tratamento de erros e mensagens.
- [ ] Avaliar separação de funções utilitárias em módulos.
- [ ] Melhorar rastreabilidade de logs e auditoria no backend.

---
## Relatórios das Tarefas Concluídas
- Integração frontend-backend: mapeamento concluído, documentação em andamento.
- Organização dos dados de referência: pasta e README criados, fluxo de ingestão documentado.
- Auditoria e logs: parcialmente implementado, sugerido expandir.

---
## Arquivos mapeados relevantes
- Frontend: `src/views/dashboard/AnalyticsUserTable.vue`, `src/views/dashboard/UserRanking.vue`, `src/views/pages/account-settings/AccountSettingsSecurity.vue`, `src/utils/fetch-interceptor.js`, `src/stores/userStore.js`, `src/utils/api.js` (sugerido), `trashX/adminviewtrue.vue.txt` (referência de integração).
- Backend: `main.py`, `rag.py`, `ingest_and_index.py`, `gemini_client.py`, `memoria/`, `api_docs/`, `tests/`, `tests_essenciais/`, `referencias.md`, `MODELOS_GEMINI_ATUAIS.md`.
- Raiz do projeto: `firebase.json` (configuração de endpoints externos), `apikeys.txt`, `jsconfig.json`, `package.json`, `vite.config.js`.

---
## Observações para depuração e uso de terminal
- Nunca execute ou rode `python main.py` no terminal principal, pois ele já está rodando e deve permanecer ativo.
- Sempre que for rodar qualquer comando de depuração, testes ou scripts, abra um novo terminal (PowerShell) e utilize apenas este para rodar comandos, evitando múltiplos terminais abertos desnecessariamente.
- Nunca rode comandos em cima dos terminais já abertos para o backend principal.
- Relate e siga estas observações sempre que modificar este arquivo.

---
## Diagnóstico de falha nos testes automatizados dos endpoints

### Erro encontrado
- O script `tests/test_endpoints.py` retorna o erro:
  `ConnectionRefusedError: [WinError 10061] Nenhuma conexão pôde ser feita porque a máquina de destino as recusou ativamente`
- Isso indica que o backend FastAPI não está aceitando conexões na porta 8080 (`localhost:8080`).
- O erro ocorre em todas as chamadas HTTP do teste, sugerindo que o servidor não está rodando ou está rodando em outra porta/endereço.

### Diagnóstico detalhado
- O arquivo `main.py` define o ponto de entrada local:
  ```python
  if __name__ == "__main__":
      uvicorn.run(app, host="127.0.0.1", port=8080)
  ```
- O backend deve estar rodando em `localhost:8080` para que os testes funcionem.
- Possíveis causas:
  1. O backend não está rodando (processo não iniciado ou caiu).
  2. O backend está rodando em outra porta/endereço (verifique configurações e logs).
  3. Firewall ou restrição de rede bloqueando a porta 8080.
  4. O backend está rodando, mas em modo de produção ou container, com porta diferente.
- Recomendações:
  - Verifique se o backend está ativo e ouvindo em `localhost:8080`.
  - Use o comando `netstat -ano | findstr :8080` no PowerShell para checar se a porta está aberta.
  - Confira se há logs de erro no terminal do backend.
  - Se necessário, ajuste o script de teste para usar a porta correta.
  - Se rodar em container/docker, verifique o mapeamento de portas.

### Próximos passos
- Não prossiga com novas tarefas até garantir que o backend está rodando corretamente na porta esperada.
- Após corrigir o backend, rode novamente o teste e registre o resultado.
- Se persistir o erro, colete logs do backend e do sistema para análise mais profunda.

---
## Diagnóstico adicional: Falha na importação do numpy na rota RAG

### Erro encontrado
- Mensagem: `Error importing numpy: you should not try to import numpy from its source directory; please exit the numpy source tree, and relaunch your python interpreter from there.`
- Ocorre ao tentar incluir a rota RAG no backend (`main.py`).

### Diagnóstico detalhado
- O erro indica que o Python está tentando importar o pacote `numpy` diretamente da pasta onde o código fonte do numpy está localizado, e não de uma instalação padrão via pip.
- Possíveis causas:
  1. O diretório atual do terminal está dentro da pasta do código fonte do numpy (exemplo: `site-packages/numpy/` ou pasta clonada do GitHub).
  2. O ambiente virtual está corrompido ou o numpy foi instalado manualmente/copiado.
  3. O `PYTHONPATH` está configurado para incluir o diretório fonte do numpy.
- Recomendações:
  - Certifique-se de que o terminal está na raiz do projeto e não dentro da pasta do numpy.
  - Execute `pip show numpy` para verificar o local de instalação.
  - Se necessário, reinstale o numpy: `pip uninstall numpy` seguido de `pip install numpy`.
  - Verifique se não há pastas chamadas `numpy` no diretório do projeto que possam conflitar.
  - Reinicie o terminal após corrigir o ambiente.

### Observação sobre alerta de memória
- O alerta de memória alta (`memoria_alta: Uso de memória: 85.8%`) indica que o sistema está consumindo muitos recursos.
- Recomenda-se monitorar o uso de memória e fechar aplicações desnecessárias.
- Se o alerta persistir, pode ser necessário otimizar o código ou aumentar os recursos do sistema.

---
*Diagnóstico registrado para rastreabilidade e ação futura. Não prossiga com testes da rota RAG até corrigir o ambiente do numpy.*

---
## AVISO IMPORTANTE SOBRE AMBIENTE VIRTUAL (.venv)

**Sempre ative o ambiente virtual antes de instalar dependências ou rodar o backend!**

- O ambiente virtual `.venv` garante que todas as bibliotecas usadas pelo projeto fiquem isoladas, evitando conflitos com outros projetos ou com o Python do sistema.
- Para ativar o ambiente virtual, navegue até a pasta `backend-python-agent` e execute:
  ```powershell
  .\.venv\Scripts\activate
  ```
- Após ativar, o terminal mostrará o nome do ambiente antes do prompt (exemplo: `(.venv) PS ...`).
- Instale pacotes SEMPRE com o ambiente ativado:
  ```powershell
  pip install nome-do-pacote
  ```
- Você só precisa instalar os pacotes:
  - Na primeira vez que clonar/criar o projeto
  - Ao adicionar/atualizar dependências
  - Se o ambiente virtual for apagado ou corrompido
  - Se aparecer erro de pacote ausente
- Para rodar o backend, execute SEMPRE com o ambiente virtual ativado:
  ```powershell
  python main.py
  ```
- O comando `python main.py` deve ser rodado dentro da pasta `backend-python-agent` e com o ambiente virtual ativado.
- Não é necessário reinstalar os pacotes toda vez, apenas garantir que o ambiente está ativado.

**Nunca instale pacotes no Python global do sistema para este projeto!**
