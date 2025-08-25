# Endpoints da API - Backend

## Estrutura Inicial

### 1. POST `/api/agent/start-creation`
- **Descrição:** Inicia a geração de estação clínica, recebendo tema, especialidade e PDF opcional.
- **Parâmetros:**
  - `tema` (string)
  - `especialidade` (string)
  - `pdf_reference` (arquivo PDF, opcional)
- **Retorno:**
  - `resumo_clinico` (string)
  - `propostas` (string, separadas por '---')

---

### 2. POST `/api/agent/generate-final-station`
- **Descrição:** Gera a estação final a partir do resumo clínico, proposta escolhida, tema e especialidade.
- **Parâmetros:**
  - `resumo_clinico` (string)
  - `proposta_escolhida` (string)
  - `tema` (string)
  - `especialidade` (string)
- **Retorno:**
  - `final_station_json` (JSON com dados da estação gerada)

---

### 3. POST `/api/agent/analyze-station`
- **Descrição:** Analisa uma estação clínica gerada, retornando insights e validações.
- **Parâmetros:**
  - `station_json` (JSON da estação)
- **Retorno:**
  - `analysis_result` (string ou JSON com resultado da análise)

---

### 4. POST `/api/agent/apply-audit`
- **Descrição:** Aplica auditoria sobre uma estação clínica, retornando relatório detalhado.
- **Parâmetros:**
  - `station_json` (JSON da estação)
- **Retorno:**
  - `audit_report` (string ou JSON)

---

### 5. GET `/api/test-gemini`
- **Descrição:** Testa a integração com o modelo Gemini, retornando status e informações do modelo.
- **Parâmetros:**
  - Nenhum
- **Retorno:**
  - `status` (string)
  - `model_info` (string ou JSON)

---

## Observações
- Atualize este arquivo conforme novos endpoints forem criados ou modificados.
- Padronize nomes e caminhos para facilitar integração frontend-backend.

---
*Documentação mantida pelo assistente de IA.*
