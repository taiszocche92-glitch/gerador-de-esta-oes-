# Estrutura Completa do Projeto - Sistema de Estações Clínicas

## 📊 Resumo Executivo

Este documento apresenta a estrutura completa do projeto **backend-python-agent**, um sistema modular para geração, gestão e análise de estações clínicas médicas utilizando IA (Gemini). O projeto contém **192 arquivos** organizados em uma arquitetura full-stack com backend em FastAPI (Python) e frontend em Vue.js.

---

## 🏗️ Estrutura de Diretórios e Arquivos

### 📁 Raiz do Projeto (backend-python-agent)

```
backend-python-agent/
├── 🐍 Arquivos Python Principais
│   ├── main.py                    # Servidor FastAPI principal
│   ├── gemini_client.py           # Configuração Gemini API
│   ├── ingest_and_index.py        # Ingestão e indexação
│   ├── rag_agent.py               # Agente RAG
│   ├── web_search.py              # Busca web
│   ├── requirements.txt           # Dependências Python
│   └── pyproject.toml             # Configuração de ferramentas
│
├── 📄 Arquivos de Configuração
│   ├── .env                       # Variáveis de ambiente
│   ├── .env.example               # Template de ambiente
│   ├── .gitignore                 # Regras Git
│   ├── dockerfile                 # Configuração Docker
│   ├── gabaritoestacoes.json      # Template JSON
│   ├── gerador.md                 # Documentação principal
│   ├── MODELOS_GEMINI_ATUAIS.md   # Modelos disponíveis
│   ├── OTIMIZACAO_CONCLUIDA.md   # Otimizações
│   ├── referencias.md            # Referências gerais
│   ├── CORRECOES_PYLANCE.md       # Correções Pylance
│   ├── tarefaincompleta.md        # Tarefas pendentes
│   ├── TEST_WEB_SEARCH.md         # Teste busca web
│   └── start-backend.ps1          # Script inicialização
│
├── 🎨 Arquivos Frontend (Vue.js)
│   └── AdminView.vue              # Dashboard administrativo
│
├── 🧠 Sistema de Memória (memoria/)
│   ├── aprendizados_usuario.jsonl # Feedback do sistema
│   ├── config_memoria.json        # Configuração central
│   ├── file-list.md              # Lista completa de arquivos
│   ├── referencias_base.md       # Guia mestre
│   ├── serviceAccountKey.json    # Credenciais Firebase
│   ├── contexto_otimizado/       # Contexto por fase
│   │   ├── fase1_analise_planejamento.md
│   │   ├── fase2_roteiros_anamnese.md
│   │   ├── fase3_impressos_exames.md
│   │   └── fase4_checklist_pep.md
│   ├── monitoring/               # Sistema de monitoramento
│   │   ├── config_monitoring.json
│   │   └── monitor-files.ps1
│   ├── vectors/                  # Embeddings e vetores
│   │   ├── config.json
│   │   ├── embeddings.npy
│   │   ├── id_map.json
│   │   └── metadata.jsonl
│   └── versoes/                  # Sistema de versionamento
│       ├── config_versoes.json
│       ├── v1.0.0/               # Versão 1.0.0
│       ├── v1.0.1/               # Versão 1.0.1
│       ├── v1.0.2/               # Versão 1.0.2
│       ├── v1.0.3/               # Versão 1.0.3
│       ├── v1.0.4/               # Versão 1.0.4
│       ├── v1.0.5/               # Versão 1.0.5
│       └── v1.0.6/               # Versão 1.0.6
│
├── 📚 Provas INEP (provas inep/)
│   ├── 2022.1/                   # Semestre 1 de 2022 (9 arquivos)
│   ├── 2022.2/                   # Semestre 2 de 2022 (8 arquivos)
│   ├── 2023.1/                   # Semestre 1 de 2023 (10 arquivos)
│   ├── 2023.2/                   # Semestre 2 de 2023 (8 arquivos)
│   ├── 2024.1/                   # Semestre 1 de 2024 (11 arquivos)
│   ├── 2024.2/                   # Semestre 2 de 2024 (11 arquivos)
│   └── 2025.1/                   # Semestre 1 de 2025 (10 arquivos)
│
├── 🧪 Scripts (scripts/)
│   ├── debug_firebase_import.py   # Debug Firebase
│   └── debug_google_import.py    # Debug Google
│
├── 🧪 Testes (tests/)
│   ├── test_endpoint.ps1         # Teste endpoints PowerShell
│   ├── test_endpoints.py         # Teste endpoints Python
│   ├── test_gemini_key.py        # Teste Gemini key
│   ├── test_key_embeddings.py    # Teste embeddings
│   ├── test_key_http.py          # Teste HTTP keys
│   ├── test_key_http_embed.py    # Teste HTTP embeddings
│   ├── test_key_http_embed_v1.py # Teste HTTP embeddings v1
│   ├── test_rag.py               # Teste RAG
│   ├── test_rag_direct.py        # Teste RAG direto
│   ├── test_rag_generation.py     # Teste RAG geração
│   ├── test_sistema_hibrido.py   # Teste sistema híbrido
│   ├── test_web_search.py        # Teste busca web
│   ├── validate_embeddings.py    # Validação embeddings
│   └── validate_embeddings_extended.py # Validação extendida
│
├── 🧪 Testes Essenciais (tests_essenciais/)
│   ├── check_env.py              # Verificação ambiente
│   └── list_gemini_models.py     # Listagem modelos
│
├── 📚 API Documentation (api_docs/)
│   ├── endpoints.md              # Documentação endpoints
│   └── README.md                 # README da API
│
├── 📁 Configuração VS Code (.vscode/)
│   └── settings.json             # Configuração editor
│
└── 📋 Configuração Firebase (firebase.json)
```

---

## 📋 Lista Completa de Arquivos (192 arquivos)

### Arquivos Principais (10)
1. `.editorconfig` - Configuração editor
2. `.env` - Variáveis de ambiente
3. `.env.example` - Template ambiente
4. `.gitignore` - Regras Git
5. `AdminView.vue` - Dashboard frontend
6. `dockerfile` - Configuração Docker
7. `gabaritoestacoes.json` - Template JSON
8. `gemini_client.py` - Configuração Gemini
9. `gerador.md` - Documentação principal
10. `ingest_and_index.py` - Ingestão dados

### Arquivos Python (7)
11. `main.py` - Servidor FastAPI
12. `rag_agent.py` - Agente RAG
13. `web_search.py` - Busca web
14. `requirements.txt` - Dependências
15. `pyproject.toml` - Configuração ferramentas
16. `MODELOS_GEMINI_ATUAIS.md` - Modelos disponíveis
17. `OTIMIZACAO_CONCLUIDA.md` - Otimizações

### Arquivos Markdown (8)
18. `referencias.md` - Referências gerais
19. `CORRECOES_PYLANCE.md` - Correções Pylance
20. `tarefaincompleta.md` - Tarefas pendentes
21. `TEST_WEB_SEARCH.md` - Teste busca web
22. `memoria/file-list.md` - Lista arquivos
23. `memoria/referencias_base.md` - Guia mestre
24. `api_docs/endpoints.md` - Documentação API
25. `api_docs/README.md` - README API

### Sistema de Memória (15 arquivos)
26. `memoria/aprendizados_usuario.jsonl` - Feedback sistema
27. `memoria/config_memoria.json` - Configuração central
28. `memoria/serviceAccountKey.json` - Credenciais Firebase
29. `memoria/contexto_otimizado/fase1_analise_planejamento.md`
30. `memoria/contexto_otimizado/fase2_roteiros_anamnese.md`
31. `memoria/contexto_otimizado/fase3_impressos_exames.md`
32. `memoria/contexto_otimizado/fase4_checklist_pep.md`
33. `memoria/monitoring/config_monitoring.json`
34. `memoria/monitoring/monitor-files.ps1`
35. `memoria/vectors/config.json`
36. `memoria/vectors/embeddings.npy`
37. `memoria/vectors/id_map.json`
38. `memoria/vectors/metadata.jsonl`
39. `memoria/versoes/config_versoes.json`
40. `memoria/versoes/v1.0.0/config_memoria.json`
41. `memoria/versoes/v1.0.0/fase1_analise_planejamento.md`
42. `memoria/versoes/v1.0.0/fase2_roteiros_anamnese.md`
43. `memoria/versoes/v1.0.0/fase3_impressos_exames.md`
44. `memoria/versoes/v1.0.0/fase4_checklist_pep.md`
45. `memoria/versoes/v1.0.0/gabaritoestacoes.json`
46. `memoria/versoes/v1.0.0/metadata.json`
47. `memoria/versoes/v1.0.0/referencias_base.md`
48. `memoria/versoes/v1.0.1/aprendizados_usuario.jsonl`
49. `memoria/versoes/v1.0.1/config_memoria.json`
50. `memoria/versoes/v1.0.1/fase1_analise_planejamento.md`
51. `memoria/versoes/v1.0.1/fase2_roteiros_anamnese.md`
52. `memoria/versoes/v1.0.1/fase3_impressos_exames.md`
53. `memoria/versoes/v1.0.1/fase4_checklist_pep.md`
54. `memoria/versoes/v1.0.1/gabaritoestacoes.json`
55. `memoria/versoes/v1.0.1/metadata.json`
56. `memoria/versoes/v1.0.1/referencias_base.md`
57. `memoria/versoes/v1.0.2/aprendizados_usuario.jsonl`
58. `memoria/versoes/v1.0.2/config_memoria.json`
59. `memoria/versoes/v1.0.2/fase1_analise_planejamento.md`
60. `memoria/versoes/v1.0.2/fase2_roteiros_anamnese.md`
61. `memoria/versoes/v1.0.2/fase3_impressos_exames.md`
62. `memoria/versoes/v1.0.2/fase4_checklist_pep.md`
63. `memoria/versoes/v1.0.2/gabaritoestacoes.json`
64. `memoria/versoes/v1.0.2/metadata.json`
65. `memoria/versoes/v1.0.2/referencias_base.md`
66. `memoria/versoes/v1.0.3/aprendizados_usuario.jsonl`
67. `memoria/versoes/v1.0.3/config_memoria.json`
68. `memoria/versoes/v1.0.3/fase1_analise_planejamento.md`
69. `memoria/versoes/v1.0.3/fase2_roteiros_anamnese.md`
70. `memoria/versoes/v1.0.3/fase3_impressos_exames.md`
71. `memoria/versoes/v1.0.3/fase4_checklist_pep.md`
72. `memoria/versoes/v1.0.3/gabaritoestacoes.json`
73. `memoria/versoes/v1.0.3/metadata.json`
74. `memoria/versoes/v1.0.3/referencias_base.md`
75. `memoria/versoes/v1.0.4/aprendizados_usuario.jsonl`
76. `memoria/versoes/v1.0.4/config_memoria.json`
77. `memoria/versoes/v1.0.4/fase1_analise_planejamento.md`
78. `memoria/versoes/v1.0.4/fase2_roteiros_anamnese.md`
79. `memoria/versoes/v1.0.4/fase3_impressos_exames.md`
80. `memoria/versoes/v1.0.4/fase4_checklist_pep.md`
81. `memoria/versoes/v1.0.4/gabaritoestacoes.json`
82. `memoria/versoes/v1.0.4/metadata.json`
83. `memoria/versoes/v1.0.4/referencias_base.md`
84. `memoria/versoes/v1.0.5/aprendizados_usuario.jsonl`
85. `memoria/versoes/v1.0.5/config_memoria.json`
86. `memoria/versoes/v1.0.5/fase1_analise_planejamento.md`
87. `memoria/versoes/v1.0.5/fase2_roteiros_anamnese.md`
88. `memoria/versoes/v1.0.5/fase3_impressos_exames.md`
89. `memoria/versoes/v1.0.5/fase4_checklist_pep.md`
90. `memoria/versoes/v1.0.5/gabaritoestacoes.json`
91. `memoria/versoes/v1.0.5/metadata.json`
92. `memoria/versoes/v1.0.5/referencias_base.md`
93. `memoria/versoes/v1.0.6/aprendizados_usuario.jsonl`
94. `memoria/versoes/v1.0.6/config_memoria.json`
95. `memoria/versoes/v1.0.6/fase1_analise_planejamento.md`
96. `memoria/versoes/v1.0.6/fase2_roteiros_anamnese.md`
97. `memoria/versoes/v1.0.6/fase3_impressos_exames.md`
98. `memoria/versoes/v1.0.6/fase4_checklist_pep.md`
99. `memoria/versoes/v1.0.6/gabaritoestacoes.json`
100. `memoria/versoes/v1.0.6/metadata.json`
101. `memoria/versoes/v1.0.6/referencias_base.md`
102. `memoria/versoes/v1.0.7/aprendizados_usuario.jsonl`
103. `memoria/versoes/v1.0.7/config_memoria.json`
104. `memoria/versoes/v1.0.7/fase1_analise_planejamento.md`
105. `memoria/versoes/v1.0.7/fase2_roteiros_anamnese.md`
106. `memoria/versoes/v1.0.7/fase3_impressos_exames.md`
107. `memoria/versoes/v1.0.7/fase4_checklist_pep.md`
108. `memoria/versoes/v1.0.7/gabaritoestacoes.json`
109. `memoria/versoes/v1.0.7/metadata.json`
110. `memoria/versoes/v1.0.7/referencias_base.md`

### Provas INEP (57 arquivos)
111. `provas inep/2022.1/cancer_colorretal_1_inep_2022_1.json`
112. `provas inep/2022.1/desprendimento_prematuro_placenta_inep_2022_1.json`
113. `provas inep/2022.1/doenca_inflamatoria_pelvica_inep_2022_1.json`
114. `provas inep/2022.1/gota_inep_2022_1.json`
115. `provas inep/2022.1/leishmaniose_tegumentar_inep_2022_1.json`
116. `provas inep/2022.1/puericultura_lactente_vomitador_inep_2022_1.json`
117. `provas inep/2022.1/queimadura_inalacao_fumaca_inep_2022_1.json`
118. `provas inep/2022.1/retocolite_ulcerativa_inep_2022_1.json`
119. `provas inep/2022.1/tabagismo_inep_2022_1.json`
120. `provas inep/2022.2/colecistite_aguda_litiasica_inep_2022_2.json`
121. `provas inep/2022.2/febre_sem_sinais_localizatorios_inep_2022_2.json`
122. `provas inep/2022.2/herpes_zoster_inep_2022_2.json`
123. `provas inep/2022.2/hidrocele_inep_2022_2.json`
124. `provas inep/2022.2/medicina_legal_obstetricia_inep_2022_2.json`
125. `provas inep/2022.2/metodo_clinico_vacinacao_inep_2022_2.json`
126. `provas inep/2022.2/prostatite_aguda_hiperplasia_prostatica_inep_2022_2.json`
127. `provas inep/2022.2/sifilis_primaria_inep_2022_2.json`
128. `provas inep/2022.2/sindrome_wolff_parkinson_white_inep_2022_2.json`
129. `provas inep/2023.1/burnout.json`
130. `provas inep/2023.1/corpo estranho.json`
131. `provas inep/2023.1/desnutrição.json`
132. `provas inep/2023.1/diabetis.json`
133. `provas inep/2023.1/febre pos operatorio.json`
134. `provas inep/2023.1/hipertensao.json`
135. `provas inep/2023.1/papanicolau.json`
136. `provas inep/2023.1/puericultura.json`
137. `provas inep/2023.1/torção testicular.json`
138. `provas inep/2023.2/cancerdecolopapanicolau.json`
139. `provas inep/2023.2/examefisico obstetrico.json`
140. `provas inep/2023.2/EXAMEFISICOMAMAS.JSON`
141. `provas inep/2023.2/exame_clinico_mamas_inep_2023_2.json`
142. `provas inep/2023.2/obesidade.json`
143. `provas inep/2023.2/pancreatiteaguda.json`
144. `provas inep/2023.2/puericultura.json`
145. `provas inep/2023.2/sutura.json`
146. `provas inep/2023.2/urticaria.json`
147. `provas inep/2024.1/celuliteperiorbitaria.json`
148. `provas inep/2024.1/climaterio.json`
149. `provas inep/2024.1/criseasma.json`
150. `provas inep/2024.1/hipertensaoportaascite.json`
151. `provas inep/2024.1/insulinoterapia.json`
152. `provas inep/2024.1/pneumotorax.json`
153. `provas inep/2024.1/queimadura.json`
154. `provas inep/2024.1/sindromehelp.json`
155. `provas inep/2024.1/spike.json`
156. `provas inep/2024.1/tesenosepiloro.json`
157. `provas inep/2024.2/criptorquidia.json`
158. `provas inep/2024.2/dengue.json`
159. `provas inep/2024.2/dip.json`
160. `provas inep/2024.2/hipertensao.json`
161. `provas inep/2024.2/lagarta.json`
162. `provas inep/2024.2/oclusaoarterial.json`
163. `provas inep/2024.2/placentaprevia.json`
164. `provas inep/2024.2/revalida_2024_2_pep_definitivo.pdf`
165. `provas inep/2024.2/revalida_2024_2_pep_definitivo_RELATORIO_TRANSCRICAO.md`
166. `provas inep/2024.2/traumaabdomen.json`
167. `provas inep/2024.2/violenciasexual.json`
168. `provas inep/2025.1/denguegestante.json`
169. `provas inep/2025.1/espondilite.json`
170. `provas inep/2025.1/insonia.json`
171. `provas inep/2025.1/mioma.json`
172. `provas inep/2025.1/osteoporose.json`
173. `provas inep/2025.1/paralisia bell.json`
174. `provas inep/2025.1/ulceraperfurada.json`
175. `provas inep/2025.1/ureterolitiase.json`

### Scripts (2)
176. `scripts/debug_firebase_import.py`
177. `scripts/debug_google_import.py`

### Testes (13)
178. `tests/test_endpoint.ps1`
179. `tests/test_endpoints.py`
180. `tests/test_gemini_key.py`
181. `tests/test_key_embeddings.py`
182. `tests/test_key_http.py`
183. `tests/test_key_http_embed.py`
184. `tests/test_key_http_embed_v1.py`
185. `tests/test_rag.py`
186. `tests/test_rag_direct.py`
187. `tests/test_rag_generation.py`
188. `tests/test_sistema_hibrido.py`
189. `tests/test_web_search.py`
190. `tests/validate_embeddings.py`
191. `tests/validate_embeddings_extended.py`

### Testes Essenciais (2)
192. `tests_essenciais/check_env.py`
193. `tests_essenciais/list_gemini_models.py`

### Configuração (2)
194. `.vscode/settings.json`
195. `firebase.json`

---

## 🔄 Comando para Gerar Estrutura Completa

Para gerar automaticamente um arquivo com a estrutura completa dos arquivos e pastas do projeto, execute o seguinte comando PowerShell:

```powershell
# Comando para gerar estrutura completa do projeto
Get-ChildItem -Path "." -Recurse | Where-Object { -not ($_.FullName -match "node_modules|dist|\.git|__pycache__|\.venv") } | 
    Sort-Object { $_.PSIsContainer }, Name | 
    Format-Table FullName, Length, LastWriteTime -AutoSize | 
    Out-File -FilePath "estrutura_projeto_completa.txt" -Encoding UTF8

# Comando alternativo (mais detalhado)
Get-ChildItem -Path "." -Recurse | 
    Where-Object { -not ($_.FullName -match "node_modules|dist|\.git|__pycache__|\.venv") } | 
    Select-Object FullName, @{Name="Tipo"; Expression={ if ($_.PSIsContainer) { "Pasta" } else { "Arquivo" } }}, Length, LastWriteTime | 
    Sort-Object "Tipo", FullName | 
    Export-Csv -Path "estrutura_projeto_detalhada.csv" -NoTypeInformation -Encoding UTF8
```

Este comando irá:
1. Listar todos os arquivos e pastas recursivamente
2. Excluir diretórios de sistema e dependências
3. Ordenar por tipo (arquivos/pastas) e nome
4. Exportar para arquivo texto ou CSV
5. Incluir informações de tamanho e data modificação

---

## 📊 Estatísticas do Projeto

- **Total de arquivos**: 192
- **Linhas de código**: Estimado em 15.000+ (baseado na complexidade dos arquivos)
- **Tamanho total**: ~50MB (estimado)
- **Linguagens**: Python, JavaScript/TypeScript, JSON, Markdown
- **Framework principal**: FastAPI + Vue.js
- **Banco de dados**: Firestore (NoSQL)
- **IA**: Gemini API (Google)
- **Sistema de versionamento**: Git + versionamento interno (v1.0.0 a v1.0.7)

---

## 🔧 Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web Python
- **Python 3.8+**: Linguagem principal
- **Firestore**: Banco de dados NoSQL
- **Gemini API**: Inteligência artificial
- **PyMuPDF**: Extração de PDFs
- **numpy**: Computação numérica
- **google-generativeai**: API Gemini

### Frontend
- **Vue 3**: Framework JavaScript
- **Vuetify 3**: Componentes UI
- **Axios**: Cliente HTTP

### Desenvolvimento
- **Git**: Controle de versão
- **Docker**: Containerização
- **PowerShell**: Ambiente Windows
- **VS Code**: IDE principal

---

## 📞 Informações Adicionais

Para mais informações sobre o sistema, consulte:
- Documentação principal: [`gerador.md`](gerador.md)
- Documentação atualizada: [`documentacao_sistema_atualizada.md`](documentacao_sistema_atualizada.md)
- Endpoints API: [`api_docs/endpoints.md`](api_docs/endpoints.md)
- Sistema de memória: [`memoria/config_memoria.json`](memoria/config_memoria.json)

---

*Estrutura gerada automaticamente em 26/08/2025*
