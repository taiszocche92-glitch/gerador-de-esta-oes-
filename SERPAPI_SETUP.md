# Configuração da Busca Web - SERPAPI
# ======================================

## Para habilitar a busca web no sistema:

### 1. Obter chave da API do SerpApi:
   - Acesse: https://serpapi.com/
   - Crie uma conta gratuita
   - Obtenha sua API Key

### 2. Configurar no ambiente:

#### Opção A - Arquivo .env (recomendado):
   Crie um arquivo `.env` na raiz do projeto com:
   ```
   SERPAPI_KEY=71abc92b94fbe2e36c8e29c366f8fe85d2c5912588f8c3059b8d9736cf992e65
   ```

#### Opção B - Variável de ambiente do sistema:
   No Windows PowerShell:
   ```powershell
   $env:SERPAPI_KEY = "71abc92b94fbe2e36c8e29c366f8fe85d2c5912588f8c3059b8d9736cf992e65"
   ```

   No Linux/Mac:
   ```bash
   export SERPAPI_KEY=sua_chave_api_aqui
   ```

### 3. Funcionalidades que usam a busca web:
   - Geração individual de estações (Fase 1)
   - Geração múltipla de estações
   - Busca por diretrizes, protocolos e consensos brasileiros

### 4. Sem a chave configurada:
   - O sistema funciona normalmente
   - A busca web é automaticamente desabilitada
   - Aparece apenas um aviso no log (não afeta a geração)

## Nota:
A conta gratuita do SerpApi oferece 100 buscas por mês, suficientes para testes e uso moderado.
