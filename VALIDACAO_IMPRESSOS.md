# Sistema de Validação de Impressos Médicos

## Visão Geral

O sistema de validação de impressos médicos foi implementado para garantir que todas as estações clínicas geradas pelo agente IA tenham impressos (documentos médicos) formatados corretamente según las reglas específicas para diferentes tipos de exames médicos.

## Funcionalidades Principais

### 1. Validação Automática por Tipo de Exame

O sistema identifica automaticamente o tipo de exame baseado no título e conteúdo do impresso:

- **Exames de Laboratório**: Hemograma, bioquímica, urina, etc.
- **Exames de Imagem**: Raio-X, TC, RM, ultrassom, ECG, etc.
- **Exames Físicos**: Semiologia, ausculta, palpação, sinais vitais
- **Outros**: Validação geral para documentos não categorizados

### 2. Regras de Validação Específicas

#### Exames de Laboratório
- ✅ Valores devem ter unidades apropriadas (mg/dL, g/dL, %, etc.)
- ✅ Valores de referência obrigatórios (VR: xxx)
- ✅ Formato numérico válido
- ✅ Campos obrigatórios: chave e valor

#### Exames de Imagem
- ✅ Laudo obrigatório com mínimo de 50 caracteres
- ✅ Estrutura do laudo: "ACHADOS:", "CONCLUSÃO:", "IMPRESSÃO:"
- ✅ Descrição mínima adequada
- ✅ Palavras-chave obrigatórias no laudo

#### Exames Físicos
- ✅ Sistemas obrigatórios: cardiovascular, respiratório, neurológico
- ✅ Formato de manobras: "positivo/negativo", "presente/ausente"
- ✅ Formato de sinais vitais: "PA: 120x80", "FC: 72", etc.

### 3. Correções Automáticas

O sistema aplica correções automáticas quando possível:

- 🔧 Adiciona valores de referência para exames laboratoriais comuns
- 🔧 Estrutura laudos de imagem automaticamente
- 🔧 Corrige formatos de sinais vitais
- 🔧 Normaliza unidades de medida

## Integração com o Sistema

### Backend (FastAPI)

A validação é executada automaticamente antes do salvamento no Firestore:

```python
# Em main.py - antes do salvamento
if IMPRESSOS_VALIDATOR_AVAILABLE:
    is_valid, validation_errors, estacao_corrigida = validar_impressos_estacao(json_output)
    
    if not is_valid:
        # Log dos erros e aplicação de correções
        json_output = estacao_corrigida
```

### Métricas de Monitoramento

O sistema registra métricas detalhadas:

- `impressos_validated`: Total de validações bem-sucedidas
- `impressos_corrected`: Total de correções aplicadas
- `impressos_validation_errors`: Total de erros de validação

### Endpoint de Teste

Endpoint dedicado para testar validação:

```
POST /api/agent/validate-impressos
```

## Como Usar

### 1. Executar Teste Completo

```bash
cd backend-python-agent
python test_impressos_validation.py
```

### 2. Testar Estação Específica

```python
from impressos_validator import validar_impressos_estacao

# Dados da estação
estacao_data = {
    "materiaisDisponiveis": {
        "impressos": [...]
    }
}

# Validar
is_valid, errors, estacao_corrigida = validar_impressos_estacao(estacao_data)
```

### 3. Via API REST

```bash
curl -X POST "http://localhost:8080/api/agent/validate-impressos" \
     -H "Content-Type: application/json" \
     -d '{"materiaisDisponiveis": {"impressos": [...]}}'
```

## Exemplos de Validação

### Exemplo 1: Exame de Laboratório

**Input (com problemas):**
```json
{
  "idImpresso": "hemograma_001",
  "tituloImpresso": "Hemograma Completo",
  "tipoConteudo": "lista_chave_valor_secoes",
  "conteudo": {
    "secoes": [{
      "tituloSecao": "Série Vermelha",
      "itens": [
        {"chave": "Hemoglobina", "valor": "12.5"},  // SEM UNIDADE
        {"chave": "Hematócrito", "valor": "38%"}
      ]
    }]
  }
}
```

**Output (corrigido):**
```json
{
  "itens": [
    {"chave": "Hemoglobina", "valor": "12.5 g/dL (VR: 12-16 g/dL)"},  // CORRIGIDO
    {"chave": "Hematócrito", "valor": "38%"}
  ]
}
```

### Exemplo 2: Exame de Imagem

**Input (com problemas):**
```json
{
  "idImpresso": "rx_torax_001",
  "tituloImpresso": "Raio-X de Tórax",
  "tipoConteudo": "imagem_com_texto",
  "conteudo": {
    "laudo": "Normal"  // MUITO CURTO
  }
}
```

**Output (corrigido):**
```json
{
  "conteudo": {
    "laudo": "ACHADOS:\nNormal\n\nCONCLUSÃO:\n[A ser preenchida conforme achados]"  // ESTRUTURADO
  }
}
```

## Configuração de Regras

As regras de validação são configuráveis no arquivo `impressos_validator.py`:

```python
self.regras_formatacao = {
    'laboratorio': {
        'formato_valores': r'^[\d,.\s]+\s*[a-zA-ZµΩ/\s%]*$',
        'intervalos_obrigatorios': True,
        'unidades_obrigatorias': True
    },
    'imagem': {
        'descricao_minima': 50,
        'laudo_obrigatorio': True,
        'palavras_chave_obrigatorias': ['achados', 'conclusão']
    }
}
```

## Logs e Debugging

O sistema gera logs detalhados para facilitar debugging:

```
✅ Validação de impressos: 3 impressos válidos
⚠️ Impressos com problemas detectados: 2 erros
🔧 Correções automáticas aplicadas aos impressos
```

## Benefícios

1. **Qualidade Médica**: Garante que impressos sigam padrões médicos
2. **Consistência**: Padroniza formatos entre diferentes estações
3. **Automação**: Corrige problemas automaticamente quando possível
4. **Monitoramento**: Métricas detalhadas para análise de qualidade
5. **Flexibilidade**: Regras configuráveis por tipo de exame

## Extensibilidade

Para adicionar novos tipos de exames:

1. Adicionar regras em `regras_formatacao`
2. Implementar `_validar_[novo_tipo]()`
3. Atualizar `_determinar_tipo_exame()`
4. Adicionar casos de teste

## Status do Sistema

Verificar status via endpoint:

```
GET /api/agent/system-status
```

Retorna informações sobre:
- Sistema de validação ativo
- Total de validações realizadas
- Total de correções aplicadas
- Erros de validação

---

**Desenvolvido como parte do sistema de geração automática de estações clínicas para o REVALIDA.**
