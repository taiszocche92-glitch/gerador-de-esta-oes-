firebase.js:34 🔥 Firebase App configurado
firebase.js:38 📦 Storage Bucket: revalida-companion.firebasestorage.app
firebase.js:39 🆔 Project ID: revalida-companion
firebase.js:40 🌍 Auth Domain: revalida-companion.firebaseapp.com
firebase.js:43 🔧 Variáveis de ambiente carregadas:
firebase.js:44 VITE_FIREBASE_STORAGE_BUCKET: revalida-companion.firebasestorage.app
firebase.js:45 VITE_FIREBASE_PROJECT_ID: revalida-companion
firebase.js:55 ✅ Cache do Firestore configurado via getFirestore()
firebase.js:71 🔧 Configurações de desenvolvimento do Firestore aplicadas
firebase.js:78 ✅ Storage inicializado com sucesso
firebase.js:79 � Storage URL: revalida-companion.firebasestorage.app
backendUrl.js:19 🔧 Backend URL configurada: http://localhost:3000
backendUrl.js:20 🌍 Ambiente: development
csp-monitor.js:141 🔍 Iniciando monitoramento de CSP...
csp-monitor.js:178 ✅ Monitoramento de CSP ativo
deployment-watcher.js:31 🔄 Vigia de deploy configurado para lidar com atualizações automáticas.
main.js:37 🚀 Performance metrics enabled
privateChatListener.js:15 🚀 Iniciando listener de chat privado para usuário: RtfNENOqMUdw7pvgeeaBVSuin662
useAdminAuth.js:42 🔍 Admin check by UID: Object
useAdminAuth.js:60 🔍 Admin check by role: Object
useAdminAuth.js:73 🔍 Final admin authorization: Object
AdminView.vue:2648 🚀 Componente montado - carregando abordagens padrão...
:8080/api/agent/generate-final-station:1 
            
            
           Failed to load resource: the server responded with a status of 500 (Internal Server Error)
AdminView.vue:1775 Erro ao gerar estação final: Error: Erro na Fase 3: {"detail":"A IA gerou uma resposta em formato JSON inválido: Invalid \\escape: line 50 column 517 (char 2663)"}
    at Proxy.handleGenerateFinalStation (AdminView.vue:1767:13)
handleGenerateFinalStation @ AdminView.vue:1775
firebase.js:34 🔥 Firebase App configurado
firebase.js:38 📦 Storage Bucket: revalida-companion.firebasestorage.app
firebase.js:39 🆔 Project ID: revalida-companion
firebase.js:40 🌍 Auth Domain: revalida-companion.firebaseapp.com
firebase.js:43 🔧 Variáveis de ambiente carregadas:
firebase.js:44 VITE_FIREBASE_STORAGE_BUCKET: revalida-companion.firebasestorage.app
firebase.js:45 VITE_FIREBASE_PROJECT_ID: revalida-companion
firebase.js:55 ✅ Cache do Firestore configurado via getFirestore()
firebase.js:71 🔧 Configurações de desenvolvimento do Firestore aplicadas
firebase.js:78 ✅ Storage inicializado com sucesso
firebase.js:79 � Storage URL: revalida-companion.firebasestorage.app
backendUrl.js:19 🔧 Backend URL configurada: http://localhost:3000
backendUrl.js:20 🌍 Ambiente: development
csp-monitor.js:141 🔍 Iniciando monitoramento de CSP...
csp-monitor.js:178 ✅ Monitoramento de CSP ativo
deployment-watcher.js:31 🔄 Vigia de deploy configurado para lidar com atualizações automáticas.
main.js:37 🚀 Performance metrics enabled
privateChatListener.js:15 🚀 Iniciando listener de chat privado para usuário: RtfNENOqMUdw7pvgeeaBVSuin662
useAdminAuth.js:42 🔍 Admin check by UID: Object
useAdminAuth.js:60 🔍 Admin check by role: Object
useAdminAuth.js:73 🔍 Final admin authorization: Object
AdminView.vue:2648 🚀 Componente montado - carregando abordagens padrão...
:8080/api/agent/generate-final-station:1 
            
            
           Failed to load resource: the server responded with a status of 500 (Internal Server Error)
AdminView.vue:1775 Erro ao gerar estação final: Error: Erro na Fase 3: {"detail":"A IA gerou uma resposta em formato JSON inválido: Invalid \\escape: line 50 column 517 (char 2663)"}
    at Proxy.handleGenerateFinalStation (AdminView.vue:1767:13)
handleGenerateFinalStation @ AdminView.vue:1775
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
