# CONTEXTO FASE 3: CRIAÇÃO DE IMPRESSOS E EXAMES
# Tipos de Impressos + Estruturas por Categoria

## TIPOS DE IMPRESSOS POR CATEGORIA

### EXAMES LABORATORIAIS (lista_chave_valor_secoes)

**Hemograma Completo:**
```json
{
  "secoes": [
    {
      "tituloSecao": "SÉRIE VERMELHA",
      "itens": [
        {"chave": "Hemoglobina", "valor": "X g/dL (VR: X - X g/dL)"},
        {"chave": "Hematócrito", "valor": "X% (VR: X - X%)"},
        {"chave": "VCM", "valor": "X fL (VR: X - X fL)"}
      ]
    },
    {
      "tituloSecao": "SÉRIE BRANCA", 
      "itens": [
        {"chave": "Leucócitos", "valor": "X.XXX/mm³ (VR: X.XXX - X.XXX/mm³)"},
        {"chave": "Segmentados", "valor": "X% (VR: X - X%)"}
      ]
    }
  ]
}
```

**Bioquímica Básica:**
```json
{
  "secoes": [
    {
      "tituloSecao": "FUNÇÃO RENAL",
      "itens": [
        {"chave": "Ureia", "valor": "X mg/dL (VR: X - X mg/dL)"},
        {"chave": "Creatinina", "valor": "X mg/dL (VR: X - X mg/dL)"}
      ]
    },
    {
      "tituloSecao": "GASOMETRIA",
      "itens": [
        {"chave": "pH", "valor": "[Valor] (Ref: [7.35-7.45])"},
        {"chave": "pCO2", "valor": "[Valor] mmHg (Ref: [35-45])"}
      ]
    }
  ]
}
```

### EXAMES DE IMAGEM (imagemComLaudo)

**Estrutura Padrão:**
```json
{
  "idImpresso": "[]",
  "tituloImpresso": "[Tipo] de [região] em [incidência]",
  "tipoConteudo": "imagemComLaudo",
  "conteudo": {
    "textoDescritivo": "ATENÇÃO: DIRIJA-SE PARA A CÂMERA E EXPLIQUE OS ACHADOS NA IMAGEM",
    "urlImagem": "[LINK DO SITE COM A IMAGEM]",
    "laudo": "[Descrição do laudo da imagem]"
  }
}
```

### EXAMES FÍSICOS (lista_chave_valor_secoes)

**Sinais Vitais:**
```json
{
  "secoes": [
    {
      "tituloSecao": "SINAIS VITAIS",
      "itens": [
        {"chave": "Pressão arterial", "valor": "XXX × XX mmHg"},
        {"chave": "Frequência cardíaca", "valor": "XX bpm"},
        {"chave": "Temperatura", "valor": "XX,X °C"},
        {"chave": "Saturação O2", "valor": "XX% em ar ambiente"}
      ]
    }
  ]
}
```

## REGRA ESPECIAL PARA DOENÇAS INFECCIOSAS
- **SEMPRE incluir impresso laboratorial com possíveis alterações**
- **Criar impressos separados para sorologias e marcadores específicos**
- **Incluir ectoscopia quando houver alterações visuais relevantes**

Local do banco de dados: southamerica-east1
