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
Análise Quantitativa e Qualitativa do PEP

## Parte 3.1: Análise Aprofundada de Tarefas e Casos Especiais (Baseado na Prova 2024.2)

A análise do `CONSOLIDADO_2024_2_ESTACOES_INEP.json` permite um aprofundamento nos padrões das `tarefasPrincipais` e na estrutura de estações com roteiro verbal mínimo.

### 3.1. Padrões em `tarefasPrincipais` por Especialidade e Cenário

As tarefas são altamente adaptadas ao contexto da estação.

- **Cenário de Emergência/Procedimento (Ex: AVC, Trauma Abdominal):**
  - **Foco:** Ação, diagnóstico rápido e conduta imediata.
  - **Estrutura:** As tarefas são diretas, imperativas e seguem um fluxo lógico de atendimento emergencial, nao tem anamnese, apenas orientações ao chefe da estação para liberar informações e impressos (sinais vitais, exame fisico, exames de imagem, laboratorio, antecedentes, historia clinica, etc).
  - **Exemplos:**
    - `"Aplicar a escala NIHSS ao paciente."` (AVC)
    - `"Totalizar a pontuação da escala NIHSS e VERBALIZAR."` (AVC)
    - `"Estabelecer e comunicar a(s) hipótese(s) diagnóstica(s) definitiva(s)"/ "Propor tratamento inicial e definitivo."` (Trauma Abdominal)

- **Cenário Ambulatorial/Orientação (Ex: Criptorquidia, Dengue):**
  - **Foco:** Raciocínio clínico, diagnóstico diferencial, comunicação com o paciente/família e planejamento de cuidados.
  - **Estrutura:** As tarefas envolvem mais explicação, interpretação e orientação.
  - **Exemplos:**
    - `"Interpretar o exame físico e explicar à mãe os diagnósticos..."` (Criptorquidia)
    - `"Elencar as possíveis complicações para a(s) condição(ões) encontrada(s) no paciente."` (Criptorquidia)
    -  `"Verbalizar o diagnóstico" / "sua classificação de gravidade" / "elaborar a conduta terapêutica"` (Dengue)

- **Conclusão para Padronização:**
  - As tarefas devem ser desenhadas para refletir o objetivo central da estação.
  - Para estações de emergência, as tarefas devem ser mais diretas e focadas na ação.
  - Para estações ambulatoriais, as tarefas devem incluir mais elementos de comunicação, interpretação e orientação, alinhando-se com a necessidade de um atendimento mais integral.
  - NUNCA DAR ORIENTAÇÕES DE COMO FAZER OU DO QUE PEDIR E O QUE FAZER, Ex: "Classifique o paciente conforme o CURB 65, QUERO QUE SEJA ASSIM, Classifique o paciente corretamente, sem orientações ou exemplos entre parenteses por favor

---

### **4. O ROTEIRO DO ATOR: INFORMAÇÃO ESTRATÉGICA (informacoesVerbaisSimulado)** ###

## 4.1 REGRAS BÁSICAS

- O roteiro é uma ferramenta de avaliação.

- * **HDA por Sintoma-Guia:** Crie um `contextoOuPerguntaChave` para cada sintoma principal (Ex: "DOR ABDOMINAL", "SANGRAMENTO VAGINAL"). Isso organiza a informação e facilita a criação de itens de avaliação específicos no PEP.

- * **A Força dos Negativos:** Inclua ativamente a negação de sintomas importantes para o diagnóstico diferencial. Isso avalia a capacidade do candidato de excluir outras hipóteses.

- * **Carga Emocional e Recusas:** Em casos sensíveis (Ex: Violência Sexual), o roteiro deve incluir o estado emocional do paciente ("com muito medo") e possíveis recusas a procedimentos ("Não quero ser examinada").

- * **Perguntas Padronizadas (`perguntasAtorSimulado`):** Use esta seção para programar perguntas-chave que o ator fará em momentos específicos (ex: após o diagnóstico), garantindo que todos os candidatos sejam testados na sua capacidade de explicar e orientar.

## 4.2 REGRAS OBRIGATÓRIAS DE CONTEXTOS E INFORMAÇÕES PADRONIZADAS E REGRAS DE EXIBIÇÃO E FORMATAÇÃO

*** Cada sintoma/queixa do paciente em relação ao motivo de consulta, no campo 'informacao' deve conter TODAS as informações relevantes, incluindo características, essas nunca devem estar contidas entre parenteses, e sim detalhadas uma a uma separadas por \n como todas as informaçções de todos os 'conteudoOuPalavraChave', como por exemplo, ao inves de estar assim:Ex: 'Caracteristica da macha': Dói, coça, descama e sangra, crie informações separadas para cada uma, assim: \nDor: [Dói]\nPrurido: [Coça]\nDescamação: [Descama]\nSangramento: [Não sangra], OBS: ESSA REGRA VALE TAMBEM PARA AS INFORMAÇÕES DA DESCRIÇÕES DOS ITENS DE AVALIAÇÃO DO PEP (VEREMOS MAIS ABAIXO EM UM TOPICO ESPECIFICO MAIS JÁ GUARDE ESSA INFORMAÇÃO) ***

*** "SEMPRE INCLUIR 'informacao' DA ANAMNESE / HISTORIA CLINICA que tenha IMPORTANCIA / RELEVANCIA CLINICA / EPIDEMIOLÓGICA  E/OU PARA DESCARTAR OUTROS DIAGNOSTICOS, QUE TENHA RELEVANCIA, AOS 'contextos' MESMO QUE ELA SEJA 'negada' pelo paciente e TODAS essas mesmas 'informacao' de um 'contexto' seja ela relatada ou negada devem estar OBRIGATORIAMENTE inseridas no PEP nos item de avaliação, cada uma separada individualmente e listada separadas por \n, sem economizar, liste o possivel sempre." ***

*** Na caracterização do(s) 'sintoma principal/sintoma guia' do motivo de consulta, o item "Característica" se for mais que duas ou mais caracteristicas, exibir o nome de cada um e não exibir esse campo, Ex: Caracteristica da macha: Dói, coça, descama e sangra, essa maneira está errado, crie informações separadas para cada uma, assim: \nDor: [Dói]\nPrurido: [Coça]\nDescamação: [Descama]\nSangramento: [Não sangra], que isso seja padrao, se for apenas uma caracteristica desconsidere essa orientação. *** (logo abaixo tem outros exemplos disto)

## 4.3 REGRAS GERAIS PARA EXIBIÇÃO DAS 'informacoesVerbaisSimulado' E SEU CONTEÚDO

*** HISTÓRIA DA DOENÇA ATUAL NÃO DEVE SER EXIBIDA E SIM O NOME DE CADA SINTOMA/QUEIXA (Sintomas guia) E SE FOR MAIS DE UM SINTOMA CRIAR UM NOVO "contextoOuPerguntaChave" PARA CADA SINTOMA, NUNCA DESCREVER A CARACTERIZAÇÃO DE UM MESMO SINTOMA/QUEIXA EM UM MESMO CONTEXTO (APENAS REFORÇANDO POIS É ESSENCIAL). ***

**Orientações, regras de exibição / formatação e padrões para os campos: 'contextoOuPerguntaChave' e 'informacao'**

 - *IDENTIFICAÇÃO DO(s) PACIENTE(s):* 

 Sempre exibir os dados de identificação do(s) acompanhante(s), geralmente são estações de pediatria ou em casos com adolescentes, ou idosos incapazes ou pessoas incapazes,(pai, mãe, ambos, avó, cuidador, tia, tio, professora, cuidador, enfermeiro, filha, filho, sobrinho,etc), o padrão do campo 'informacao' sempre é composto por :Nome, idade, estado civil e profissão, outras informações como procedencia (Ex: casos de malaria que o paciente veio/viajou ou vive em regiao endemica, procedente de regiões especificas de certas doenças), religâo (se for um caso em que o paciente é de certa religiao que não aceita certos procedimentos), genero (em estações onde o paciente é gay, lésbica, ou lgbt, apenas nesses casos).

 - *MOTIVO DE CONSULTA:* 

 Motivo claro e objetivo, deve ser registrada de forma sucinta, utilizando as palavras exatas do paciente, apenas contendo os sintoma(s)/queixas do paciente, sem caracterização, por exemplo, não deve ser assim: "Estou com dor de barriga muito forte a dois dias e febre de 38 graus", o correto deve ser assim: "Estou com dor de barriga e também estou com febre".

 - *História da Doença Atual (HDA), O Coração da Anamnese:* (RECAPITULANDO)

 Esta é a seção mais importante e detalhada da anamnese, onde a queixa principal e seus sintomas associados são explorados em profundidade. A HDA deve ser uma narrativa clara, lógica e cronológica do adoecimento, desde o primeiro sintoma até o momento da consulta. Cada sintoma relatado deve ser minuciosamente dissecado utilizando um roteiro semiológico universal. Cada sintoma deve conter os seguintes elementos praticamente obrigatórios, que são os seguintes: "Início: [Quando começou? Há quanto tempo? Como começou?]\nLocalização: [Onde exatamente? Bem ou mal localizada? É em um menbro ou varios, doi só o joelho direitou ou dói os dois?]\nQuantidade: [São quantas machans, quantas feridas, quantos caroços, quantas picadas, quantas mordidas]\nIntensidade: [Escala 0-10, fraca? forte? desconforto?]\nCaracterística(Qualidade/caráter): [Como é o sintoma: pontada, queimação, pressão, etc.?(se for mais que uma caracteristica, exibir o nome de cada um e não exibir esse campo, Ex: Caracteristica da macha: Dói, coça, descama e sangra, crie informações separadas para cada uma, assim: \nDor: [Dói]\nPrurido: [Coça]\nDescamação: [Descama]\nSangramento: [Não sangra], que isso seja padrao)]\nIrradiação: [Migração da dor ? Espalha para onde? Propaga-se?]\nDuração: [Contínuo, intermitente, duração dos episódios?]\n Progressão: [Progressiva, em melhora, está piorando com o tempo? Como tem evoluído?]\nFrequencia: [Quantas vezes ocorre? Qauntas vezes vomitou? Quantas vezes teve diarréia? Quantos acessos de tosse durante a crise?]\nFator de piora ou agravante: [O que piora o sintoma? ao movimento?, após se alimentar?, Quando está ansioso? quando esta estressado?, piora ao acordar?, piora ao movimentar?, parado?, ao deitar?, após beber café?]\nFator de melhora ou atenuante: [O que alivia? melhora em repouso?, Melhora ao se movimentar? Melhora ao comer? melhora ao deitar? melhora após usar medicamento(s)?, Melhora após evacuar? posição?]\nEpisódios prévios: [Já teve algo similar antes?, Já teve esse sintoma antes?, Quantas vezes já sentiu isso antes?, Já teve essa cris]\nMedicação de alivio: [Usou algum analgésico para a dor?,Com que resultado?]"
 Cada sintoma/queixa do paciente da história da doença atual, especificamente no campo 'informacao' do contexto do sintoma deve conter TODAS as informações relevantes, incluindo características (essas nunca devem estar contidas entre parenteses, e sim detalhadas uma a uma separadas por \n como todas as informaçções de todos os 'conteudoOuPalavraChave', como por exemplo, ao inves de estar assim: Caracteristicas:  Caracteristicas ()), duração e fatores de melhora/piora.


 - *ORIENTAÇÕES AO CHEFE DE ESTAÇÃO* - Esse campo deve ser exibido/criado somente em situações específicas, como estações de trauma (xatls), parada cardiorespiratória, emergencias, onde não tem interação com o paciente, ai ao inves de roteiro de ator, tem apenas contextos com informações para passar ao candidato, e essas informações nao devem ser inseridas no campo 'informacao' e sim como 'impresso' e o 'contextoOuPerguntaChave' será a orientação do chefe de estação de qual impresso liberar ou do que responder ao candidato (nesse caso apenas se as respostas forem curtas, nunca frases complexas, resultado de exames fisicos, exames complementares, etc)

---

###### **5. BANCO DE SEMIOLOGIA ###

### SINTOMAS - ROTEIROS DETALHADOS

**Dispneia**
- Início: [Quando começou? Foi súbito ou gradual?]
- Duração: [Há quanto tempo está com falta de ar?]
- Padrão: [Contínua ou episódica? Frequência dos episódios?]
- Intensidade: [Escala 0-10, limita atividades diárias?]
- Impacto nas Atividades de Vida Diária (AVDs): [O que o(a) senhor(a) deixou de fazer por causa da falta de ar?]
- Ortopneia e Dispneia Paroxística Noturna (DPN): [Precisa de quantos travesseiros para dormir? Acorda à noite com falta de ar?]
- Fatores de piora: [Exercício físico, repouso, posição?]
- Fatores de melhora: [Uso de medicação, repouso, mudança de posição?]
- Sintomas associados: [Tosse, dor no peito, sibilos?]
- Episódios prévios: [Já teve episódios semelhantes antes?]
- Relação com o ambiente: [Piora no trabalho ou em algum cômodo da casa?]
- Histórico de Tabagismo (quantificado): [Fuma ou já fumou? Quantos cigarros por dia e por quantos anos?]

**Febre**
- Início: [Quando começou? Foi súbito com calafrios ou gradual?]
- Duração: [Há quantos dias está com febre?]
- Padrão: [Contínua ou tem picos? Em que período do dia é mais alta?]
- Intensidade: [Qual a temperatura mais alta medida?]
- Sintomas associados: [Calafrios? Sudorese noturna?]
- Resposta a antitérmicos: [Tomou algum remédio? Qual? A febre cedeu completamente?]
- Histórico de Viagens Recentes: [Viajou para algum lugar diferente no último mês? Onde?]
- Contato com doentes ou animais: [Teve contato com alguém doente ou com animais recentemente?]
- Uso de medicamentos recentes (incluindo antibióticos): [Está tomando algum remédio novo? Usou antibiótico recentemente?]
- Episódios prévios: [Já teve algo similar antes?]

**Alterações de Peso**
- Início: [Quando começou a notar a alteração de peso?]
- Tipo: [Perda ou ganho de peso]
- Quantificação: [Exemplo: 'Perdi 6 quilos nos últimos 3 meses']
- Intencionalidade: [Exemplo: 'Não foi intencional, não estou fazendo dieta']
- Relação com apetite: [Exemplo: 'Meu apetite diminuiu muito']
- Tempo de evolução: [Exemplo: 'Notei a mudança de peso há cerca de 2 meses']
- Sintomas associados: [Exemplo: 'Além da perda de peso, tenho sentido muito cansaço']
- Episódios prévios: [Já teve alterações de peso semelhantes antes?]

**Astenia/Fadiga**
- Início: [Exemplo: 'Começou há cerca de 1 mês']
- Diferenciação: [Exemplo: 'Sinto mais cansaço do que fraqueza']
- Evolução: [Exemplo: 'Tem piorado com o tempo']
- Impacto funcional: [Exemplo: 'Estou com dificuldade para fazer as tarefas de casa']
- Relação com atividade/repouso: [Exemplo: 'Piora quando faço esforço, melhora um pouco quando descanso']
- Qualidade do sono: [Tem dormido bem? Ronca? Acorda cansado(a)?]
- Sintomas de humor associados (tristeza, anedonia): [Tem se sentido triste ou desanimado(a)? Perdeu o interesse em coisas que gostava?]
- Sintomas associados: [Exemplo: 'Tenho dormido mal e perdido peso']
- Episódios prévios: [Já teve algo similar antes?]

**Lesões Cutâneas**
- Início: [Exemplo: 'Apareceu há 5 dias']
- Evolução: [Exemplo: 'A lesão aumentou de tamanho e mudou de cor']
- Localização: [Exemplo: 'Começou no braço']
- Quantidade: [Exemplo: 'Uma lesão única ou várias?']
- Sintomas associados: [Exemplo: 'Coça e às vezes arde']
- Fatores desencadeantes: [Exemplo: 'Apareceu depois que usei um creme novo']
- Exposição: [Exemplo: 'Não tive contato com plantas ou animais diferentes']
- Uso de medicamentos: [Exemplo: 'Estou usando um creme para a pele']
- Episódios prévios: [Já teve algo similar antes?]

**Prurido (Coceira)**
- Início: [Exemplo: 'Começou há 2 semanas']
- Localização: [Exemplo: 'Coça mais nas pernas, mas às vezes no corpo todo']
- Intensidade: [Exemplo: 'É forte, nota 7 de 10']
- Piora/melhora: [Exemplo: 'Piora à noite, melhora um pouco com banho frio']
- Lesões associadas: [Exemplo: 'Fica vermelho e com marcas de unha']
- Sintomas sistêmicos: [Exemplo: 'Não notei febre nem amarelão nos olhos']
- Contexto: [Exemplo: 'Ninguém mais em casa está com coceira']
- Episódios prévios: [Já teve algo similar antes?]

**Cefaleia (Dor de Cabeça)**
- Início: [Exemplo: 'Começou de repente, como uma explosão']
- Localização: [Exemplo: 'Dói mais na nuca, mas pega a cabeça toda']
- Intensidade: [Exemplo: 'É a pior dor que já senti, nota 10 de 10']
- Tipo/Característica: [Exemplo: 'É uma dor pulsátil, como se estivesse batendo']
- Duração/frequência: [Exemplo: 'Dura cerca de 2 horas, já tive 3 crises esta semana']
- Fatores de piora: [Exemplo: 'Piora com luz forte e barulho']
- Fatores de melhora: [Exemplo: 'Melhora quando fico deitado no escuro']
- Sintomas associados: [Exemplo: 'Sinto enjoo e às vezes vejo luzes antes da dor começar']
- Sinais de alarme: [Exemplo: 'Nunca tive dor assim antes']
- Episódios prévios (padrão habitual): [Essa dor é igual às dores que o(a) senhor(a) costuma ter?]

**Tontura/Vertigem**
- Início: [Exemplo: 'Começou de repente, enquanto estava em pé']
- Tipo: [Exemplo: 'Sinto que tudo gira ao meu redor']
- Duração: [Exemplo: 'Dura alguns minutos e depois passa']
- Fatores desencadeantes: [Exemplo: 'Piora quando viro a cabeça rápido']
- Sintomas associados: [Exemplo: 'Às vezes fico com náusea e suor frio']
- Impacto funcional: [Exemplo: 'Já caí uma vez por causa da tontura']
- Episódios prévios: [Já teve algo similar antes?]

**Tosse**
- Início: [Quando a tosse começou?]
- Duração: [Aguda (<3 semanas), subaguda (3-8 semanas) ou crônica (>8 semanas)]
- Característica: [Seca ou produtiva com catarro]
- Padrão/Gatilhos: [Pior pela manhã, à noite, com exercício, exposição à poeira]
- Expectoração: [Cor, consistência, quantidade do catarro, se houver]
- Presença de sangue: [Se houve hemoptise, quantidade, frequência]
- Sintomas associados: [Febre, dispneia, dor torácica]
- Episódios prévios: [Já teve algo similar antes?]

**Dispneia (Falta de ar)**
- Início: [Súbito ou gradual]
- Intensidade: [Leve, moderada, grave]
- Gatilhos: [Em repouso ou aos esforços? Quais atividades causam?]
- Classificação NYHA: [I-IV - detalhar quais atividades causam dispneia]
- Ortopneia: [Necessita de quantos travesseiros para dormir?]
- Dispneia paroxística noturna: [Acorda à noite sufocado? Com que frequência?]
- Sintomas associados: [Tosse, chiado, dor torácica, edema de MMII]
- Episódios prévios: [Já teve algo similar antes?]

**Dor Torácica**
- Início: [Súbito ou gradual]
- Localização: [Onde exatamente no peito? Precordial, retroesternal?]
- Irradiação: [Para mandíbula, braço esquerdo, costas?]
- Caráter: [Aperto, peso, queimação, pontada]
- Intensidade: [Escala 0-10]
- Duração: [Quanto tempo dura cada episódio?]
- Fatores desencadeantes: [Durante esforço, em repouso, com emoções?]
- Fatores de alívio: [Repouso, posição, nitratos?]
- Sintomas associados: [Dispneia, sudorese, náuseas, síncope]
- Episódios prévios: [Já teve algo similar antes?]

**Palpitações**
- Início/Término: [Começa e termina subitamente ou gradualmente?]
- Descrição: [Como sente o coração bater? Rápido e regular, irregular?]
- Duração/Frequência: [Quanto tempo dura? Com que frequência ocorre?]
- Fatores desencadeantes: [Esforço, estresse, café, álcool?]
- Sintomas associados: [Tontura, pré-síncope, síncope, dor no peito]
- Episódios prévios: [Já teve algo similar antes?]

**Edema de Membros**
- Início: [Quando começou?]
- Localização: [Quais membros? Unilateral ou bilateral?]
- Padrão: [Pior no final do dia? Melhora ao elevar as pernas?]
- Caráter: [Forma cacifo/depressão quando aperta com o dedo?]
- Sintomas associados: [Dispneia, ortopneia, DPN]
- Episódios prévios: [Já teve algo similar antes?]

**Dor Abdominal**
- Início/Duração: [Súbito ou gradual? Contínua ou intermitente?]
- Localização: [Em qual quadrante ou região?]
- Irradiação: [A dor se espalha para algum outro local?]
- Caráter: [Cólica, queimação, pontada, peso]
- Intensidade: [Escala 0-10]
- Relação com funções: [Piora ou melhora com alimentação, evacuação, micção?]
- Fatores de melhora/piora: [O que alivia ou piora a dor?]
- Sintomas associados: [Náuseas, vômitos, febre, alteração do hábito intestinal]
- Sinais de Alarme: [Febre alta, vômitos com sangue, fezes pretas ou com sangue, parada de eliminação de gases e fezes, icterícia, piora súbita e intensa da dor?]
- Relação com ciclo menstrual: [A dor tem relação com a menstruação?]
- Episódios prévios: [Já teve algo similar antes?]

**Náuseas e Vômitos**
- Início: [Quando começou?]
- Frequência: [Quantos episódios por dia?]
- Relação temporal: [Ocorre em jejum, após alimentação?]
- Conteúdo: [Alimentar recente, bilioso, com sangue, fecaloide?]
- Fatores de alívio: [O que melhora? Algum medicamento usado?]
- Sintomas associados: [Dor abdominal, diarreia, febre]
- Episódios prévios: [Já teve algo similar antes?]

**Alterações Intestinais**
- Início: [Quando começou?]
- Tipo: [Diarreia ou constipação]
- Duração: [Aguda ou crônica]
- Frequência: [Quantas evacuações por dia/semana?]
- Consistência: [Líquida, pastosa, endurecida, em cíbalos]
- Cor: [Normal, clara, escura, com sangue, com muco]
- Volume: [Grande ou pequeno volume em cada evacuação]
- Sintomas associados: [Dor, distensão abdominal, tenesmo, urgência]
- Padrão: [Contínua ou intermitente? Também ocorre à noite?]
- Fatores de melhora/piora: [Alimentos específicos, estresse, medicamentos]
- Uso de medicamentos recentes (especialmente antibióticos e laxantes): [Usou algum remédio novo recentemente?]
- Histórico de viagens recentes: [Viajou recentemente? Para onde?]
- Episódios prévios: [Já teve algo similar antes?]

**Icterícia/Colúria/Acolia**
- Início: [Quando notou o amarelão? Foi súbito ou gradual?]
- Intensidade: [Leve, moderada, intensa]
- Prurido: [Presença de coceira associada? Intensidade?]
- Colúria: [Urina escura como Coca-Cola?]
- Acolia fecal: [Fezes claras, esbranquiçadas?]
- Sintomas associados: [Dor abdominal, febre, perda de peso]
- Episódios prévios: [Já teve algo similar antes?]

**Sintomas Urinários**
- Início: [Quando começaram os sintomas?]
- Disúria: [Dor ou ardência ao urinar]
- Polaciúria: [Aumento da frequência urinária]
- Urgência: [Vontade súbita e incontrolável de urinar]
- Nictúria: [Necessidade de levantar à noite para urinar]
- Hesitação: [Demora para iniciar o jato]
- Jato fraco: [Diminuição da força do jato]
- Gotejamento terminal: [Continua pingando após terminar]
- Sensação de esvaziamento incompleto: [Sente que não esvaziou tudo]
- Alterações na urina: [Presença de sangue, cheiro forte, espuma]
- Episódios prévios: [Já teve algo similar antes?]

**Dor Lombar**
- Início: [Quando começou a dor?]
- Localização: [Lombar bilateral ou unilateral (flanco)?]
- Irradiação: [Para região inguinal, genitais?]
- Caráter: [Em cólica? Peso? Contínua?]
- Intensidade: [Escala 0-10]
- Fatores de melhora/piora: [Repouso, posição, movimentos?]
- Sintomas urinários associados: [Disúria, hematúria, febre]
- Episódios prévios: [Já teve algo similar antes?]

**Corrimento Vaginal/Uretral**
- Início: [Quando começou?]
- Cor: [Branco, amarelado, esverdeado, acinzentado]
- Odor: [Presença de odor forte ou desagradável]
- Quantidade: [Pequena, moderada, grande]
- Consistência: [Espesso tipo 'nata', bolhoso, fluido]
- Sintomas associados: [Coceira, ardor, dispareunia, disúria]
- Relação com ciclo menstrual: [Piora antes/depois da menstruação]
- Episódios prévios: [Já teve algo similar antes?]

**Dor Articular/Rigidez**
- Início: [Quando começou? Súbito ou gradual?]
- Localização: [Quais articulações? Padrão simétrico?]
- Número de articulações acometidas: [Uma, poucas (2-4) ou muitas (>4)?]
- Caráter: [Tipo de dor: latejante, em peso, em pontada]
- Intensidade: [Escala 0-10]
- Padrão da dor: [Pior pela manhã (inflamatório) ou no fim do dia (mecânico)?]
- Fator de melhora com atividade física: [A dor melhora com o movimento inicial?]
- Rigidez matinal: [Presente? Duração? >1h sugere inflamação]
- Sinais inflamatórios: [Articulações ficam inchadas, quentes, vermelhas?]
- Limitação funcional: [Impacto nas atividades diárias]
- Sintomas sistêmicos: [Febre, perda de peso, lesões cutâneas]
- Episódios prévios: [Já teve algo similar antes?]

**Alterações Neurológicas**
- Início: [Súbito ou gradual? Quando iniciou?]
- Tipo: [Fraqueza (paresia), alteração de sensibilidade (parestesia)]
- Localização: [Onde exatamente? Padrão de distribuição? Lado do corpo?]
- Evolução: [Está piorando, melhorando ou estável?]
- Fatores desencadeantes: [Trauma, posição, movimento?]
- Sintomas associados: [Alteração visual, fala, marcha, consciência]

### SINTOMAS GERAIS/SISTÊMICOS - Padrões de Script

**Febre:**
- "Estou com febre há alguns dias"
- Características: temperatura máxima, padrão (contínua, intermitente, remitente), duração
- Sintomas associados: calafrios, sudorese, mialgia, cefaleia

**Perda de Peso:**
- "Tenho emagrecido muito sem fazer dieta"
- Características: quantidade de peso perdido e em quanto tempo, se foi intencional ou não
- Sintomas associados: alteração de apetite (aumentado ou diminuído), fadiga, alterações intestinais
---
### **6. TIPOS DE IMPRESSOS POR CATEGORIA

### EXAMES LABORATORIAIS (tipoConteudo: "lista_chave_valor_secoes")

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
        { "chave": "Ureia", "valor": "X mg/dL (VR: X - X mg/dL)" },
        { "chave": "Creatinina", "valor": "X mg/dL (VR: X - X mg/dL)" }
      ]
    },
    {
      "tituloSecao": "GLICEMIA",
      "itens": [
        { "chave": "Glicose jejum", "valor": "X mg/dL (VR: X - X mg/dL)" }
      ]
    },
    {
      "tituloSecao": "GASOMETRIA",
      "itens": [
        { "chave": "pH", "valor": "[Valor] (Ref: [7.35-7.45])" },
        { "chave": "pCO2", "valor": "[Valor] mmHg (Ref: [35-45])" },
        { "chave": "pO2", "valor": "[Valor] mmHg (Ref: [75-100])" },
        { "chave": "HCO3", "valor": "[Valor] mEq/L (Ref: [22-26])" }
      ]
    }
  ]
}
```

### EXAMES DE IMAGEM (tipoConteudo: "imagemComLaudo")

```

**Radiografia Simples:**

```json

{
                "idImpresso": "[]",
                "tituloImpresso": "Radiografia de [região] em [incidência]",
                "tipoConteudo": "imagemComLaudo",
                "conteudo": {
                    "textoDescritivo": "[ATENÇÃO: DIRIJA-SE PARA A CÂMERA E EXPLIQUE OS ACHADOS NA IMAGEM].",
                    "caminhoImagem": "[BUSQUE NA INTERNET UMA IMAGEM RELACIONADA A IMAGEM EM QUESTAO DO IMPRESSO E COPIE O LINK DO SITE QUE CONTEM A IMAGEM E NAO O LINK DA IMAGEM EM SI, E DE REFERENCIAIS DE QUAL LOCAL DO SITE OU DOCUMENTO ENCONTRAR]",
                    "laudo": "[descreva o laudo da imagem pesquisada]."
               
   }
}

```

**Tomografia Computadorizada:**


```json
{
                "idImpresso": "[]",
                "tituloImpresso": "Tomografia Computadorizada de [região] em [incidência]",
                "tipoConteudo": "imagemComLaudo",
                "conteudo": {
                    "textoDescritivo": "[ATENÇÃO: DIRIJA-SE PARA A CÂMERA E EXPLIQUE OS ACHADOS NA IMAGEM].",
                    "urlImagem": "[BUSQUE NA INTERNET UMA IMAGEM RELACIONADA A IMAGEM EM QUESTAO DO IMPRESSO E COPIE O LINK DO SITE QUE CONTEM A IMAGEM E NAO O LINK DA IMAGEM EM SI, E DE REFERENCIAIS DE QUAL LOCAL DO SITE OU DOCUMENTO ENCONTRAR]",
                    "laudo": "[descreva o laudo da imagem pesquisada]."
  }
}
```

**Ultrassonografia:**
```json
{
  "idImpresso": "[]",
                "tituloImpresso": "Ultrassonografia de [região/órgão] em [incidência]",
                "tipoConteudo": "imagemComLaudo",
                "conteudo": {
                    "textoDescritivo": "[ATENÇÃO: DIRIJA-SE PARA A CÂMERA E EXPLIQUE OS ACHADOS NA IMAGEM].",
                    "urlImagem": "[BUSQUE NA INTERNET UMA IMAGEM RELACIONADA A IMAGEM EM QUESTAO DO IMPRESSO E COPIE O LINK DO SITE QUE CONTEM A IMAGEM E NAO O LINK DA IMAGEM EM SI, E DE REFERENCIAIS DE QUAL LOCAL DO SITE OU DOCUMENTO ENCONTRAR]",
                    "laudo": "[descreva o laudo da imagem pesquisada]."
  }
}
```

### EXAMES FÍSICOS (tipoConteudo: "lista_chave_valor_secoes")

**Sinais Vitais Padrão:**
```json
{
  "secoes": [
    {
      "tituloSecao": "SINAIS VITAIS",
      "itens": [
        {"chave": "Pressão arterial", "valor": "XXX × XX mmHg"},
        {"chave": "Frequência cardíaca", "valor": "XX bpm"},
        {"chave": "Frequência respiratória", "valor": "XX irpm"},
        {"chave": "Temperatura", "valor": "XX,X °C"},
        {"chave": "Saturação O2", "valor": "XX% em ar ambiente"}
      ]
    }
  ]
}
```

**Exame Físico por Sistemas:**
```json
{
  "secoes": [
    {
      "tituloSecao": "ESTADO GERAL",
      "itens": [
        {"chave": "Estado geral", "valor": "[Descrição completa do aspecto geral]"}
      ]
    },
    {
      "tituloSecao": "APARELHO CARDIOVASCULAR",
      "itens": [
        {"chave": "Ausculta cardíaca", "valor": "[Achados específicos]"}
      ]
    },
    {
      "tituloSecao": "APARELHO RESPIRATÓRIO",
      "itens": [
        {"chave": "Ausculta pulmonar", "valor": "[Achados específicos]"}
      ]
    }
  ]
}
```

---
### **7. DIRETRIZES AVANÇADAS PARA CONSTRUÇÃO DO PEP (CHECKLIST) ⚖️

O PEP é o coração da avaliação. Sua qualidade define a justiça e a objetividade da estação.

### **7.1. Mapeamento Direto e Critérios Quantitativos**
Cada item de anamnese no PEP deve ser um espelho de uma informação disponível no roteiro. Os critérios de pontuação devem ser numéricos e não subjetivos.
* **Padrão:** "Pergunta sobre X, Y, Z..."
* **Critério:** "Adequado: Pergunta sobre 4 ou 5 itens. Parcialmente Adequado: Pergunta sobre 2 ou 3 itens".

### **7.2. Avaliando o "Saber Não Fazer" (Ações Negativas)**
Pontue positivamente a abstenção de condutas inadequadas ou perigosas.
* **Exemplo Prático (Estação Placenta Prévia):** O PEP atribui nota máxima para o candidato que **não solicita ou contraindica** o toque vaginal.
* **Exemplo Prático (Estação Criptorquidia):** O PEP atribui nota máxima para quem **não indica** exame de imagem na abordagem inicial.

### **7.3. Decompondo Habilidades Práticas (Avaliação Procedimental)**
Divida uma habilidade técnica em passos críticos e observáveis.
* **Exemplo Prático (Estação de Sutura):** O PEP possui itens separados para **preparo do material** (lavar mãos, calçar luvas, aspirar anestésico), **etapas do procedimento** (antissepsia, infiltração) e **técnica da sutura** (uso de instrumentos, coaptação de bordas, nós).

### **7.4. Avaliando Protocolos de Comunicação e Emergência**
Estruture o PEP para seguir a sequência de um protocolo estabelecido.
* **Comunicação (SPIKES):** Crie itens que correspondam a cada letra do mnemônico (Setting, Perception, Invitation, Knowledge, Emotions, Strategy/Summary).
* **Emergência (ATLS):** Crie itens que avaliem a execução correta e na ordem certa das etapas do protocolo (A, B, C, D, E) e as intervenções críticas.

### **7.5. Integrando Saúde Coletiva e Profissionalismo**
Inclua itens que avaliem responsabilidades mais amplas.
* **Notificação Compulsória:** Para doenças como dengue, acidentes com animais peçonhentos e violência, inclua um item "Verbaliza a necessidade de notificação do caso ao SINAN".
* **Profissionalismo:** Em casos de discriminação (Ex: Estação de Prevenção em Mulher Lésbica), avalie a postura empática, o pedido de desculpas em nome da equipe e o compromisso de ação gerencial.
## 4. PADRÕES PEP POR TIPO DE AVALIAÇÃO

### **7.6. Quantidade de itens de avaliação**

  - **PADRÃO DAS ESTAÇÕES:** Varia consideravelmente, tipicamente entre 10 e 15 itens por estação. Estações com foco em orientação e manejo de condições crônicas (Ex: Obesidade, com 15 itens) tendem a ter mais itens de avaliação do que estações de procedimento agudo (Ex: Sutura, com 10 itens).
  - **Conclusão:** Para seu objetivo didático de criar estações mais "difíceis", aumentar a granularidade para 12 a 15 itens de avaliação é uma estratégia excelente, pois permite avaliar mais detalhadamente o raciocínio e a conduta do candidato.

### **7.6. Distribuição de Pontos e Critérios de Pontuação**

  - A pontuação reflete a complexidade da tarefa.

  - **Baixo Peso (0.25 - 0.5 pontos):** Tarefas de comunicação inicial (apresentar-se, cumprimentar), notificação ao SINAM (padrao é 0,5), encaminhamento ao especialista (0,5) e resposta de dúvidas (0,5), orientações e retorno (0,25 a 0,5).

  - **Peso Médio (1.0 - 1.5 pontos):** Anamnese dirigida, solicitação de exames complementares e interpretação correta, exames laboratoriais específicos ou manobras/exames físicos específicos, Diagnósticos diferenciais (mais que 5, o máximo que se pode citar), Fatores de risco (mais que 5, o máximo que se pode citar), solicitação e interpretação de achados nos exames de imagem.

  - **Alto Peso (2.0 - 2.5 pontos):** Formulação do diagnóstico correto e completo, sempre citando a síndrome + a causa, pode ter mais de um diagnóstico corretos, (Ex:lombalgia inflamatória ou espondiloartropatia inflamatória ou espondiloartrite axial ou espondilite anquilosante, ou seja, sinonimos também valem) ou o diagnóstico mais o agente etiológico, (Ex: pneumonia grave com sepse, abdômen agudo inflamatório devido a apendicite aguda, exantema súbito causado pelo agente etiológico herpes vírus), e indicação da conduta terapêutica definitiva.

  - O critério `parcialmenteAdequado` é um recurso-chave, usado para diferenciar o conhecimento completo do incompleto (ex: citar 2 de 4 diagnósticos diferenciais, ao invés de realizar o diagnostico de dengue realizou de arbovirose, ao inves de eritema infeccioso por parvovirus b19, apenas eritema infeccioso, etc), .

  - **Conclusão:** Ao definir as pontuações, siga essa lógica de complexidade. Para aumentar a dificuldade, você pode exigir mais elementos no critério "adequado" de um item de alto peso, tornando o "parcialmenteAdequado" mais provável e, assim, diferenciando melhor os candidatos. A sua proposta de padronizar a `descricaoItem` com enumeração numérica facilitará enormemente a criação de critérios de pontuação mais justos e objetivos.

### **7.7 . Diretrizes para Construção de Itens de Avaliação**

**Listagem dos Itens de Avaliação:** Para cada tarefa, desmembre as ações esperadas em `itensAvaliacao` granulares, ou seja, nunca crie itens que abordem múltiplos contextos ou diagnósticos (diagnostico final juntamente com diagnosticos diferenciais) em um único item. Siga o padrão

2.  **Descrição Quantitativa:** Escreva a `descricaoItem` de cada item usando a padronização de enumeração numérica, Ex: '"descricaoItem": "Questiona a presença dos seguintes sintomas associados no MIE:\n(1) palidez OU alteração da cor do membro;\n(2) frialdade (poiquilotermia) ou alteração de temperatura;\n(3) parestesia / formigamento/ alteração da sensibilidade;\n(4) alteração de mobilidade OU dificuldade para caminhar;\n(5) edema.",'

3.  **Atribuição de Pontos:** Defina as `pontuacoes` para cada item, balanceando os pesos conforme a complexidade e garantindo que a soma total seja 10.0. Crie critérios claros para `adequado`, `parcialmenteAdequado` e `inadequado`.

**EXEMPLO ORIGINAL ITEM ANAMNESE:**
```json
{
  "descricaoItem": "Anamnese - Caracterização da Doença Atual: Investiga de forma completa:\n(1) características da dor torácica (início, tipo, localização, irradiação, intensidade, fatores de piora/melhora);\n(2) características da dispneia (início, progressão, relação com decúbito);\n(3) cronologia do quadro (relação com a crise álgica prévia);\n(4) sintomas associados (febre, tosse)."
}
```

**APLICAR DESMEMBRAMENTO:**

**Item 1 - Investigação do Sintoma Principal:**

```json
{
  "descricaoItem": "Anamnese - Caracterização da Dor Torácica: Investiga de forma completa:\n(1) início;\n(2) tipo/qualidade;\n(3) localização;\n(4) intensidade;\n(5) irradiação;\n(6) fatores de melhora/atenuantes;\n(7) fatores de piora/agravantes;\n(8) uso de medicação de alívio;\n(9) episódios anteriores" 
}
```

**Item 2 - Sintomas/Sinais Acompanhantes:**
```json
{
  "descricaoItem": "Investiga Sintomas Associados:\n(1) dispneia;\n(2) tosse;\n(3) hemopstise;\n(4) dor torácica;\n(5) febre;\n(6) dor abdominal;\n(7) cefaleia;\n(8) desmaio;\n(9) lipotimia;\n(10) náuseas;\n(11) vômitos;\n(12) calafrios;\n(13) sudorese;\n(14) perda de peso não intencional"
}

*** OBS: Adicionar todas as características associadas mesmo que o paciente negue, sempre que tiver relevância para o caso e manter todos os sintomas associados, sempre nessa estrutura.***

```
 ### 7.8  REGRAS ESPECIAIS ###

- **O item diagnóstico pode conter mais de um diagnóstico correto (Ex: lombalgia inflamatória ou espondiloartropatia inflamatória ou espondiloartrite axial ou espondilite anquilosante) ou seja, sinonimos também valem, desde que sejam sinonimos de diagnosticos completos, e não sindromicos**

- **Sempre detalhar ao maximo cada informação/caracteristica de cada item, e sempre inserir o maximo de itens relevantes ao caso, nunca citando exemplos, apenas colocando entre parenteses referencias (Ex: (1) indica a reposição de Vitamina B12 (cianocobalamina ou hidroxocobalamina);)**

- **Quando um item do PEP abordar investigação completa de sintoma principal + sintomas associados, SEMPRE dividir em 2 itens distintos:**

- **Quando um item do PEP abordar DIAGNÓSTICO + diagnósticos diferenciais, SEMPRE dividir em 2 itens distintos:**

- ***sempre crie um novo iten de avaliação para cada 'contextoOuPerguntaChave' da anamnse**

Um novo item para cada sintoma da Historia da doença atual separe os sintomas principais/guia se mais que um (Ex: Se os sintomas do motivo de consulta forem Febre e Exantema, crie um item para cada), também um item somente para sintomas acompanhantes/associados. Quando presente os `contextoOuPerguntaChave` : antecedentes (Ex: Patologicos pessoais e familiares, epidemiológicos, ginecológicos, etc) crie sempre um item para cada tipo de antecedentes (se tiver mais que um, mas recomenda ser apenas se tiver relevancia clinica e seja importante) e o `contextoOuPerguntaChave` : hábitos (tabagismo, etilismo,drogas ilicitas, atividade física, dieta, sono, ingesta hidrica) tambem deve ser em um item separado (todos os hábitos em um item novo) . Todo novo `contextoOuPerguntaChave`, o campo `informacao` deve ser caracterizado individualmente e quantitativamente, as informaçoes devem ser muito bem detalhadas e com o máximo de informações possiveis, mesmo que seja negado pelo paciente, mas que seja essencial investigar tanto em relação a suspeita diagnostica quanto para os diagnosticos diferenciais.Nunca exiba no campo `contextoOuPerguntaChave` com informações/caracteristicas entre parenteses (Ex: 'Realiza anamnese da queixa principal:\n(1) caracteriza a dor epigástrica (localização, qualidade, intensidade, duração, evolução), sempre exiba cada caracteristica ou informação após o titulo da descrição do item seguido por dois pontos e as informações enumeradas (1) e paradas por ponto e virgula (1) info ; (2) info2; (3) info3. , a ultima informação nao necessita ponto e virgula, apenas ponto ou deixe sem pontuação ou caracterer nenhum(Ex:"descricaoItem": "Pergunta sobre as características da menstruação:\n(1) frequência OU regularidade OU intervalo;\n(2) volume de sangramento OU quantidade OU uso de absorvente;\n(3) duração do fluxo;\n(4) presença de cólicas."). E essas mesmas orientações valem para todos os demais `contextoOuPerguntaChave` do campo anamnse. sendo divida em dois itens de avaliação todo sintoma principal da história da doença atual, crie um novo item para a febre e outro para o exantema, contendo todas as informações descritas pelo paciente detalhadas individualmente e separadas, e também as que não constam mais são importantes para o caso, sempre o máximo possível. Essa mesma regra vale para Exame fisico geral e sinais vitais, Ectoscopia (Quando tiver um impresso com tipoConteudo imagemComLaude), Exames laboratoriais, exames de imagem, sorologias, para diagnostico, diagnosticos diferenciais, tratamentos, etc.

- ***sempre crie um item exclusivo para notificação, exatamente assim "Notificação ao SINAM" valendo sempre 0.5 pontos adequado e sem pontuação parcial e sempre o último item do pep**

- ***sempre que tiver impressos na estação, crie um item específico para cada impresso, descrevendo seu conteúdo e relevância para o caso.**

### 7.9  Padronização dos Itens do PEP (Regras Fundamentais obrigatórias para estrutura dos itens de avaliação)

### DESCRIÇÃO DO ITEM (descricaoItem): ###
- Deve conter TODAS as informações específicas e detalhadas
- Listar todos os elementos a serem avaliados numerados: (1), (2), (3), etc.
- Na descrição dos itens do pep NUNCA DEVE CONTER informações entre parênteses - apenas os elementos puros, nunca deve estar assim: "Realiza anamnese, investigando os sinais de alarme:\n(1) cronologia da febre;\n(2) mudança no aspecto das lesões de pele;\n(3) presença de dor local nas lesões;\n(4) alteração do estado geral da criança;\n(5) pus;\n(6) rubor/eritema;\n(7) sangue;\n(8) hipoatividade;\n(9) prostração"

**CRITÉRIOS DE PONTUAÇÃO (pontuacoes):**
- Em 'Critérios e Pontuações do Item' os textos desse campo Devem ser GENÉRICOS e quantitativos e/ou qualitativos, ex: Realizou os dois itens corretamente, Realizou 5 ou 6 itens corretamente, Executou corretamente o primeiro item obrigatoriamente e mais 2 itens... e nunca explicações extensas, as explicações e os itens devem estar no contexto em "Descrição do Item de Avaliação, siga o padrao do inep:"
- Referenciar apenas a quantidade de itens corretos
- Exemplo: "indica corretamente os dois itens", "indica apenas um item"

**EXEMPLO CORRETO:**
```json
{
  "descricaoItem": "Indica corretamente a necessidade de suporte hemoterápico e define o destino do paciente: (1) indica a necessidade de transfusão de concentrado de hemácias; (2) indica a internação hospitalar em unidade de terapia intensiva ou semi-intensiva",
  "pontuacoes": {
    "adequado": {"criterio": "indica corretamente os dois itens", "pontos": 1.5},
    "parcialmenteAdequado": {"criterio": "indica corretamente apenas um item", "pontos": 0.75},
    "inadequado": {"criterio": "não indica adequadamente nenhum item", "pontos": 0.0}
  }
}
```
 ### PADRÕES ESPECIFICOS POR ESPECIALIDADE  ###


 ### APRESENTAÇÃO E COMUNICAÇÃO (Padrão Universal Para todas especialidades)  ###

```json
{
  "descricaoItem": "Apresentação:\n(1) Apresenta-se e (2) cumprimenta o paciente simulado.",
  "pontuacoes": {
    "adequado": {"criterio": "realiza as duas ações", "pontos": 0.5},
    "parcialmenteAdequado": {"criterio": "realiza apenas uma ação", "pontos": 0.25},
    "inadequado": {"criterio": "não realiza nenhuma das ações", "pontos": 0.0}
  }
}
```

### PADRÃO PARA MEDICINA DA FAMÍLIA E COMUNIDADE  ###

***SEMPRE os três primeiros itens do pep em medicina da familia e comunidade SEMPRE devem ser esses 3 A SEGUIR:***

```json
[
  {
    "idItem": "pep_est10_item01",
    "itemNumeroOficial": "1",
    "descricaoItem": "Apresentação:\n(1) cumprimenta o paciente simulado;\n(2) identifica-se;\n(3) dirige-se ao paciente simulado pelo nome, pelo menos uma vez;\n(4) pergunta o motivo da consulta.",
    "pontuacoes": {
      "adequado": {"criterio": "Realiza as quatro ações.", "pontos": 0.5},
      "parcialmenteAdequado": {"criterio": "Realiza duas ou três ações.", "pontos": 0.25},
      "inadequado": {"criterio": "Realiza apenas uma ação ou não realiza ação alguma.", "pontos": 0.0}
    }
  },
  {
    "idItem": "pep_est10_item02",
    "itemNumeroOficial": "2",
    "descricaoItem": "Postura:\n(1) estabelece contato visual;\n(2) mantém postura empática ao longo da consulta;\n(3) escuta a fala do paciente simulado sem interrompê-lo.",
    "pontuacoes": {
      "adequado": {"criterio": "Realiza as três ações.", "pontos": 0.25},
      "parcialmenteAdequado": {"criterio": "Realiza apenas uma ou duas ações.", "pontos": 0.15},
      "inadequado": {"criterio": "Não realiza ação alguma.", "pontos": 0.0}
    }
  },
  {
    "idItem": "pep_est10_item03",
    "itemNumeroOficial": "3",
    "descricaoItem": "Responde às perguntas/dúvidas do paciente simulado.",
    "pontuacoes": {
      "adequado": {"criterio": "Responde às perguntas/dúvidas.", "pontos": 0.25},
      "parcialmenteAdequado": {"criterio": "Não aplicável.", "pontos": 0.0},
      "inadequado": {"criterio": "Não responde às perguntas/dúvidas.", "pontos": 0.0}
    }
  }
]
```

### PADRÃO PARA PEDIATRIA  ###

***SEMPRE os dois primeiros itens do pep em pediatria devem ser esses dois a seguir:***

```json
[
  {
    "idItem": "pep_est10_item01",
    "itemNumeroOficial": "1",
    "descricaoItem": "Apresentação: (1) Identifica-se; (2) Cumprimenta a mãe de maneira adequada/cordial; (3) Mantém contato visual durante sua apresentação; (4) Pergunta o nome da mãe e o nome da criança",
    "pontuacoes": {
      "adequado": {"criterio": "Realiza 3-4 subitens", "pontos": 0.5},
      "parcialmenteAdequado": {"criterio": "Realiza 1-2 subitens", "pontos": 0.25},
      "inadequado": {"criterio": "Não realiza nenhum subitem", "pontos": 0.0}
    }
  },
  {
    "itemNumeroOficial": "2",
    "descricaoItem": "Pergunta sobre a queixa principal: (1) pergunta o motivo da consulta; (2) deixa a mãe explicar sem interrompê-la",
    "pontuacoes": {
      "adequado": {"criterio": "Realiza ambos os subitens", "pontos": 0.5},
      "parcialmenteAdequado": {"criterio": "Não se aplica", "pontos": 0.0},
      "inadequado": {"criterio": "Não realiza adequadamente", "pontos": 0.0}
    }
  }
]
```

### ANAMNESE - Padrões por Especialidade  ###

**Clínica Médica - Anamnese Completa (destrinchamento do sintoma guia principal(dor)):**
```json
{
        "idItem": "pep_est01_item02",
        "itemNumeroOficial": "2",
        "descricaoItem": "Realiza anamnese, perguntando sobre as características da dor:\n(1) início;\n(2) frequência;\n(3) fatores desencadeantes;\n(4) agravantes;\n(5) atenuantes;\n(6) intensidade;\n(7) irradiação;\n(8) despertar noturno;\n(9) rigidez matinal.",
        "pontuacoes": {
          "adequado": {"criterio": "Pergunta sobre 6 ou mais características da dor", "pontos": 1.5},
          "parcialmenteAdequado": {"criterio": "Pergunta sobre 3 a 5 características da dor", "pontos": 0.75},
          "inadequado": {"criterio": "Pergunta sobre menos de 3 características ou não pergunta", "pontos": 0.0}
        }
      },
```

**Pediatria - Anamnese Dirigida ao Responsável:**
```json
{
  "descricaoItem": "Realiza anamnese dirigida ao responsável, investigando:\n(1) características da queixa principal;\n(2) antecedentes perinatais;\n(3) desenvolvimento neuromotor;\n(4) alimentação;\n(5) imunização.",
  "pontuacoes": {
    "adequado": {"criterio": "investiga 4 ou 5 elementos", "pontos": 1.0},
    "parcialmenteAdequado": {"criterio": "investiga 2 ou 3 elementos", "pontos": 0.5},
    "inadequado": {"criterio": "investiga apenas 1 elemento ou nenhum", "pontos": 0.0}
  }
}
```

### EXAME FÍSICO - Padrões de Solicitação e Interpretação

**Padrão Geral:**
```json
{
  "descricaoItem": "Solicita e interpreta adequadamente o exame físico.",
  "pontuacoes": {
    "adequado": {"criterio": "solicita e interpreta adequadamente", "pontos": 1.0},
    "inadequado": {"criterio": "não solicita ou não interpreta adequadamente", "pontos": 0.0}
  }
}
```

**Padrão Específico por Sistema:**
```json
{
  "descricaoItem": "Solicita exame físico específico:\n(1) inspeção;\n(2) palpação;\n(3) ausculta;\n(4) manobras especiais.",
  "pontuacoes": {
    "adequado": {"criterio": "solicita os 4 exames", "pontos": 1.5},
    "parcialmenteAdequado": {"criterio": "solicita 2 exames", "pontos": 0.75},
    "inadequado": {"criterio": "não solicita", "pontos": 0.0}
  }
}
```

### EXAMES COMPLEMENTARES - Padrões de Solicitação

**Laboratoriais Básicos:**
```json
{
  "descricaoItem": "Solicita os exames laboratoriais e interpreta corretamente:\n(1) hemograma;\n(2) PCR e(ou) VHS;\n(3) creatinina e(ou) ureia;\n(4) sódio e(ou) potássio;\n(5) rotina de urina / sumário de urina / urina tipo 1;\n(6) beta-HCG.",
  "pontuacoes": {
    "adequado": {"criterio": "Solicita cinco ou seis itens.", "pontos": 1.0},
    "parcialmenteAdequado": {"criterio": "solicita 4 exames", "pontos": 0.5},
    "inadequado": {"criterio": "Solicita três ou menos itens.", "pontos": 0.0}
  }
}
```

**Exames de Imagem:**
```json
{
  "descricaoItem": "Solicita exames de imagem apropriados:\n(1) radiografia;\n(2) ultrassonografia;\n(3) tomografia computadorizada.",
  "pontuacoes": {
    "adequado": {"criterio": "solicita exames adequados", "pontos": 1.5},
    "parcialmenteAdequado": {"criterio": "solicita parcialmente", "pontos": 0.75},
    "inadequado": {"criterio": "não solicita ou solicita inadequadamente", "pontos": 0.0}
  }
}
```

### DIAGNÓSTICO - Padrões de Formulação

**Diagnóstico Principal:**
```json
{
  "descricaoItem": "Estabelece o diagnóstico correto.",
  "pontuacoes": {
    "adequado": {"criterio": "estabelece o diagnóstico correto", "pontos": 2.0},
    "parcialmenteAdequado": {"criterio": "estabelece um diagnóstico correto, mas incompleto ou impreciso", "pontos": 1.0},
    "inadequado": {"criterio": "não estabelece o diagnóstico correto", "pontos": 0.0}
  }
}
```

**Diagnósticos Diferenciais:**
```json
{
  "descricaoItem": "Cita diagnósticos diferenciais relevantes:\n(1) diagnóstico diferencial 1;\n(2) diagnóstico diferencial 2;\n(3) diagnóstico diferencial 3.",
  "pontuacoes": {
    "adequado": {"criterio": "cita 2 ou mais diagnósticos diferenciais corretos", "pontos": 1.0},
    "parcialmenteAdequado": {"criterio": "cita apenas 1 diagnóstico diferencial correto", "pontos": 0.5},
    "inadequado": {"criterio": "não cita diagnósticos diferenciais ou cita incorretamente", "pontos": 0.0}
  }
}
```

### CONDUTA TERAPÊUTICA - Padrões de Prescrição

**Tratamento Medicamentoso:**
```json
{
  "descricaoItem": "Prescreve tratamento medicamentoso adequado.",
  "pontuacoes": {
    "adequado": {"criterio": "prescreve medicação adequada", "pontos": 1.5},
    "parcialmenteAdequado": {"criterio": "prescreve parcialmente adequado", "pontos": 0.75},
    "inadequado": {"criterio": "não prescreve ou prescreve inadequadamente", "pontos": 0.0}
  }
}
```

**Orientações Gerais:**
```json
{
  "descricaoItem": "Orienta sobre:\n(1) medidas não farmacológicas;\n(2) sinais de alerta;\n(3) seguimento;\n(4) prevenção.",
  "pontuacoes": {
    "adequado": {"criterio": "orienta sobre 3 ou 4 aspectos", "pontos": 1.0},
    "parcialmenteAdequado": {"criterio": "orienta sobre 1 ou 2 aspectos", "pontos": 0.5},
    "inadequado": {"criterio": "não orienta adequadamente", "pontos": 0.0}
  }
}
```

## 8. ESTRUTURAS ESPECÍFICAS POR ESPECIALIDADE

### CLÍNICA MÉDICA - Características Distintivas

**Cenários Típicos:**
- Atenção secundária/terciária
- Casos ambulatoriais e hospitalares
- Integração clínico-laboratorial importante
- Diagnósticos diferenciais complexos

**Exames Mais Utilizados:**
- Hemograma completo
- Bioquímica abrangente
- Tomografia computadorizada
- Ecocardiograma
- Endoscopias

**PEP Característicos:**
- 8-12 itens de avaliação
- Ênfase na interpretação de exames
- Correlação clínico-laboratorial
- Diagnósticos diferenciais (1-2 pontos)

### CIRURGIA GERAL - Características Distintivas

**Cenários Típicos:**
- Urgência/emergência frequente
- Atenção secundária/terciária
- Decisões terapêuticas críticas
- Indicações cirúrgicas

**Exames Mais Utilizados:**
- Exame físico detalhado
- Tomografia computadorizada
- Ultrassonografia
- Radiografias simples
- Exames laboratoriais básicos

**PEP Característicos:**
- 8-10 itens de avaliação
- Ênfase no exame físico
- Indicações cirúrgicas (pontuação alta)
- Manejo de urgências

### PEDIATRIA - Características Distintivas

**Cenários Típicos:**
- Puericultura vs urgência
- Interação com responsáveis
- Crescimento e desenvolvimento
- Prevenção importante

**Exames Específicos:**
- Curvas de crescimento
- Dados antropométricos
- Caderneta da criança
- Exames específicos pediátricos

**PEP Característicos:**
- 8-12 itens de avaliação
- Avaliação do crescimento (pontuação alta)
- Orientações aos pais (pontuação significativa)
- Prevenção e seguimento

### GINECOLOGIA E OBSTETRÍCIA - Características Distintivas

**Cenários Típicos:**
- Urgências obstétricas
- Consultas ginecológicas
- Emergências reprodutivas
- Prevenção em saúde da mulher

**Exames Específicos:**
- Exame ginecológico
- Ultrassonografia pélvica/obstétrica
- Exames hormonais
- Teste de gravidez
- Colpocitologia oncótica

**PEP Característicos:**
- 10-15 itens de avaliação
- Exame físico ginecológico (pontuação alta)
- Diagnósticos diferenciais específicos
- Urgências obstétricas (pontuações altas)

### MEDICINA DA FAMÍLIA - Características Distintivas

**Cenários Típicos:**
- Atenção primária
- Prevenção e promoção
- Abordagem comunitária
- Casos endêmicos/notificáveis

**Abordagens Específicas:**
- Contexto socioepidemiológico
- Notificação compulsória
- Educação em saúde
- Prevenção primária

**PEP Característicos:**
- 12-15 itens de avaliação
- Comunicação e empatia (pontuação significativa)
- Medidas preventivas (pontuação alta)
- Abordagem comunitária
- Notificação quando aplicável (infectologia, doenças de notificação compulsória, saúde mental, etc)

---

## 9. CHECKLIST DE VALIDAÇÃO FINAL DA ESTAÇÃO (NOVO) ##


***ORIENTAÇÕES GERAIS***

**Você separou cada caracteristicas dos sintomas / sinais individualmente nas informações de cada contexto do roteiro do ator? OBS:Na caracterização do(s) 'sintoma principal/sintoma guia' do motivo de consulta, se for mais que duas ou mais caracteristicas em uma mesma informação sempre exibir o nome de cada um e não exibir esse campo, Ex: Caracteristica da macha: Dói, coça, descama e sangra, essa maneira está errado, crie informações separadas para cada uma, assim: \nDor: [Dói]\nPrurido: [Coça]\nDescamação: [Descama]\nSangramento: [Não sangra], que isso seja padrao, se for apenas uma caracteristica desconsidere essa orientação.**

- **Em toda doença infecciosa, ou quando tiver febre, ou sempre que o tema puder ter alterações no laboratorio SEMPRE incluir um impresso com todas as possiveis alterações laboratoriais,e para exames laboratoriais especificos sempre criar um impresso separado (ex: sorologias, marcadores, etc)**


**DESCRIÇÃO DO ITEM (descricaoItem):**
- Deve conter TODAS as informações específicas e detalhadas
- Listar todos os elementos a serem avaliados numerados: (1), (2), (3), etc.
- Na descrição dos itens do pep NUNCA DEVE CONTER informações entre parênteses - apenas os elementos puros, nunca deve estar assim: "Realiza anamnese, investigando os sinais de alarme:\n(1) cronologia da febre (padrão em 'V');\n(2) mudança no aspecto das lesões de pele (surgimento de pus ou vermelhidão intensa);\n(3) presença de dor local nas lesões;\n(4) alteração do estado geral da criança (hipoatividade/prostração)" , deve estar SEMPRE assim: \n(1) Padrão da febre (padrão em 'V');\n(2)Pus;(3)\nRubor/eritema;n(4)\n(sangue);\n(5) presença de dor local nas lesões;\n(6) hipoatividade; (7) prostração" ***o ultimo item deve terminar sem ponto nem ponto e virgula, sem nenhum caracter apos o item final

**CRITÉRIOS DE PONTUAÇÃO (pontuacoes):**
- Em 'Critérios e Pontuações do Item' os textos desse campo Devem ser GENÉRICOS e quantitativos e/ou qualitativos, ex: Realizou os dois itens corretamente, Realizou 5 ou 6 itens corretamente, Executou corretamente o primeiro item obrigatoriamente e mais 2 itens... e nunca explicações extensas, as explicações e os itens devem estar no contexto em "Descrição do Item de Avaliação, siga o padrao do inep:"
- Referenciar apenas a quantidade de itens corretos
- Exemplo: "indica corretamente os dois itens", "indica apenas um item"



Antes de finalizar, verifique se a estação cumpre todos os critérios abaixo:

[ ] Coerência Geral: O nível de atenção e a infraestrutura são compatíveis com o caso clínico?

[ ] Tarefas: As tarefasPrincipais refletem os desafios centrais da estação e usam verbos de ação claros?

[ ] Roteiro do Ator:

[ ] O MOTIVO DE CONSULTA é sucinto e em primeira pessoa?

[ ] Cada sintoma-guia tem seu próprio contextoOuPerguntaChave?

[ ] A semiologia de cada sintoma está completa, incluindo informações NEGATIVAS relevantes?

[ ] Tem um impresso separado para ECTOSCOPIA (pode ser de qualquer parte do corpo sem excessao), OROSCOPIA, RINOSCOPIA, OFTALMOSCOPIA, OTOSCOPIA,  quando for essencial para a estação, como em doenças que tenham alterações visuais? Ex: doenças enxatematicas, dengue, zica, que tenham ictericia, alterações anatomicas, ou qualquer achado relevante na ecostopia? e tiver relevancia clinica ?

[ ] A estação necessita de exames laboratoriais padroes? Como algum desses: Hemograma, pcr, vha, tgo, tgp, fostatasa alcalina, gama gt, perfil renal (ureia, creatinina) e eletrolitos (sódio, potassio, cloro, magnésio, calcio,etc), glicemia capilar/jejum/glicada, coagulograma, inr, lipidograma (ldl, hdl,colesterol total e trigliceridos)? OBS: Em toda doença infecciosa, ou quando tiver febre, ou sempre que o tema puder ter alterações no laboratorio SEMPRE incluir um impresso com todas as possiveis alterações laboratoriais,e para exames laboratoriais especificos sempre criar um impresso separado (ex: sorologias, marcadores, etc)**

[ ] Você separou cada caracteristicas dos sintomas / sinais individualmente nas informações de cada contexto do roteiro do ator? OBS:Na caracterização do(s) 'sintoma principal/sintoma guia' do motivo de consulta, se for mais que duas ou mais caracteristicas em uma mesma informação sempre exibir o nome de cada um e não exibir esse campo, Ex: Caracteristica da macha: Dói, coça, descama e sangra, essa maneira está errado, crie informações separadas para cada uma, assim: \nDor: [Dói]\nPrurido: [Coça]\nDescamação: [Descama]\nSangramento: [Não sangra], que isso seja padrao, se for apenas uma caracteristica desconsidere essa orientação.

[ ] Toda informação necessária para pontuar nos itens de anamnese do PEP está presente no roteiro?

[ ] Checklist de Avaliação (PEP):

[ ] MAPEAMENTO 1:1: Cada tarefaPrincipal tem seu(s) item(ns)Avaliacao correspondente(s)?

[ ] GRANULARIDADE: A anamnese foi desmembrada em itens distintos (sintoma principal, sintomas associados, antecedentes, hábitos)?

[ ] GRANULARIDADE: Diagnóstico está em um item SEPARADO da conduta? E SEPARADO dos diagnósticos diferenciais?

[ ] GRANULARIDADE: A conduta foi desmembrada em itens lógicos no PEP? (Ex: 1. Droga de escolha, 2. Via, 3. Dose)?

[ ] IMPRESSOS: Existe um item para a solicitação do impresso (qual impresso da estação) e sua interpretação de CADA impresso disponivel na estação?

[ ] OBJETIVIDADE: Os criterios de pontuação são quantitativos ("Realiza 6 ou mais 8 itens", "Cita 5 ou mais")?

[ ] PONTUAÇÃO: A soma total dos pontos de todos os itens é exatamente 10.0?

[ ] NOTIFICAÇÃO: Se for um caso de notificação compulsória (Ex: Dengue), o item "Menciona que fará a notificação do caso ao SINAN" foi adicionado? (Padrão: 0.5 pontos).

Este documento serve como referência completa para criação de novas estações baseadas nos padrões reais do INEP, garantindo fidelidade aos modelos oficiais e qualidade técnica das avaliações.


Este documento serve como referência completa para criação de novas estações baseadas nos padrões reais do INEP, garantindo fidelidade aos modelos oficiais e qualidade técnica das avaliações. 

---

## 10. REGRA APRENDIDA (Feedback do Usuário): - Esta é uma nova regra de teste que estou ensinando ao agente. "
(string)


Local do banco de dados: southamerica-east1 
