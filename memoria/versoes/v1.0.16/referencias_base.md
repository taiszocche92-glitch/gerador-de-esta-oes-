# GUIA MESTRE PARA CRIAÇÃO DE ESTAÇÕES CLÍNICAS - PADRÃO REVALIDA FÁCIL (INEP)
# Versão 3.0 - Baseado na análise de 40 estações

---
. PRINCÍPIOS FUNDAMENTAIS DE DESIGN 🎯

Toda estação de alta qualidade se baseia em dois princípios essenciais.

### **0.1. A Tríade de Coerência**
Este é o pilar de uma estação robusta. Deve haver um alinhamento perfeito entre:
1.  **Tarefas (`tarefasPrincipais`):** O que o candidato **deve fazer**.
2.  **Informações Disponíveis (`informacoesVerbaisSimulado` + `impressos`):** Todas as informações (e apenas as informações) necessárias para **cumprir as tarefas**.
3.  **Checklist (`padraoEsperadoProcedimento`):** A pontuação objetiva que mede **como o candidato executou as tarefas** com base nas informações disponíveis.

* **Exemplo Prático (Estação Dengue na Gestante):**
    * **Tarefa:** "Classificar o quadro quanto à gravidade".
    * **Informação:** Roteiro informa que a paciente é **gestante**. Impresso da Prova do Laço mostra resultado **positivo**.
    * **PEP:** O item do checklist pontua especificamente a "Classificação como dengue - **grupo B**", diagnóstico que só é possível ao conectar as informações de "gestante" (condição de risco) e "prova do laço positiva" (sinal de alerta).

### **0.2. O Princípio da Autonomia**
A estação deve ser autossuficiente. O candidato deve encontrar todas as informações necessárias para a resolução do caso através da anamnese, do exame físico solicitado ou dos impressos disponíveis. O avaliador não deve interferir, e o roteiro do ator deve prever as interações-chave, incluindo o que responder a perguntas não previstas (geralmente com "Não consta no script").

---

## 1. ARQUITETURA DAS ESTAÇÕES: TIPOS E ESTRATÉGIAS 🏗️

As estações podem ser classificadas em quatro arquétipos principais, cada um com um foco de avaliação distinto.

### **1.1. Estação de Encontro Clínico Completo**
O formato clássico que simula uma consulta completa.
* **Foco:** Raciocínio clínico do início ao fim.
* **Estrutura:** Anamnese, exame físico, solicitação de exames, diagnóstico e conduta.
* **Exemplos:** Pancreatite Aguda, Dengue Clássica, AVC Isquêmico.

### **1.2. Estação de Habilidade Procedimental/Educacional**
Foca exclusivamente na execução e/ou explicação de uma técnica ou procedimento.
* **Foco:** "Saber como fazer" e "saber como ensinar".
* **Estrutura:** Anamnese e exame físico geral são omitidos (conforme `avisosImportantes`). As tarefas são diretas: "Realizar a técnica...", "Demonstrar e verbalizar...", "Registrar nos gráficos...".
* **Exemplos:** Sutura, Exame Físico Obstétrico, Puericultura (Antropometria), Orientação de Insulinoterapia.

### **1.3. Estação de Habilidade de Comunicação**
Foca no manejo de diálogos sensíveis e na aplicação de protocolos de comunicação.
* **Foco:** Habilidades interpessoais, empatia, clareza e profissionalismo.
* **Estrutura:** Anamnese e exame físico são omitidos. As tarefas envolvem "Utilizar habilidades...", "Comunicar o diagnóstico...", "Acolher...".
* **Exemplos:** Comunicação de Más Notícias (Protocolo SPIKES), Prevenção de Câncer de Colo em Mulher Lésbica (abordagem de discriminação), Abordagem da Obesidade (pactuação de metas), NUNCA COLOCAR NADA ENTRE PARENTESES, NUNCA DAR DICAS NAS TAREFAS DE COMO FAZER OU O QUE FAZER OU SOLICITAS, APENAS TAREFAS GENERICAS PARA QUE O CANDIDATO SIGA E SAIBA E O QUE FAZER.

### **1.4. Estação de Protocolo de Emergência**
Foca na aplicação correta e sequencial de protocolos de atendimento rápido.
* **Foco:** "Saber o que fazer primeiro" em uma emergência.
* **Estrutura:** Segue uma sequência lógica de atendimento (ex: ABCDE do ATLS).
* **Materiais:** Impressos com protocolos e fluxogramas de atendimento.
* **Roteiro do ator:** Quando o paciente esta inconciente ou irresponsivel não tem anamnese, apenas tem os dados do paciente como impressos, e instrução ao chefe de estação nas informações verbais do simulado apenas para dar respostas ou liberar impressos com as informações conforme o candidato solicita ou questiona, geralmente sao protocolos especificos que seguem uma ordem cronologia de tarefas, exe: xatls, pals, reanimação neonatal, pcr, etc.
* **Exemplos:** Pneumotórax Hipertensivo (ATLS), Grande Queimado (ATLS e Parkland).

---

## 2. DIRETRIZES PARA TAREFAS, ROTEIROS E MATERIAIS 📝

### **2.1. O Roteiro do Ator: Informação Estratégica**
O roteiro é uma ferramenta de avaliação.
* **HDA por Sintoma-Guia:** Crie um `contextoOuPerguntaChave` para cada sintoma principal (Ex: "DOR ABDOMINAL", "SANGRAMENTO VAGINAL"). Isso organiza a informação e facilita a criação de itens de avaliação específicos no PEP.
* **A Força dos Negativos:** Inclua ativamente a negação de sintomas importantes para o diagnóstico diferencial. Isso avalia a capacidade do candidato de excluir outras hipóteses.
* **Carga Emocional e Recusas:** Em casos sensíveis (Ex: Violência Sexual), o roteiro deve incluir o estado emocional do paciente ("com muito medo") e possíveis recusas a procedimentos ("Não quero ser examinada").
* **Perguntas Padronizadas (`perguntasAtorSimulado`):** Use esta seção para programar perguntas-chave que o ator fará em momentos específicos (ex: após o diagnóstico), garantindo que todos os candidatos sejam testados na sua capacidade de explicar e orientar.

### **2.2. Impressos: Ferramentas e Resultados**
Os impressos fornecem os dados objetivos.
* **Tipos de Conteúdo:**
    * `lista_chave_valor_secoes`: Ideal para exames físicos e resultados de laboratório simples.
    * `tabela`: Melhor formato para múltiplos exames laboratoriais, pois permite a inclusão clara de valores de referência.
    * `imagemComLaudo`: Para exames de imagem, ECGs, ou para fornecer ferramentas como escalas (NIHSS) e tabelas de referência (percentis de PA pediátrica).
    * `texto_livre`: Para cartas, encaminhamentos ou outros documentos em texto corrido.
* **Materiais Interativos:** Use impressos para avaliar a aplicação do conhecimento, como figuras para o candidato anotar (locais de aplicação de insulina) ou tabelas para completar verbalmente (cálculo de Parkland).

---

## 3. TAREFAS PRINCIPAIS POR ESPECIALIDADE

### CLÍNICA MÉDICA - Padrões de Tarefas

**Padrão Geral (Casos Ambulatoriais):**
- Realizar anamnese direcionada à queixa principal do paciente
- Solicitar/realizar exames físicos necessários à avaliação do caso
- Solicitar exames complementares pertinentes ao caso clínico
- Relacionar os resultados dos exames às hipóteses diagnósticas
- Verbalizar o diagnóstico, sua classificação de gravidade e elaborar a conduta terapêutica

**Padrão Específico - Casos com Exames Pré-existentes:**
- Ler a ficha do paciente apresentada a seguir
- Fazer a anamnese dirigida ao paciente
- Interpretar os exames apresentados e verbalizar seus achados
- Estabelecer o diagnóstico inicial
- Estabelecer a conduta terapêutica indicada

**Padrão para Casos Complexos/Sistêmicos:**
- Realizar anamnese detalhada
- Solicitar exame físico completo
- Analisar exames complementares
- Formular hipóteses diagnósticas principais e diferenciais
- Elaborar plano terapêutico e seguimento

### CIRURGIA GERAL - Padrões de Tarefas

**Padrão Ambulatorial/Eletivo:**
- Realizar anamnese do paciente
- Solicitar/realizar exames físicos necessários à avaliação do caso
- Solicitar exames complementares pertinentes ao caso clínico
- Relacionar os resultados dos exames às hipóteses diagnósticas
- Verbalizar o diagnóstico, sua classificação de gravidade e elaborar a conduta terapêutica

**Padrão Urgência/Emergência:**
- Realizar o atendimento do paciente, verbalizando os achados e as condutas
- Solicitar a realização de exames que julgar necessários
- Definir a extensão e gravidade do quadro
- Adotar a conduta terapêutica necessária

**Padrão com Avaliação Específica (ex: trauma, queimadura):**
- Realizar avaliação primária seguindo protocolo ABCDE
- Calcular scores específicos (ex: superfície corporal queimada)
- Indicar medidas de suporte e estabilização
- Determinar necessidade de transferência/especialização

### PEDIATRIA - Padrões de Tarefas

**Padrão Puericultura/Rotina:**
- Realizar a anamnese dirigida à mãe/responsável
- Solicitar qualquer exame físico e/ou complementar que considere pertinente
- Explicar os achados do exame físico
- Analisar o crescimento e desenvolvimento da criança
- Explicar ao responsável o diagnóstico clínico da criança
- Orientar sobre prevenção, cuidados e seguimento

**Padrão Urgência Pediátrica:**
- Ler a ficha da paciente apresentada a seguir
- Fazer a anamnese dirigida ao responsável
- Solicitar qualquer exame físico e/ou complementar que deseje
- Comentar o exame físico (não será necessário examinar diretamente o paciente)
- Estabelecer o diagnóstico inicial e responder aos questionamentos
- Solicitar exames complementares, se necessário
- Interpretar os exames apresentados e verbalizar seus achados
- Confirmar a hipótese diagnóstica
- Encaminhar o paciente de acordo com a conduta terapêutica indicada

### GINECOLOGIA E OBSTETRÍCIA - Padrões de Tarefas

**Padrão Ginecológico:**
- Realizar anamnese dirigida
- Solicitar exames pertinentes ao caso
- Verbalizar hipótese diagnóstica e diagnósticos diferenciais
- Solicitar exames complementares, caso necessário
- Propor à paciente o tratamento a ser realizado
- Explicar possíveis complicações da doença
- Dar orientações de seguimento

**Padrão Obstétrico/Urgência:**
- Realizar anamnese
- Solicitar os exames que julgar necessários
- Responder aos questionamentos da paciente simulada
- Citar hipótese diagnóstica
- Realizar as condutas necessárias
- Estabelecer a orientação final à paciente simulada

### MEDICINA DA FAMÍLIA - Padrões de Tarefas

**Padrão Atenção Primária/Prevenção:**
- Abordar adequadamente a pessoa conforme contexto específico
- Avaliar critérios específicos da condição (ex: dependência, risco)
- Orientar adequadamente sobre intervenções comportamentais
- Indicar tratamento medicamentoso e/ou não medicamentoso adequado
- Cumprir medidas de prevenção e controle comunitário

**Padrão Doença Endêmica/Notificável:**
- Realizar o atendimento do paciente
- Definir o diagnóstico clínico-epidemiológico
- Orientar o plano terapêutico
- Cumprir as medidas de prevenção e controle
- Realizar notificação compulsória

---

Este documento contém as diretrizes fundamentais para criação de estações clínicas no padrão REVALIDA FÁCIL (INEP), incluindo princípios de design, tipos de estações, padrões de tarefas por especialidade e critérios de avaliação.

Local do banco de dados: southamerica-east1
