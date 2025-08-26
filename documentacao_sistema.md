# Documentação Completa do Sistema de Estações Clínicas

## Visão Geral

Este projeto é um sistema modular para geração, gestão e análise de estações clínicas médicas, utilizando IA (Gemini) para automatizar a criação de provas, templates e documentação. O sistema possui arquitetura full-stack com backend em FastAPI (Python) e frontend em Vue.js, integrado com Firestore para persistência e Gemini API para inteligência artificial.

---

## Estrutura do Projeto

### 📁 Diretórios Principais

- **`provas inep/`**: Contém provas médicas organizadas por ano/semestre
- **`memoria/`**: Sistema de memória persistente com embeddings, versões e contexto
- **`pdf_referencias/`**: Fontes de conhecimento em formato PDF
- **`tests/`** e **`tests_essenciais/`**: Testes automatizados e scripts de diagnóstico

---

## Documentação Detalhada dos Arquivos

### 🐍 Arquivos Python (Backend)

#### [`main.py`](main.py)
- **Função**: Servidor FastAPI principal do sistema
- **Localização**: Raiz do projeto
- **Principais Componentes**:
  - Endpoints para geração de estações clínicas
  - Sistema de versionamento e auditoria
  - Integração com Firestore e Gemini API
  - Monitoramento e logs
- **Métodos Principais**:
  - `generate_station()`: Geração de estações via IA
  - `audit_station()`: Auditoria automática de estações
  - `get_memory_context()`: Recuperação de contexto otimizado
  - `save_version()`: Versionamento de dados
- **Dependências**: FastAPI, Firestore, Gemini API, numpy
- **Relações**: Integra com `gemini_client.py`, `ingest_and_index.py`, `AdminView.vue`

#### [`gemini_client.py`](gemini_client.py)
- **Função**: Configuração e gerenciamento das chaves API do Gemini
- **Localização**: Raiz do projeto
- **Principais Componentes**:
  - Sistema de seleção automática de chaves API
  - Priorização de chaves HTTP (começadas com 'AIza')
  - Fallback para métodos alternativos
- **Métodos Principais**:
  - `configure_first_available()`: Seleciona primeira chave disponível
  - `configure_specific()`: Configura chave específica
- **Dependências**: google-generativeai, python-dotenv
- **Relações**: Usado por `main.py` e `ingest_and_index.py`

#### [`ingest_and_index.py`](ingest_and_index.py)
- **Função**: Ingestão e indexação de PDFs e estações clínicas
- **Localização**: Raiz do projeto
- **Principais Componentes**:
  - Extração de texto de PDFs (PyMuPDF)
  - Chunking de textos grandes
  - Geração de embeddings via Gemini
  - Indexação de dados do Firestore
- **Métodos Principais**:
  - `extract_text_from_pdf()`: Extração de texto
  - `chunk_text()`: Divisão de textos em chunks
  - `index_documents()`: Geração de embeddings
  - `find_pdfs()`: Busca recursiva por PDFs
- **Dependências**: PyMuPDF, google-generativeai, numpy, firebase-admin
- **Relações**: Alimenta o sistema com dados para `main.py`

#### [`pyproject.toml`](pyproject.toml)
- **Função**: Configuração de ferramentas de análise estática
- **Localização**: Raiz do projeto
- **Configurações**:
  - Pylance: Desativa avisos para importações privadas
  - Pyright: Desativa avisos para acesso de atributos
- **Dependências**: Configuração de desenvolvimento

---

### 📄 Arquivos de Configuração e Templates

#### [`gabaritoestacoes.json`](gabaritoestacoes.json)
- **Função**: Template JSON para estruturação de estações clínicas
- **Localização**: Raiz do projeto
- **Estrutura**:
  - Campos de identificação (ID, título, especialidade)
  - Contexto do caso (cenário, instruções)
  - Materiais disponíveis (impressos, perguntas)
  - Checklist de avaliação (itens, pontuações)
- **Relações**: Usado como base para geração de estações em `main.py`

#### [`gerador.md`](gerador.md)
- **Função**: Documentação completa do sistema
- **Localização**: Raiz do projeto
- **Conteúdo**:
  - Fluxo de ingestão de PDFs
  - Estrutura da memória do sistema
  - Integração frontend-backend
  - Diagnóstico de erros
  - Recomendações técnicas
- **Relações**: Documenta todo o sistema, incluindo `main.py`, `AdminView.vue`, `ingest_and_index.py`

#### [`.gitignore`](.gitignore)
- **Função**: Regras para ignorar arquivos no versionamento
- **Localização**: Raiz do projeto
- **Itens Ignorados**:
  - Arquivos de ambiente (`.env`)
  - Virtual environment (`.venv/`)
  - Cache Python (`__pycache__/`)
  - Credenciais Firebase (`serviceAccountKey.json`)
  - Embeddings e vetores (`memoria/vectors/`)
  - Arquivos do sistema (`.DS_Store`, `Thumbs.db`)

---

### 🎨 Arquivos Frontend (Vue.js)

#### [`AdminView.vue`](AdminView.vue)
- **Função**: Dashboard administrativo para gestão de estações
- **Localização**: Frontend (caminho relativo)
- **Principais Componentes**:
  - Interface para geração de estações via IA
  - Sistema de fases (análise, geração, validação)
  - Tabelas de estações (recentes, editadas, não editadas)
  - Sistema de feedback e aprendizado do agente
  - Controle de versões e monitoramento
- **Métodos Principais**:
  - `handleStartCreation()`: Inicia geração de estação
  - `handleAuditStation()`: Realiza auditoria
  - `enviarFeedback()`: Envia feedback para aprendizado
  - `loadVersions()`: Carrega versões do sistema
- **Dependências**: Vue 3, Vuetify 3, Axios
- **Relações**: Comunica com `main.py` via API

---

### 📚 Arquivos de Dados (JSON)

#### Provas INEP (57 arquivos)
- **Função**: Banco de dados de provas médicas
- **Localização**: `provas inep/[ano].[semestre]/`
- **Estrutura**: JSON com estrutura padronizada
- **Conteúdo**:
  - Informações clínicas (títulos, descrições)
  - Perguntas e respostas
  - Contextos médicos específicos
- **Relações**: Indexados por `ingest_and_index.py` e usados como referência

---

## 🔄 Fluxo de Trabalho do Sistema

### 1. Ingestão de Dados
1. **PDFs**: `ingest_and_index.py` extrai textos de PDFs em `pdf_referencias/`
2. **Provas INEP**: Arquivos JSON são indexados como documentos
3. **Firestore**: Dados existentes são integrados ao sistema
4. **Embeddings**: Textos são convertidos em vetores numéricos

### 2. Geração de Estações
1. **Interface**: Usuário preenche tema e especialidade em `AdminView.vue`
2. **Backend**: `main.py` recebe requisição e busca contexto relevante
3. **IA**: Gemini gera resumo clínico e propostas estratégicas
4. **Template**: `gabaritoestacoes.json` estrutura o resultado final
5. **Armazenamento**: Estação salva no Firestore com versionamento

### 3. Auditoria e Validação
1. **Análise**: Sistema verifica qualidade e completude
2. **Feedback**: Usuários podem fornecer orientações
3. **Melhoria**: Regras são aprendidas e aplicadas futuramente

### 4. Monitoramento e Versões
1. **Controle**: Todas as alterações são versionadas
2. **Auditoria**: Histórico completo de modificações
3. **Monitoramento**: Métricas de desempenho e qualidade

---

## 🛠️ Tecnologias e Dependências

### Backend
- **FastAPI**: Framework web Python
- **Firestore**: Banco de dados NoSQL
- **Gemini API**: Inteligência artificial do Google
- **PyMuPDF**: Extração de texto de PDFs
- **numpy**: Computação numérica e embeddings

### Frontend
- **Vue 3**: Framework JavaScript progressivo
- **Vuetify 3**: Componentes UI Material Design
- **Axios**: Cliente HTTP para API

### Desenvolvimento
- **Python**: Linguagem principal
- **PowerShell**: Ambiente de execução
- **Git**: Controle de versão
- **Docker**: (Configurado) Para deployment

---

## 📊 Métricas e Monitoramento

### Sistema de Memória
- **Embeddings**: Vetores numéricos para busca semântica
- **Contexto Otimizado**: Arquivos markdown enriquecidos
- **Aprendizado**: Regras e feedbacks acumulados

### Qualidade das Estações
- **Cobertura**: Checklist completo de avaliação
- **Consistência**: Padronização via templates
- **Relevância**: Contexto médico atualizado

### Performance
- **Tempo de Resposta**: Monitorado em tempo real
- **Uso de Memória**: Alertas para otimização
- **Taxa de Erro**: Métricas de qualidade do sistema

---

## 🔧 Configuração e Implantação

### Ambiente de Desenvolvimento
1. **Ativar virtual environment**: `.venv\Scripts\activate`
2. **Instalar dependências**: `pip install -r requirements.txt`
3. **Configurar variáveis de ambiente**: `.env`
4. **Rodar backend**: `python main.py`

### Ambiente de Produção
1. **Docker**: Containerização do sistema
2. **Firestore**: Configuração de produção
3. **Gemini API**: Chaves de produção configuradas
4. **Monitoramento**: Sistema de alertas ativo

---

## 📝 Próximos Passos e Melhorias

### Tarefas Pendentes
- [ ] Testes automatizados completos
- [ ] Documentação de API detalhada
- [ ] Otimização de performance
- [ ] Expansão de templates

### Melhorias Propostas
- **Interface**: Melhor UX na geração de estações
- **IA**: Integração com mais modelos de linguagem
- **Dados**: Expansão do banco de provas
- **Automação**: Scripts de manutenção automatizados

---

## 📞 Suporte e Contato

Para suporte técnico ou dúvidas sobre o sistema, consulte:
- Documentação: [`gerador.md`](gerador.md)
- Código fonte: Todos os arquivos documentados acima
- Configuração: [`pyproject.toml`](pyproject.toml), [`.gitignore`](.gitignore)

---

*Esta documentação foi gerada automaticamente com base na análise completa do projeto em 26/08/2025.*
