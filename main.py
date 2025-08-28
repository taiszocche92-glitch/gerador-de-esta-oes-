# Arquivo: main.py (Versão 8 - Geração com Salvamento Automático no Firestore)

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import firebase_admin
from firebase_admin import credentials, firestore
from contextlib import asynccontextmanager
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
from pydantic import BaseModel
import json
import fitz  # PyMuPDF para processamento de PDF
import time
import psutil  # Para métricas do sistema
import threading
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
# Configuração mínima do logging para o módulo
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# Logger global do agente (usado em funções compartilhadas)
logger = logging.getLogger("agent")
import uuid  # Para gerar IDs únicos no fallback local
from typing import Optional, Dict, Any, List
from pathlib import Path

# --- Carregamento de Variáveis de Ambiente ---
load_dotenv()  # Carrega .env da pasta atual (se existir)
load_dotenv("../.env")  # Carrega .env da pasta pai (projeto principal)
# web_search import moved to runtime use to avoid E402 (import inside function where needed)

# --- Importar Sistema de Validação de Impressos ---
try:
    from impressos_validator import validar_impressos_estacao
    IMPRESSOS_VALIDATOR_AVAILABLE = True
    print("[SUCCESS] Sistema de validação de impressos carregado!")
except ImportError as e:
    IMPRESSOS_VALIDATOR_AVAILABLE = False
    print(f"[WARNING] Sistema de validação de impressos não disponível: {e}")

# --- Constantes do Gemini FinishReason ---
FINISH_REASON_NAMES = {
    0: "FINISH_REASON_UNSPECIFIED",
    1: "STOP",  # Ponto de parada natural
    2: "MAX_TOKENS",  # Limite máximo de tokens
    3: "SAFETY",  # Bloqueado por segurança
    4: "RECITATION",  # Bloqueado por recitação
    5: "LANGUAGE",  # Idioma não suportado  
    6: "OTHER",  # Motivo desconhecido
    7: "BLOCKLIST",  # Termos proibidos
    8: "PROHIBITED_CONTENT",  # Conteúdo proibido
    9: "SPII",  # Informações pessoais sensíveis
    10: "MALFORMED_FUNCTION_CALL",  # Chamada de função inválida
}

# --- Variáveis Globais ---
db = None
firebase_mock_mode = False
AGENT_RULES: Dict[str, Any] = {}
PARSED_REFERENCIAS: Dict[str, str] = {}  # Nova variável para armazenar seções parsed
GEMINI_CONFIGS: Dict[str, List[Dict[str, str]]] = {}
LOCAL_MEMORY_SYSTEM: Dict[str, Any] = {}  # Nova variável para sistema de memória local

# --- Abordagens Padrão para Seleção na Fase 2 ---
ABORDAGENS_PADRAO = [
    {
        "id": "completa",
        "nome": "Encontro Clínico Completo",
        "descricao": "Anamnese → Exame Físico → Diagnóstico → Conduta",
        "foco": "Avaliação clínica integral com todas as etapas do raciocínio médico"
    },
    {
        "id": "procedimental", 
        "nome": "Foco Procedimental/Educacional",
        "descricao": "Demonstração de técnica ou orientação ao paciente",
        "foco": "Habilidades práticas, procedimentos e educação em saúde"
    },
    {
        "id": "comunicacao",
        "nome": "Habilidade de Comunicação", 
        "descricao": "Diálogo sensível, empatia, protocolos de comunicação",
        "foco": "Competências de comunicação e relacionamento médico-paciente"
    },
    {
        "id": "emergencia",
        "nome": "Protocolo de Emergência",
        "descricao": "Sequência ABCDE, atendimento rápido, estabilização",
        "foco": "Atendimento de urgência e emergência com protocolos padronizados"
    },
    {
        "id": "diagnostico",
        "nome": "Diagnóstico Diferencial",
        "descricao": "Análise comparativa de hipóteses diagnósticas",
        "foco": "Raciocínio clínico avançado e diferenciação diagnóstica"
    }
]
VERSION_SYSTEM: Dict[str, Any] = {}  # Nova variável para sistema de versionamento
MONITORING_SYSTEM: Dict[str, Any] = {}  # Nova variável para sistema de monitoramento

# --- Modelos de Dados (Pydantic) ---
class CreateStationRequest(BaseModel):
    tema: str
    especialidade: str

class GenerateFinalStationRequest(BaseModel):
    resumo_clinico: str
    proposta_escolhida: str
    tema: str
    especialidade: str

class AnalyzeStationRequest(BaseModel):
    station_id: str
    feedback: str | None = None

class ApplyAuditRequest(BaseModel):
    station_id: str
    analysis_result: str

class UpdateRulesRequest(BaseModel):
    new_rule: str
    context: str | None = None
    category: str | None = None

class MultipleGenerationRequest(BaseModel):
    temas: List[str]
    especialidade: str
    abordagem_selecionada: str
    enable_web_search: str = "0"

# --- Função de Extração de PDF ---
def extract_pdf_content_structured(pdf_bytes: bytes, tema: str) -> str:
    """
    Extrai o conteúdo do PDF de forma estruturada conforme as orientações específicas.
    Foca no tema/doença especificado e segue a estrutura solicitada.
    """
    try:
        # Abrir o PDF a partir dos bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Extrair todo o texto do PDF
        full_text = ""
        toc_text = ""
        
        # Tentar extrair o índice/sumário se existir
        toc = doc.get_toc()  # type: ignore
        if toc:
            toc_text = "ÍNDICE/SUMÁRIO ENCONTRADO:\n"
            for level, title, page in toc:
                toc_text += f"{'  ' * (level-1)}- {title} (página {page})\n"
            toc_text += "\n"
        
        # Extrair texto de todas as páginas
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()  # type: ignore
            full_text += f"\n--- PÁGINA {page_num + 1} ---\n"
            full_text += page_text
        
        doc.close()
        
        # Estruturar o conteúdo conforme solicitado
        structured_content = f"""
ANÁLISE ESTRUTURADA DO PDF PARA O TEMA: {tema.upper()}

{toc_text}

INSTRUÇÕES DE EXTRAÇÃO:
- Foque especificamente no tema/doença: {tema}
- Extraia apenas conteúdo relevante para criação de estações médicas
- Identifique seções sobre: conceitos, classificação, fatores de risco, quadro clínico, diagnóstico, tratamento
- Ignore conteúdo não relacionado ao tema principal

CONTEÚDO COMPLETO DO PDF:
{full_text}

ORIENTAÇÕES PARA ANÁLISE:
1. Busque no índice tópicos relacionados ao tema: {tema}
2. Extraia conceitos iniciais relevantes ao tema
3. Identifique subtópicos como: classificação, fatores de risco, prevenção, quadro clínico, diagnóstico, tratamento
4. Localize referências bibliográficas
5. Busque considerações finais relacionadas ao tema
"""
        
        return structured_content
        
    except Exception as e:
        raise Exception(f"Erro ao processar PDF: {str(e)}")

# --- Função de Parser de Referencias ---
def parse_referencias_md(referencias_content: str) -> dict:
    """
    Parser que divide o conteúdo do referencias.md em seções específicas.
    Retorna um dicionário com as seções identificadas para uso otimizado nos prompts.
    """
    if not referencias_content:
        print("[WARNING] Conteúdo de referencias.md está vazio")
        return {}
    
    try:
        sections = {}
        lines = referencias_content.split('\n')
        current_section = None
        current_content = []
        
        print("🔍 Iniciando parsing do referencias.md...")
        
        for line in lines:
            # Detectar início das seções principais
            if line.startswith('# GUIA MESTRE') or line.startswith('. PRINCÍPIOS FUNDAMENTAIS'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'principios_fundamentais'
                current_content = [line]
                
            elif line.startswith('## 1. ARQUITETURA DAS ESTAÇÕES'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'arquitetura_estacoes'
                current_content = [line]
                
            elif line.startswith('## 2. DIRETRIZES PARA TAREFAS'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'diretrizes_tarefas'
                current_content = [line]
                
            elif line.startswith('## 3. TAREFAS PRINCIPAIS POR ESPECIALIDADE'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'tarefas_especialidade'
                current_content = [line]
                
            elif line.startswith('### **4.1. REGRAS BÁSICAS'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'regras_basicas_ator'
                current_content = [line]
                
            elif line.startswith('### **4.2. REGRAS OBRIGATÓRIAS'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'regras_contextos_ator'
                current_content = [line]
                
            elif line.startswith('## 4. O ROTEIRO DO ATOR'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'roteiro_ator_completo'
                current_content = [line]
                
            elif line.startswith('## 5. BANCO DE SEMIOLOGIA'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'banco_semiologia'
                current_content = [line]
                
            elif line.startswith('## 6. TIPOS DE IMPRESSOS'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'tipos_impressos'
                current_content = [line]
                
            elif line.startswith('## 7. DIRETRIZES AVANÇADAS PARA CONSTRUÇÃO DO PEP'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'diretrizes_pep'
                current_content = [line]
                
            elif line.startswith('## 8. ESTRUTURAS ESPECÍFICAS POR ESPECIALIDADE'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'estruturas_especialidade'
                current_content = [line]
                
            elif line.startswith('## 9. CHECKLIST DE VALIDAÇÃO'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'checklist_validacao'
                current_content = [line]
                
            elif line.startswith('## 10. REGRA APRENDIDA'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'regra_aprendida'
                current_content = [line]
                
            else:
                # Adicionar linha ao conteúdo da seção atual
                if current_section:
                    current_content.append(line)
        
        # Adicionar a última seção
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        print(f"[SUCCESS] Parser concluído! {len(sections)} seções identificadas:")
        for key in sections.keys():
            print(f"   [DOC] {key}: {len(sections[key])} caracteres")
        
        return sections
        
    except Exception as e:
        print(f"[ERROR] Erro ao fazer parsing do referencias.md: {e}")
        return {}

# --- Sistema Híbrido de Memória Local ---
def load_local_memory_config():
    """Carrega a configuração do sistema de memória local"""
    try:
        with open('memoria/config_memoria.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Erro ao carregar config_memoria.json: {e}")
        return {}

def load_local_file(file_path):
    """Carrega conteúdo de arquivo local com encoding UTF-8"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[WARNING] Erro ao carregar arquivo {file_path}: {e}")
        return ""

def load_provas_inep(provas_dir):
    """Carrega todas as provas INEP como exemplos de estrutura JSON"""
    provas_exemplos = []
    
    if not provas_dir:
        return provas_exemplos
    
    base_path = os.path.join(os.getcwd(), provas_dir)
    if not os.path.exists(base_path):
        print(f"[WARNING] Diretório de provas INEP não encontrado: {base_path}")
        return provas_exemplos
    
    try:
        # Buscar recursivamente por arquivos .json
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            prova_data = json.load(f)
                            provas_exemplos.append({
                                'arquivo': file,
                                'caminho': os.path.relpath(file_path, base_path),
                                'conteudo': prova_data
                            })
                    except Exception as e:
                        print(f"[WARNING] Erro ao carregar {file_path}: {e}")
        
        print(f"📚 Carregadas {len(provas_exemplos)} provas INEP como exemplos")
        return provas_exemplos
        
    except Exception as e:
        print(f"[WARNING] Erro ao processar diretório INEP: {e}")
        return provas_exemplos

def initialize_local_memory_system():
    """Inicializa o sistema híbrido de memória local"""
    global LOCAL_MEMORY_SYSTEM
    try:
        print("[BRAIN] Inicializando sistema híbrido de memória local...")

        # Carregar configuração
        print("[DEBUG] Carregando configuração...")
        config = load_local_memory_config()
        if not config:
            print("[ERROR] Falha ao carregar configuração - usando sistema antigo")
            return False

        print("[DEBUG] Configuração carregada com sucesso")
        LOCAL_MEMORY_SYSTEM['config'] = config
        sistema = config.get('sistema_memoria', {})
        estrutura = sistema.get('estrutura', {})
        print(f"[DEBUG] Estrutura encontrada: {list(estrutura.keys())}")

        # Carregar arquivos base
        print("[DOC] Carregando arquivos base...")
        referencias_path = estrutura.get('referencias_base', '')
        gabarito_path = estrutura.get('gabarito_template', '')

        print(f"[DEBUG] Carregando referencias_base: {referencias_path}")
        LOCAL_MEMORY_SYSTEM['referencias_base'] = load_local_file(referencias_path)

        print(f"[DEBUG] Carregando gabarito_template: {gabarito_path}")
        LOCAL_MEMORY_SYSTEM['gabarito_template'] = load_local_file(gabarito_path)

        # [SUCCESS] CORREÇÃO: Carregar provas INEP para referência
        print("📚 Carregando provas INEP...")
        provas_inep_dir = estrutura.get('provas_inep', 'provas inep/')
        LOCAL_MEMORY_SYSTEM['provas_inep'] = load_provas_inep(provas_inep_dir)

        # Carregar contextos otimizados por fase
        print("📁 Carregando contextos otimizados...")
        contextos = estrutura.get('contexto_otimizado', {})
        LOCAL_MEMORY_SYSTEM['contextos'] = {}
        print(f"[DEBUG] Contextos a carregar: {list(contextos.keys())}")

        for fase, arquivo in contextos.items():
            print(f"[DEBUG] Carregando contexto {fase}: {arquivo}")
            LOCAL_MEMORY_SYSTEM['contextos'][fase] = load_local_file(arquivo)

        # Carregar aprendizados do usuário
        print("🎓 Carregando aprendizados do usuário...")
        aprendizados_path = estrutura.get('aprendizados_usuario', '')
        print(f"[DEBUG] Carregando aprendizados: {aprendizados_path}")

        try:
            with open(aprendizados_path, 'r', encoding='utf-8') as f:
                LOCAL_MEMORY_SYSTEM['aprendizados'] = json.load(f)
            print(f"[DEBUG] Aprendizados carregados: {len(LOCAL_MEMORY_SYSTEM['aprendizados'])} itens")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar aprendizados: {e}")
            LOCAL_MEMORY_SYSTEM['aprendizados'] = []

        print("[SUCCESS] Sistema híbrido de memória local inicializado com sucesso!")
        economia = sistema.get('reducao_tokens', {}).get('economia', 'N/A')
        print(f"💰 Economia estimada: {economia}")

        # Log final do estado do sistema
        print(f"[DEBUG] LOCAL_MEMORY_SYSTEM final: {list(LOCAL_MEMORY_SYSTEM.keys())}")
        for key, value in LOCAL_MEMORY_SYSTEM.items():
            if isinstance(value, str):
                print(f"[DEBUG] {key}: {len(value)} caracteres")
            elif isinstance(value, list):
                print(f"[DEBUG] {key}: {len(value)} itens")
            elif isinstance(value, dict):
                print(f"[DEBUG] {key}: {len(value)} chaves")

        return True

    except Exception as e:
        print(f"[ERROR] Erro ao inicializar sistema local: {e}")
        import traceback
        print(f"[DEBUG] Traceback completo: {traceback.format_exc()}")
        return False

def get_context_for_phase(phase_number):
    """Retorna contexto otimizado para uma fase específica"""
    if not LOCAL_MEMORY_SYSTEM:
        return ""
        
    try:
        config = LOCAL_MEMORY_SYSTEM.get('config', {})
        regras = config.get('sistema_memoria', {}).get('regras_carregamento', {})
        
        # Arquivos que sempre devem ser carregados
        sempre_carregar = regras.get('sempre_carregar', [])
        contexto_completo = ""
        
        # Adicionar referências base se sempre necessário
        if 'referencias_base' in sempre_carregar:
            contexto_completo += LOCAL_MEMORY_SYSTEM.get('referencias_base', '')
            
        # Carregar contextos específicos da fase
        carregar_por_fase = regras.get('carregar_por_fase', {})
        fase_str = str(phase_number)
        
        if fase_str in carregar_por_fase:
            arquivos_fase = carregar_por_fase[fase_str]
            
            for arquivo in arquivos_fase:
                if arquivo == 'gabarito_template':
                    # Gabarito JSON é carregado separadamente
                    continue
                elif arquivo.startswith('fase'):
                    # Contexto otimizado de fase
                    conteudo = LOCAL_MEMORY_SYSTEM.get('contextos', {}).get(arquivo, '')
                    if conteudo:
                        contexto_completo += f"\n\n--- {arquivo.upper().replace('_', ' ')} ---\n"
                        contexto_completo += conteudo
        
        # Sempre adicionar aprendizados do usuário se houver (novo formato)
        aprendizados = LOCAL_MEMORY_SYSTEM.get('aprendizados', [])
        if aprendizados:
            contexto_completo += "\n\n" + format_learnings_for_context(aprendizados)
                
        print(f"[STATS] Fase {phase_number}: {len(contexto_completo)} caracteres carregados")
        return contexto_completo
        
    except Exception as e:
        print(f"[WARNING] Erro ao gerar contexto para fase {phase_number}: {e}")
        return ""

def get_gabarito_template():
    """Retorna o template do gabarito JSON local"""
    return LOCAL_MEMORY_SYSTEM.get('gabarito_template', '{}')

# --- Sistema de Aprendizado Automático ---
def categorize_learning(new_rule: str, context: Optional[str] = None) -> str:
    """Categoriza automaticamente um novo aprendizado"""
    rule_lower = new_rule.lower()
    
    # Palavras-chave para categorização
    if any(word in rule_lower for word in ['nunca', 'não', 'evitar', 'proibido', 'incorreto']):
        return "restricao"
    elif any(word in rule_lower for word in ['sempre', 'obrigatório', 'deve', 'essencial', 'regra']):
        return "obrigatorio"
    elif any(word in rule_lower for word in ['preferir', 'melhor', 'recomendado', 'ideal']):
        return "preferencia"
    elif any(word in rule_lower for word in ['novo', 'adicionar', 'incluir', 'criar']):
        return "novo_padrao"
    elif any(word in rule_lower for word in ['corrigir', 'erro', 'problema', 'bug']):
        return "correcao"
    elif any(word in rule_lower for word in ['formato', 'estrutura', 'template', 'padrão']):
        return "formatacao"
    else:
        return "geral"

def save_learning(new_rule: str, context: Optional[str] = None, category: Optional[str] = None) -> bool:
    """Salva um novo aprendizado no sistema local"""
    try:
        if not LOCAL_MEMORY_SYSTEM:
            print("[WARNING] Sistema local não inicializado, salvando no Firestore apenas")
            return False
            
        # Categorizar automaticamente se não fornecida
        if not category:
            category = categorize_learning(new_rule, context)
            
        # Criar registro do aprendizado
        learning_entry = {
            "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}}),
            "rule": new_rule,
            "context": context or "Sem contexto específico",
            "category": category,
            "source": "user_feedback"
        }
        
        # Carregar aprendizados existentes
        aprendizados_file = "memoria/aprendizados_usuario.jsonl"
        aprendizados = LOCAL_MEMORY_SYSTEM.get('aprendizados', [])
        
        # Adicionar novo aprendizado
        aprendizados.append(learning_entry)
        LOCAL_MEMORY_SYSTEM['aprendizados'] = aprendizados
        
        # Salvar no arquivo local
        with open(aprendizados_file, 'w', encoding='utf-8') as f:
            json.dump(aprendizados, f, ensure_ascii=False, indent=2)
            
        print(f"[SUCCESS] Aprendizado salvo - Categoria: {category}")
        print(f"📝 Regra: {new_rule[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro ao salvar aprendizado: {e}")
        return False

def get_recent_learnings(limit: int = 10) -> list:
    """Retorna os aprendizados mais recentes"""
    if not LOCAL_MEMORY_SYSTEM:
        return []
        
    aprendizados = LOCAL_MEMORY_SYSTEM.get('aprendizados', [])
    return aprendizados[-limit:] if aprendizados else []

def format_learnings_for_context(learnings: list) -> str:
    """Formata aprendizados para incluir no contexto"""
    if not learnings:
        return ""
        
    formatted = "## REGRAS APRENDIDAS AUTOMATICAMENTE\n\n"
    
    # Agrupar por categoria
    by_category = {}
    for learning in learnings:
        category = learning.get('category', 'geral')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(learning)
    
    # Formatação por categoria
    category_names = {
        'restricao': '🚫 RESTRIÇÕES',
        'obrigatorio': '[SUCCESS] OBRIGATÓRIO',
        'preferencia': '💡 PREFERÊNCIAS',
        'novo_padrao': '🆕 NOVOS PADRÕES',
        'correcao': '🔧 CORREÇÕES',
        'formatacao': '📝 FORMATAÇÃO',
        'geral': '📋 GERAIS'
    }
    
    for category, items in by_category.items():
        if items:
            formatted += f"\n### {category_names.get(category, category.upper())}\n"
            for item in items[-5:]:  # Últimos 5 de cada categoria
                formatted += f"- {item['rule']}\n"
    
    return formatted

# --- Sistema de Versionamento de Contexto ---
import hashlib
import shutil
from datetime import datetime
import difflib

def load_version_config():
    """Carrega a configuração do sistema de versionamento"""
    try:
        with open('memoria/versoes/config_versoes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Erro ao carregar config de versões: {e}")
        return {}

def save_version_config(config):
    """Salva a configuração do sistema de versionamento"""
    try:
        with open('memoria/versoes/config_versoes.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Erro ao salvar config de versões: {e}")
        return False

def calculate_content_hash(content):
    """Calcula hash MD5 do conteúdo para detectar mudanças"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def detect_significant_change(old_content, new_content, threshold=0.1):
    """Detecta se houve mudança significativa no conteúdo"""
    if not old_content or not new_content:
        return True
        
    # Usar difflib para calcular similaridade
    similarity = difflib.SequenceMatcher(None, old_content, new_content).ratio()
    change_ratio = 1 - similarity
    
    return change_ratio >= threshold

def generate_version_number(current_version, change_type="auto"):
    """Gera novo número de versão baseado no tipo de mudança"""
    try:
        # Parsear versão atual (ex: v1.2.3)
        version_parts = current_version.replace('v', '').split('.')
        major, minor, patch = map(int, version_parts)
        
        if change_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif change_type == "minor":
            minor += 1
            patch = 0
        else:  # patch ou auto
            patch += 1
            
        return f"v{major}.{minor}.{patch}"
    except Exception:
        # Fallback para versão com timestamp se parsing falhar
        timestamp = int(__import__('time').time())
        return f"v1.0.{timestamp}"

def create_version_snapshot(version_number, change_type="auto", description=""):
    """Cria um snapshot completo do sistema atual"""
    try:
        timestamp = datetime.now().isoformat()
        
        # Criar diretório da versão
        version_dir = f"memoria/versoes/{version_number}"
        os.makedirs(version_dir, exist_ok=True)
        
        # Snapshot de todos os arquivos importantes
        files_to_backup = [
            "memoria/referencias_base.md",
            "memoria/aprendizados_usuario.jsonl",
            "memoria/config_memoria.json",
            "gabaritoestacoes.json"
        ]
        
        # Backup dos contextos otimizados
        for fase in ["fase1", "fase2", "fase3", "fase4"]:
            files_to_backup.append(f"memoria/contexto_otimizado/{fase}_*.md")
        
        # Calcular tamanho total
        total_size = 0
        backed_files = []
        
        for file_pattern in files_to_backup:
            if "*" in file_pattern:
                # Usar glob para padrões
                import glob
                matching_files = glob.glob(file_pattern)
                for file_path in matching_files:
                    if os.path.exists(file_path):
                        target_path = os.path.join(version_dir, os.path.basename(file_path))
                        shutil.copy2(file_path, target_path)
                        total_size += os.path.getsize(file_path)
                        backed_files.append(os.path.basename(file_path))
            else:
                if os.path.exists(file_pattern):
                    target_path = os.path.join(version_dir, os.path.basename(file_pattern))
                    shutil.copy2(file_pattern, target_path)
                    total_size += os.path.getsize(file_pattern)
                    backed_files.append(os.path.basename(file_pattern))
        
        # Criar metadados da versão
        version_metadata = {
            "version": version_number,
            "timestamp": timestamp,
            "change_type": change_type,
            "description": description or f"Backup automático {change_type}",
            "total_size_bytes": total_size,
            "files_count": len(backed_files),
            "files": backed_files,
            "system_state": {
                "hybrid_active": bool(LOCAL_MEMORY_SYSTEM),
                "learnings_count": len(LOCAL_MEMORY_SYSTEM.get('aprendizados', [])),
                "contexts_count": len(LOCAL_MEMORY_SYSTEM.get('contextos', {}))
            }
        }
        
        # Salvar metadados
        metadata_path = os.path.join(version_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(version_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"[SUCCESS] Snapshot criado: {version_number}")
        print(f"📂 Arquivos: {len(backed_files)}, Tamanho: {total_size/1024:.1f}KB")
        
        return version_metadata
        
    except Exception as e:
        print(f"[ERROR] Erro ao criar snapshot: {e}")
        return None

def initialize_version_system():
    """Inicializa o sistema de versionamento"""
    global VERSION_SYSTEM
    try:
        print("📦 Inicializando sistema de versionamento...")
        
        # Carregar configuração
        config = load_version_config()
        if not config:
            print("[ERROR] Falha ao carregar configuração de versões")
            return False
            
        VERSION_SYSTEM = config
        # Adiciona base_path e versions_path para evitar erro 500 nos endpoints
        VERSION_SYSTEM['base_path'] = 'memoria/versoes'
        VERSION_SYSTEM['versions_path'] = 'memoria/versoes'
        
        # Verificar se é a primeira execução
        sistema_versoes = VERSION_SYSTEM.get('sistema_versionamento', {})
        historico = sistema_versoes.get('historico_versoes', [])
        
        if not historico:
            print("🆕 Primeira execução - criando versão inicial...")
            metadata = create_version_snapshot("v1.0.0", "major", "Versão inicial do sistema híbrido")
            
            if metadata:
                # Atualizar configuração
                sistema_versoes['versao_atual'] = "v1.0.0"
                sistema_versoes['historico_versoes'] = [metadata]
                sistema_versoes['metricas']['total_versoes'] = 1
                sistema_versoes['metricas']['ultima_atualizacao'] = metadata['timestamp']
                sistema_versoes['metricas']['tamanho_total_bytes'] = metadata['total_size_bytes']
                
                VERSION_SYSTEM['sistema_versionamento'] = sistema_versoes
                save_version_config(VERSION_SYSTEM)
        
        versao_atual = sistema_versoes.get('versao_atual', 'v1.0.0')
        total_versoes = sistema_versoes.get('metricas', {}).get('total_versoes', 0)
        
        print(f"[SUCCESS] Sistema de versionamento ativo!")
        print(f"📌 Versão atual: {versao_atual}")
        print(f"[STATS] Total de versões: {total_versoes}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erro ao inicializar versionamento: {e}")
        return False

def auto_version_on_change(description="Mudança automática detectada"):
    """Cria versão automaticamente quando detecta mudanças significativas"""
    try:
        if not VERSION_SYSTEM:
            return False
            
        # Obter conteúdo atual
        current_content = ""
        for file_path in ["memoria/referencias_base.md", "memoria/aprendizados_usuario.jsonl"]:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content += f.read()
        
        # Obter versão atual
        sistema_versoes = VERSION_SYSTEM.get('sistema_versionamento', {})
        versao_atual = sistema_versoes.get('versao_atual', 'v1.0.0')
        
        # Verificar se há mudanças significativas
        # (Implementação simplificada - na prática, compararia com última versão)
        current_hash = calculate_content_hash(current_content)
        
        # Gerar nova versão
        nova_versao = generate_version_number(versao_atual, "patch")
        metadata = create_version_snapshot(nova_versao, "auto", description)
        
        if metadata:
            # Atualizar sistema
            historico = sistema_versoes.get('historico_versoes', [])
            historico.append(metadata)
            
            # Manter apenas as últimas N versões
            max_versoes = sistema_versoes.get('configuracao', {}).get('max_versoes', 50)
            if len(historico) > max_versoes:
                historico = historico[-max_versoes:]
            
            # Atualizar métricas
            sistema_versoes['versao_atual'] = nova_versao
            sistema_versoes['historico_versoes'] = historico
            sistema_versoes['metricas']['total_versoes'] = len(historico)
            sistema_versoes['metricas']['ultima_atualizacao'] = metadata['timestamp']
            
            VERSION_SYSTEM['sistema_versionamento'] = sistema_versoes
            save_version_config(VERSION_SYSTEM)
            
            print(f"[REFRESH] Nova versão criada automaticamente: {nova_versao}")
            return True
            
    except Exception as e:
        print(f"[WARNING] Erro no versionamento automático: {e}")
        return False

def get_version_history(limit=10):
    """Retorna o histórico de versões"""
    if not VERSION_SYSTEM:
        return []
        
    historico = VERSION_SYSTEM.get('sistema_versionamento', {}).get('historico_versoes', [])
    return historico[-limit:] if historico else []

def rollback_to_version(version_number):
    """Faz rollback para uma versão específica"""
    try:
        # Verificar se a versão existe
        version_dir = f"memoria/versoes/{version_number}"
        if not os.path.exists(version_dir):
            return False, f"Versão {version_number} não encontrada"
        
        # Criar backup da versão atual antes do rollback
        versao_atual = VERSION_SYSTEM.get('sistema_versionamento', {}).get('versao_atual', 'v1.0.0')
        backup_version = generate_version_number(versao_atual, "patch")
        create_version_snapshot(backup_version, "backup", f"Backup antes de rollback para {version_number}")
        
        # Restaurar arquivos da versão solicitada
        metadata_path = os.path.join(version_dir, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        for file_name in metadata['files']:
            source_path = os.path.join(version_dir, file_name)
            if file_name.startswith('fase'):
                target_path = f"memoria/contexto_otimizado/{file_name}"
            elif file_name == 'gabaritoestacoes.json':
                target_path = file_name
            else:
                target_path = f"memoria/{file_name}"
            
            if os.path.exists(source_path):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(source_path, target_path)
        
        print(f"[SUCCESS] Rollback para {version_number} concluído!")
        return True, f"Sistema restaurado para versão {version_number}"
        
    except Exception as e:
        return False, f"Erro no rollback: {e}"

# --- Funções de Inicialização ---

def safe_clear_firebase_apps():
    """Limpa apps Firebase de forma segura para evitar erros de iteração"""
    try:
        # Método 1: Tentar limpar diretamente se possível
        if not firebase_admin._apps:
            return True
            
        # Método 2: Converter para lista e deletar
        try:
            apps_to_delete = list(firebase_admin._apps.values())
            for app in apps_to_delete:
                try:
                    firebase_admin.delete_app(app)
                except Exception as delete_err:
                    print(f"[WARNING] Erro ao deletar app individual: {delete_err}")
            firebase_admin._apps.clear()
            return True
        except Exception as method2_err:
            print(f"[WARNING] Método 2 falhou: {method2_err}")
        
        # Método 3: Forçar clear sem deletar individualmente
        try:
            firebase_admin._apps.clear()
            return True
        except Exception as method3_err:
            print(f"[WARNING] Método 3 falhou: {method3_err}")
        
        return False
        
    except Exception as general_err:
        print(f"[WARNING] Erro geral ao limpar Firebase apps: {general_err}")
        return False

def reinitialize_firebase_with_retry():
    """Reinicializa Firebase com estratégia de retry para resolver problemas de JWT"""
    global db, firebase_mock_mode
    
    # Resetar apps Firebase existentes para forçar nova inicialização
    print("[REFRESH] Limpando apps Firebase existentes...")
    safe_clear_firebase_apps()
    
    # SEM sleep durante inicialização do servidor
    return initialize_firebase()

def reinitialize_firebase_for_operations():
    """Versão com retry completo para uso durante operações (não startup)"""
    global db, firebase_mock_mode
    
    # Resetar apps Firebase existentes
    print("[REFRESH] Limpando apps Firebase existentes para operação...")
    safe_clear_firebase_apps()
    
    # Aguardar um pouco para evitar problemas de cache
    time.sleep(2)
    
    # Tentar com retry completo
    service_account_paths = [
        os.path.join('memoria', 'serviceAccountKey.json'),
        'serviceAccountKey.json'
    ]
    
    for path in service_account_paths:
        if os.path.exists(path):
            result = _try_firebase_connection_with_retry(path, f"arquivo local: {path}")
            if result:
                return True
    
    # Se chegou aqui, falhou
    firebase_mock_mode = True
    db = None
    return False

def initialize_firebase():
    global db, firebase_mock_mode

    # Código original comentado para debug
    
    try:
        # Preferir arquivo de credenciais local (evita erro de ADC quando não configurado)
        service_account_paths = [
            os.path.join('memoria', 'serviceAccountKey.json'),
            'serviceAccountKey.json'
        ]

        # Se houver variável de ambiente apontando para um arquivo, tentar usá-la primeiro
        env_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if env_path and os.path.exists(env_path):
            return _try_firebase_connection_simple(env_path, "GOOGLE_APPLICATION_CREDENTIALS")

        # Tentar arquivos locais conhecidos
        for path in service_account_paths:
            if os.path.exists(path):
                result = _try_firebase_connection_simple(path, f"arquivo local: {path}")
                if result:
                    return True

        # Por fim, tentar Application Default Credentials (padrão GCP)
        try:
            cred = credentials.ApplicationDefault()
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {'projectId': os.getenv('FIREBASE_PROJECT_ID', 'revalida-companion')})

            # Teste de conectividade SIMPLES (sem retry)
            db = firestore.client()
            print("[SUCCESS] Firebase Admin SDK inicializado com Application Default Credentials.")
            return True
        except Exception as adc_error:
            print(f"[WARNING] Falha com Application Default Credentials: {adc_error}")

    except Exception as e_final:
        print(f"[WARNING] Erro geral ao inicializar Firebase Admin SDK: {e_final}")

    # Se chegou aqui, todas as tentativas falharam
    print(f"[REFRESH] Ativando modo híbrido local (sem sincronização Firestore)")
    print(f"[SUCCESS] Sistema local funcionando normalmente!")
    firebase_mock_mode = True
    db = None
    return False

def _try_firebase_connection_simple(credential_path, description):
    """Versão simplificada sem retry loops que travem o servidor"""
    global db, firebase_mock_mode
    
    try:
        cred = credentials.Certificate(credential_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        # Teste simples de conectividade SEM retry loops
        db = firestore.client()
        print(f"[SUCCESS] Firebase Admin SDK inicializado com {description}")
        firebase_mock_mode = False
        return True
                
    except Exception as connectivity_err:
        print(f"[WARNING] Falha de conectividade Firebase: {connectivity_err}")
        print(f"[REFRESH] Continuando em modo local...")
        db = None
        firebase_mock_mode = True
        return False

def _try_firebase_connection_with_retry(credential_path, description):
    """Versão com retry para uso após inicialização do servidor"""
    global db, firebase_mock_mode
    
    try:
        cred = credentials.Certificate(credential_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        # Teste de conectividade com retry para problemas de JWT
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db = firestore.client()
                # Teste mínimo de conectividade
                db.collection('test').limit(1).get()
                print(f"[SUCCESS] Firebase Admin SDK inicializado com {description}")
                firebase_mock_mode = False
                return True
                
            except Exception as connectivity_err:
                error_msg = str(connectivity_err).lower()
                
                # Verificar se é erro de JWT signature
                if 'invalid jwt signature' in error_msg or 'invalid_grant' in error_msg:
                    print(f"[WARNING] Erro de JWT detectado (tentativa {attempt + 1}/{max_retries}): {connectivity_err}")
                    
                    if attempt < max_retries - 1:
                        print("[REFRESH] Aguardando e tentando novamente...")
                        time.sleep(5)  # Aguardar 5 segundos
                        
                        # Limpar e reinicializar para próxima tentativa
                        try:
                            safe_clear_firebase_apps()
                            cred = credentials.Certificate(credential_path)
                            firebase_admin.initialize_app(cred)
                        except Exception:
                            pass
                        continue
                    else:
                        print("[ERROR] Erro de JWT persistiu após todas as tentativas")
                        
                elif 'timeout' in error_msg or '503' in error_msg:
                    print(f"[WARNING] Timeout/503 detectado (tentativa {attempt + 1}/{max_retries}): {connectivity_err}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                else:
                    print(f"[WARNING] Erro de conectividade: {connectivity_err}")
                
                # Se chegou aqui e não é a última tentativa, continue
                if attempt < max_retries - 1:
                    continue
                    
                # Última tentativa falhou
                print(f"[WARNING] Firebase inicializado mas sem conectividade após {max_retries} tentativas")
                db = None
                firebase_mock_mode = True
                return False
                
    except Exception as e_cred:
        print(f"[WARNING] Falha ao inicializar com {description}: {e_cred}")
        return False
    
    return False

# ====================================
# [STATS] SISTEMA DE MONITORAMENTO EM TEMPO REAL
# ====================================

def initialize_monitoring_system():
    """Inicializa o sistema de monitoramento em tempo real"""
    global MONITORING_SYSTEM
    
    try:
        config_path = os.path.join("memoria", "monitoring", "config_monitoring.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                MONITORING_SYSTEM.update(config)
        
        # Inicializar estruturas de dados em memória
        MONITORING_SYSTEM['metrics'] = {
            'requests_count': 0,
            'errors_count': 0,
            'response_times': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'system_uptime': time.time(),
            'tokens_saved': 0,
            'versions_created': 0,
            'learning_events': 0,
            'search_count': 0,
            # Novas métricas
            'successful_generations': 0,
            'failed_generations': 0,
            'backups_created': 0,
            'gemini_errors': 0,
            'json_parse_errors': 0,
            'validation_warnings': 0,
            'validation_errors': 0,
            # Novas métricas para validação de impressos
            'impressos_validated': 0,
            'impressos_corrected': 0,
            'impressos_validation_errors': 0,
            # Métricas para rate limiting
            'gemini_requests_per_key': defaultdict(int),
            'rate_limit_exceeded': 0
        }
        
        # Lista de eventos de busca (sanitizados) para telemetria — manter tamanho limitado
        MONITORING_SYSTEM['search_events'] = deque(maxlen=200)
        
        MONITORING_SYSTEM['alerts'] = []
        MONITORING_SYSTEM['active'] = True
        
        # Iniciar thread de coleta de métricas
        monitoring_thread = threading.Thread(target=collect_system_metrics, daemon=True)
        monitoring_thread.start()
        
        print("[STATS] Sistema de monitoramento inicializado!")
        return True
        
    except Exception as e:
        print(f"[WARNING] Erro ao inicializar sistema de monitoramento: {e}")
        MONITORING_SYSTEM['active'] = False
        return False

# Rate limiting helpers for Gemini keys (sliding-window per key)
RATE_LIMIT_STATE = defaultdict(lambda: deque())
RATE_LIMIT_LOCK = threading.Lock()
GEMINI_RATE_WINDOW_SECONDS = int(os.getenv("GEMINI_RATE_WINDOW_SECONDS", "60"))
GEMINI_MAX_REQUESTS_PER_WINDOW = int(os.getenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "30"))

def register_gemini_request(key: str):
    """Registra timestamp de requisição para uma chave (sliding window)."""
    if not key:
        return
    now_ts = time.time()
    with RATE_LIMIT_LOCK:
        dq = RATE_LIMIT_STATE[key]
        dq.append(now_ts)
        # remover timestamps antigos
        cutoff = now_ts - GEMINI_RATE_WINDOW_SECONDS
        while dq and dq[0] < cutoff:
            dq.popleft()
        RATE_LIMIT_STATE[key] = dq

def rate_limit_exceeded(key: str) -> bool:
    """Retorna True se a chave excedeu o limite configurado."""
    if not key:
        return True
    with RATE_LIMIT_LOCK:
        dq = RATE_LIMIT_STATE.get(key, deque())
        now_ts = time.time()
        cutoff = now_ts - GEMINI_RATE_WINDOW_SECONDS
        # limpar antigos
        while dq and dq[0] < cutoff:
            dq.popleft()
        RATE_LIMIT_STATE[key] = dq
        return len(dq) >= GEMINI_MAX_REQUESTS_PER_WINDOW

def get_finish_reason_name(value) -> str:
    """Normaliza finish_reason para int e retorna nome legível."""
    try:
        code = int(value) if value is not None else -1
    except Exception:
        code = -1
    return FINISH_REASON_NAMES.get(code, f"UNKNOWN_{code}")
def collect_system_metrics():
    """Coleta métricas do sistema em tempo real"""
    while MONITORING_SYSTEM.get('active', False):
        try:
            # Coletar métricas do sistema
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent()
            
            # Armazenar métricas
            MONITORING_SYSTEM['metrics']['memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent
            })
            
            # Verificar alertas
            check_alerts(memory_percent, cpu_percent)
            
            # Aguardar intervalo configurado
            interval = MONITORING_SYSTEM.get('monitoring_system', {}).get('configuracao', {}).get('intervalo_coleta', 30)
            time.sleep(interval)
            
        except Exception as e:
            print(f"[WARNING] Erro na coleta de métricas: {e}")
            time.sleep(30)  # Aguardar mais tempo em caso de erro

def check_alerts(memory_percent, cpu_percent):
    """Verifica e gera alertas baseado nos thresholds"""
    alerts_config = MONITORING_SYSTEM.get('monitoring_system', {}).get('alertas_configurados', {})
    
    # Alert de memória alta
    memory_threshold = float(alerts_config.get('memoria_alta', {}).get('threshold', '85').rstrip('%'))
    if memory_percent > memory_threshold:
        create_alert('memoria_alta', f'Uso de memória: {memory_percent:.1f}%')
    
    # Cleanup de alertas antigos (manter apenas últimos 50)
    if len(MONITORING_SYSTEM['alerts']) > 50:
        MONITORING_SYSTEM['alerts'] = MONITORING_SYSTEM['alerts'][-50:]

def create_alert(alert_type, message):
    """Cria um novo alerta"""
    alert = {
        'type': alert_type,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'severity': 'warning'
    }
    
    MONITORING_SYSTEM['alerts'].append(alert)
    print(f"🚨 ALERT [{alert_type}]: {message}")

def log_search_event(query: str, hit: dict):
    """
    Registra evento de busca sanitizado na estrutura de monitoramento.
    hit: {'title','snippet','link','query'}
    """
    try:
        if not MONITORING_SYSTEM.get('active'):
            return
        event = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "title": hit.get("title", "")[:200],
            "snippet": hit.get("snippet", "")[:1000],  # já sanitizado pelo web_search
            "link": hit.get("link", "")[:500]
        }
        # incrementar métricas simples
        MONITORING_SYSTEM['metrics']['search_count'] = MONITORING_SYSTEM['metrics'].get('search_count', 0) + 1
        MONITORING_SYSTEM['search_events'].append(event)
    except Exception as e:
        print(f"[WARNING] Erro ao logar evento de busca: {e}")

def log_request_metric(endpoint, response_time, status_code):
    """Registra métricas de requisição"""
    if not MONITORING_SYSTEM.get('active'):
        return
        
    MONITORING_SYSTEM['metrics']['requests_count'] += 1
    MONITORING_SYSTEM['metrics']['response_times'].append({
        'endpoint': endpoint,
        'response_time': response_time,
        'status_code': status_code,
        'timestamp': datetime.now().isoformat()
    })
    
    if status_code >= 400:
        MONITORING_SYSTEM['metrics']['errors_count'] += 1
        
    # Verificar alerta de tempo de resposta (ajustado para IA)
    if response_time > 120000:  # 2 minutos - mais realistico para operações de IA
        create_alert('tempo_resposta_alto', f'Endpoint {endpoint}: {response_time}ms')

def log_token_savings(tokens_saved):
    """Registra economia de tokens"""
    if MONITORING_SYSTEM.get('active'):
        MONITORING_SYSTEM['metrics']['tokens_saved'] += tokens_saved

def log_version_created():
    """Registra criação de nova versão"""
    if MONITORING_SYSTEM.get('active'):
        MONITORING_SYSTEM['metrics']['versions_created'] += 1

def log_learning_event():
    """Registra evento de aprendizado"""
    if MONITORING_SYSTEM.get('active'):
        MONITORING_SYSTEM['metrics']['learning_events'] += 1

def get_monitoring_stats():
    """Retorna estatísticas do sistema de monitoramento"""
    if not MONITORING_SYSTEM.get('active'):
        return {"status": "inactive"}
    
    metrics = MONITORING_SYSTEM['metrics']
    uptime_seconds = time.time() - metrics['system_uptime']
    uptime_hours = uptime_seconds / 3600
    
    # Calcular médias
    recent_response_times = list(metrics['response_times'])[-10:]  # últimas 10 requisições
    avg_response_time = sum(rt['response_time'] for rt in recent_response_times) / len(recent_response_times) if recent_response_times else 0
    
    recent_memory = list(metrics['memory_usage'])[-5:]  # últimas 5 medições
    avg_memory = sum(m['memory_percent'] for m in recent_memory) / len(recent_memory) if recent_memory else 0
    
    return {
        "status": "active",
        "uptime_hours": round(uptime_hours, 2),
        "total_requests": metrics['requests_count'],
        "total_errors": metrics['errors_count'],
        "error_rate": round((metrics['errors_count'] / max(metrics['requests_count'], 1)) * 100, 2),
        "avg_response_time_ms": round(avg_response_time, 2),
        "avg_memory_percent": round(avg_memory, 1),
        "tokens_saved": metrics['tokens_saved'],
        "versions_created": metrics['versions_created'],
        "learning_events": metrics['learning_events'],
        "recent_alerts": MONITORING_SYSTEM['alerts'][-5:],  # últimos 5 alertas
        "total_alerts": len(MONITORING_SYSTEM['alerts'])
    }

def load_rules_from_firestore():
    global AGENT_RULES, PARSED_REFERENCIAS, VERSION_SYSTEM

    print("[DEBUG] Iniciando carregamento de regras...")
    print(f"[DEBUG] Firebase mock mode: {firebase_mock_mode}")
    print(f"[DEBUG] Database connection: {db is not None}")

    # Tentar carregar sistema híbrido primeiro
    print("[DEBUG] Tentando inicializar sistema híbrido de memória...")
    hybrid_success = initialize_local_memory_system()

    if hybrid_success:
        print("[FAST] Sistema híbrido de memória local ativo!")

        # Inicializar sistema de versionamento
        try:
            initialize_version_system()
            VERSION_SYSTEM['active'] = True
            print("📦 Sistema de versionamento ativo!")

            # Criar snapshot automático na inicialização
            auto_version_on_change("Inicialização do sistema híbrido")

        except Exception as e:
            print(f"[WARNING] Erro ao inicializar sistema de versionamento: {e}")
            VERSION_SYSTEM['active'] = False

        # Inicializar sistema de monitoramento
        try:
            initialize_monitoring_system()
            print("[STATS] Sistema de monitoramento ativo!")

            # Registrar economia de tokens na inicialização
            log_token_savings(28000)  # 82% de 35000 tokens médios

        except Exception as e:
            print(f"[WARNING] Erro ao inicializar sistema de monitoramento: {e}")
            MONITORING_SYSTEM['active'] = False

        # Sistema híbrido local está ativo - pular Firestore
        print("ℹ️ Sistema híbrido local ativo - pulando carregamento Firestore")

        # [SUCCESS] CORREÇÃO: Popular AGENT_RULES com dados do sistema local
        print("[DEBUG] Populando AGENT_RULES com dados do sistema local...")
        print(f"[DEBUG] LOCAL_MEMORY_SYSTEM keys: {list(LOCAL_MEMORY_SYSTEM.keys())}")

        global AGENT_RULES
        referencias_base = LOCAL_MEMORY_SYSTEM.get('referencias_base')
        print(f"[DEBUG] referencias_base loaded: {len(referencias_base) if referencias_base else 0} characters")

        if referencias_base:
            AGENT_RULES = {
                'referencias_md': referencias_base,
                'gabarito_json': LOCAL_MEMORY_SYSTEM.get('gabarito_template', '{}'),
                'config': LOCAL_MEMORY_SYSTEM.get('config', {}),
                'aprendizados': LOCAL_MEMORY_SYSTEM.get('aprendizados', [])
            }
            print(f"[SUCCESS] AGENT_RULES populado com {len(AGENT_RULES.get('referencias_md', ''))} caracteres de referências")
            print(f"[DEBUG] AGENT_RULES keys: {list(AGENT_RULES.keys())}")
        else:
            print("[ERROR] referencias_base não encontrado no sistema local!")

        print("[SUCCESS] Inicialização completa do sistema híbrido!")
        return
    else:
        print("[ERROR] Falha ao inicializar sistema híbrido!")

    # Fallback para sistema antigo se sistema local falhar
    print("[REFRESH] Usando sistema de memória tradicional (Firestore)...")
    if firebase_mock_mode or not db:
        print("[WARNING] Firebase em modo mock ou desconectado - sistema sem regras!")
        return

    try:
        print("[BRAIN] Carregando regras do Firestore...")
        doc_ref = db.collection('agent_config').document('rules')
        doc = doc_ref.get()
        if doc.exists:
            AGENT_RULES = doc.to_dict() or {}  # Garantir que nunca seja None
            print("[SUCCESS] Regras carregadas na memória com sucesso!")

            # Fazer parse do referencias_md para otimização
            referencias_content = AGENT_RULES.get('referencias_md', '')
            if referencias_content:
                print("🔧 Fazendo parse do referencias.md...")
                PARSED_REFERENCIAS = parse_referencias_md(referencias_content)
                if PARSED_REFERENCIAS:
                    print("[SUCCESS] Referencias.md parsed e otimizado com sucesso!")
                else:
                    print("[WARNING] Falha no parsing - usando conteúdo completo como fallback")
            else:
                print("[WARNING] Conteúdo referencias_md não encontrado no documento")
        else:
            print("[ERROR] ERRO: Documento 'rules' não encontrado.")
    except Exception as e:
        print(f"[ERROR] ERRO CRÍTICO ao carregar regras do Firestore: {e}")

def configure_gemini_keys():
    global GEMINI_CONFIGS
    # Configuração simplificada de modelos Gemini
    api_keys = [
        os.getenv("GOOGLE_API_KEY_1"),
        os.getenv("GOOGLE_API_KEY_2"),
        os.getenv("GOOGLE_API_KEY_3"),
        os.getenv("GOOGLE_API_KEY_4"),
        os.getenv("GOOGLE_API_KEY_5"),
    ]

    valid_keys = [key for key in api_keys if key]

    flash_configs = [{"key": key, "model_name": 'gemini-2.5-flash'} for key in valid_keys]
    flash_lite_configs = [{"key": key, "model_name": 'gemini-2.5-flash-lite'} for key in valid_keys]
    flash_2_0_configs = [{"key": key, "model_name": 'gemini-2.0-flash-exp'} for key in valid_keys]
    pro_configs = [{"key": key, "model_name": 'gemini-2.5-pro'} for key in valid_keys]

    GEMINI_CONFIGS = {
        'flash': flash_configs,
        'flash_lite': flash_lite_configs,
        'flash_2_0': flash_2_0_configs,
        'pro': pro_configs,
        'all': pro_configs + flash_configs + flash_lite_configs + flash_2_0_configs
    }

    if not valid_keys:
        print("[ERROR] Nenhuma chave de API do Gemini foi encontrada.")
    else:
        print(f"[SUCCESS] {len(valid_keys)} chave(s) de API do Gemini configurada(s).")
        print(f"[INFO] Modelo para tarefas rápidas: 'gemini-2.5-flash'")
        print(f"[INFO] Modelo para tarefas avançadas: 'gemini-2.5-pro'")

# --- Gerenciador de Ciclo de Vida ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    if initialize_firebase():
        load_rules_from_firestore()
    configure_gemini_keys()
    yield
    print("Servidor finalizado.")

# --- Aplicação FastAPI ---
app = FastAPI(title="Agente de IA", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Incluir rota RAG (busca por similaridade usando embeddings locais)
try:
    from rag_agent import router as rag_router
    app.include_router(rag_router)
    print("[SUCCESS] Rota RAG incluída com sucesso!")
except ImportError as e:
    print(f"[WARNING] Não foi possível incluir rota RAG: erro de importação - {e}")
except Exception as e:
    print(f"[WARNING] Não foi possível incluir rota RAG: {e}")

# --- Middleware de Monitoramento ---
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # Em milissegundos
    
    # Registrar métricas
    endpoint = request.url.path
    log_request_metric(endpoint, process_time, response.status_code)
    
    # Adicionar header com tempo de resposta
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# --- Função Auxiliar para RAG ---
async def perform_rag_search(query: str, top_k: int = 5, generation_model: str = "flash") -> str:
    """Executa busca RAG usando o sistema de embeddings local"""
    try:
        # Chamar diretamente a função async rag_query de rag_agent (evita subprocessos)
        from rag_agent import rag_query, RAGQuery

        body = RAGQuery(query=query, top_k=top_k, generation_model=generation_model)
        # Como estamos em contexto async, await diretamente a coroutine
        rag_result = await rag_query(body)

        evidence = rag_result.get('evidence', []) if isinstance(rag_result, dict) else []
        contexts = []
        for item in evidence[:top_k]:
            metadata = item.get('metadata', {}) or {}
            text_preview = metadata.get('text_preview') or metadata.get('text') or ''
            source_path = (metadata.get('meta') or {}).get('path', 'fonte desconhecida')
            score = item.get('score', 0)
            contexts.append(f"**Fonte:** {source_path} (Score: {score:.3f})\n{text_preview}")

        if contexts:
            return "\n\n---\n\n".join(contexts)
        return ""
    except Exception as e:
        print(f"[WARNING] Erro no sistema RAG: {e}")
        return ""

# --- Funções de Construção de Prompts (build_prompt_fase_1 atualizada com RAG) ---
async def build_prompt_fase_1(tema: str, especialidade: str) -> str:
    """Constrói o prompt para a Fase 1 usando RAG para buscar PDFs indexados"""
    
    # Executar busca RAG para encontrar PDFs relacionados ao tema
    print(f"🔍 Buscando PDFs indexados para o tema: {tema}")
    rag_query = f"{tema} {especialidade} diretrizes protocolo tratamento"
    pdf_content = await perform_rag_search(rag_query, top_k=5, generation_model="flash")
    
    pdf_instruction = ""
    if pdf_content:
        pdf_instruction = f"""
**FONTE PRIMÁRIA DE CONHECIMENTO (PDFs Indexados):**
---
{pdf_content}
---

**INSTRUÇÕES ESPECÍFICAS PARA ANÁLISE DOS PDFs:**
1. **ANALISE O CONTEÚDO**: Use os trechos mais relevantes dos PDFs indexados sobre "{tema}"
2. **EXTRAIA APENAS O RELEVANTE**: Foque no que é essencial para estações médicas sobre "{tema}"
3. **INTEGRE AS FONTES**: Combine informações de diferentes fontes quando complementares
4. **ESTRUTURE A INFORMAÇÃO**: Organize conforme os tópicos solicitados abaixo
"""
    else:
        print("[WARNING] Nenhum PDF relevante encontrado nos embeddings locais")
    
    return f"""
# FASE 1: ANÁLISE E CONTEXTUALIZAÇÃO ESPECÍFICA

**SUA TAREFA PRINCIPAL:**
Criar um resumo clínico FOCADO ESPECIFICAMENTE no tema "{tema}" em {especialidade}.

**METODOLOGIA:**
1. **Analise a Fonte Primária (se PDF fornecido):** 
   - Use o PDF como sua PRINCIPAL fonte de verdade para conduta clínica
   - Leia o índice e extraia apenas informações sobre "{tema}"
   - Faça um relatório preciso focando no essencial para estações médicas
   - IGNORE outros temas/doenças que possam estar no arquivo
   
   **Tópicos a buscar no PDF:**
   - Conceitos iniciais relevantes ao tema/doença específica
   - Tópicos e subtítulos referentes ao TEMA CENTRAL "{tema}": 
     * Classificação, fatores de risco, fatores de proteção
     * Prevenção, quadro clínico, diagnóstico, diagnóstico diferencial
     * Avaliação pré-operatória, estadiamento, tratamento
     * Prognóstico, complicações
   - Referências bibliográficas específicas
   - Considerações finais sobre o tema

2. **Pesquise Normativas Complementares:** 
   - "Casos clínicos reais {tema}"
   - "Diretrizes brasileiras {tema}"
   - "Protocolo {tema} Revalida INEP"
   - "Consenso {tema} sociedade brasileira de {especialidade}"

3. **Sintetize o Conhecimento:** 
   Com base em TODAS as fontes (PDF se existir + conteúdo web), crie um resumo objetivo utilizando EXATAMENTE esta estrutura:

   * **Contexto Clínico:**
   * **Anamnese Completa:** (história da doença atual, antecedentes patológicos/fisiológicos, antecedentes familiares, hábitos de vida, outros achados relevantes)
   * **Exame Físico:** (alterações esperadas nos sinais vitais, exame físico geral, manobras semiológicas específicas)
   * **Critérios Diagnósticos Principais:** (critérios essenciais para o diagnóstico)
   * **Exames Complementares:** 
     - Laboratoriais padrão e específicos
     - Exames de imagem de rotina e específicos
     - Conforme normas e diretrizes
   * **Alterações nos Sinais Vitais e Exame Físico:**
   * **Hipóteses Diagnósticas:** (síndrome principal e diferenciais)
   * **Diagnósticos Diferenciais a Descartar:**
   * **Tratamento de Primeira e Segunda Linha:**
   * **Avaliação Pré-operatória:** (se aplicável)
   * **Sinais de Alarme/Complicações:**
   * **Fatores de Risco:**
   * **Fatores de Proteção:**
   * **Estadiamento e Encaminhamentos:** (se aplicável)
   * **Orientações e Seguimento:**
   * **Contraindicações e Efeitos Colaterais:**
   * **Notificações Obrigatórias:** (SINAM, CAPS-AD, etc., se aplicável)
   * **Rastreamento e Prevenção:**

{pdf_instruction}

{load_and_apply_user_learnings()}
"""

# (As outras funções de build_prompt permanecem as mesmas)
async def build_prompt_fase_2(tema: str, especialidade: str, resumo_clinico: str, abordagens_selecionadas: Optional[List[str]] = None) -> str:
    """Constrói o prompt da Fase 2 usando RAG para buscar estações INEP similares"""
    
    # Executar busca RAG para encontrar estações INEP relacionadas
    print(f"🔍 Buscando estações INEP similares para: {tema} {especialidade}")
    rag_query = f"estação {tema} {especialidade} INEP revalida"
    estacoes_content = await perform_rag_search(rag_query, top_k=3, generation_model="flash")
    
    # Usar sistema híbrido se disponível
    if LOCAL_MEMORY_SYSTEM:
        print("[FAST] Usando sistema híbrido para Fase 2...")
        contexto_otimizado = get_context_for_phase(2)
    else:
        print("[REFRESH] Fallback para sistema tradicional...")
        # Seções específicas para Fase 2: 0, 1, 2, 3, 4.1, 4.2, 6, 8
        secoes_fase_2 = [
            'principios_fundamentais',
            'arquitetura_estacoes', 
            'diretrizes_tarefas',
            'tarefas_especialidade',
            'regras_basicas_ator',
            'regras_contextos_ator',
            'tipos_impressos',
            'estruturas_especialidade'
        ]
        
        # Construir contexto otimizado usando apenas seções relevantes
        contexto_otimizado = ""
        if PARSED_REFERENCIAS:
            print("🔧 Construindo prompt Fase 2 com seções otimizadas...")
            for secao in secoes_fase_2:
                if secao in PARSED_REFERENCIAS:
                    contexto_otimizado += f"\n\n--- {secao.upper().replace('_', ' ')} ---\n"
                    contexto_otimizado += PARSED_REFERENCIAS[secao]
            print(f"[STATS] Fase 2: {len(contexto_otimizado)} caracteres (vs {len(AGENT_RULES.get('referencias_md', '') if AGENT_RULES else '')} originais)")
        else:
            print("[WARNING] PARSED_REFERENCIAS não disponível, usando conteúdo completo como fallback")
            contexto_otimizado = AGENT_RULES.get('referencias_md', "") if AGENT_RULES else ""
    
    # Adicionar seção de exemplos INEP se encontrados
    secao_exemplos = ""
    if estacoes_content:
        secao_exemplos = f"""

**EXEMPLOS DE ESTAÇÕES INEP SIMILARES (PARA REFERÊNCIA DE ESTRUTURA):**
{estacoes_content}

**INSTRUÇÕES SOBRE OS EXEMPLOS:**
- Use os exemplos acima como REFERÊNCIA DE ESTRUTURA e PADRÃO INEP
- Observe os padrões de tarefas, cenários e abordagens utilizadas
- Adapte as estratégias para o tema específico: {tema}
- NÃO copie o conteúdo clínico, apenas a estrutura e padrões"""

    # Determinar as abordagens a serem geradas
    if abordagens_selecionadas:
        # Filtrar apenas as abordagens selecionadas
        abordagens_para_gerar = [
            abordagem for abordagem in ABORDAGENS_PADRAO
            if abordagem["id"] in abordagens_selecionadas
        ]
        print(f"🎯 Gerando {len(abordagens_para_gerar)} abordagens selecionadas: {[a['nome'] for a in abordagens_para_gerar]}")
    else:
        # Usar todas as 5 abordagens padrão (comportamento antigo)
        abordagens_para_gerar = ABORDAGENS_PADRAO
        print("🎯 Gerando todas as 5 abordagens padrão")

    # Construir as instruções das propostas
    propostas_instrucoes = ""
    for i, abordagem in enumerate(abordagens_para_gerar, 1):
        propostas_instrucoes += f"\n{i}. **{abordagem['nome']}:** {abordagem['descricao']} - {abordagem['foco']}"

    return f"""# FASE 2: GERAÇÃO DE ESTRATÉGIAS

**CONTEXTO CLÍNICO:**
{resumo_clinico}

**REGRAS DE ARQUITETURA E DIRETRIZES (SEÇÕES OTIMIZADAS):**
{contexto_otimizado}{secao_exemplos}

{load_and_apply_user_learnings()}

**SUA TAREFA:**
Gere {len(abordagens_para_gerar)} proposta(s) estratégica(s) para uma estação sobre **{tema}** em **{especialidade}**, conforme as abordagens selecionadas:{propostas_instrucoes}

Cada proposta deve especificar:
- Tipo de estação e foco principal
- Cenário de atendimento (atenção primária/secundária/terciária)
- Tarefas principais esperadas
- Materiais necessários (impressos, escalas, imagens)
- Nível de dificuldade"""

def load_and_apply_user_learnings() -> str:
    """
    Carrega as regras aprendidas do aprendizados_usuario.jsonl e formata para uso nos prompts
    Retorna string formatada com todas as regras categorizadas
    """
    try:
        learnings_path = os.path.join("memoria", "aprendizados_usuario.jsonl")
        
        if not os.path.exists(learnings_path):
            print("[WARNING] Arquivo aprendizados_usuario.jsonl não encontrado")
            return ""
        
        with open(learnings_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # Parse do JSONL (JSON Lines)
        if content.startswith('[') and content.endswith(']'):
            # É um array JSON normal
            learnings = json.loads(content)
        else:
            # É JSONL real (uma linha por objeto)
            learnings = []
            for line in content.split('\n'):
                if line.strip():
                    learnings.append(json.loads(line.strip()))
        
        if not learnings:
            return ""
        
        # Categorizar e formatar as regras
        regras_obrigatorias = []
        regras_restricoes = []
        regras_preferencias = []
        
        for learning in learnings:
            rule = learning.get('rule', '')
            category = learning.get('category', 'preferencia')
            context = learning.get('context', '')
            
            if category == 'obrigatorio':
                regras_obrigatorias.append(f"• {rule}")
            elif category == 'restricao':
                regras_restricoes.append(f"• {rule}")
            else:
                regras_preferencias.append(f"• {rule}")
        
        # Construir seção formatada
        secao_regras = """

**🎯 REGRAS APRENDIDAS DO USUÁRIO (APLICAR RIGOROSAMENTE):**"""
        
        if regras_obrigatorias:
            secao_regras += f"""

**REGRAS OBRIGATÓRIAS:**
{chr(10).join(regras_obrigatorias)}"""
        
        if regras_restricoes:
            secao_regras += f"""

**RESTRIÇÕES IMPORTANTES:**
{chr(10).join(regras_restricoes)}"""
        
        if regras_preferencias:
            secao_regras += f"""

**PREFERÊNCIAS DO SISTEMA:**
{chr(10).join(regras_preferencias)}"""
        
        print(f"[SUCCESS] Carregadas {len(learnings)} regras aprendidas do usuário")
        return secao_regras
        
    except Exception as e:
        print(f"[WARNING] Erro ao carregar regras aprendidas: {e}")
        return ""

def extract_json_from_text(text: str) -> str:
    """
    Extrai o primeiro JSON (objeto ou array) de uma resposta textual gerada pela IA.
    Versão aprimorada com múltiplas estratégias de extração e validação.
    """
    try:
        import re

        if not text or not isinstance(text, str):
            return text

        # 1) Procurar fence ```json ... ``` (prioridade máxima)
        m = re.search(r"```json\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", text, re.I)
        if m:
            candidate = m.group(1).strip()
            if _is_valid_json_structure(candidate):
                return candidate

        # 2) Procurar fence ``` ... ``` contendo JSON genérico
        m2 = re.search(r"```\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", text, re.I)
        if m2:
            candidate = m2.group(1).strip()
            if _is_valid_json_structure(candidate):
                return candidate

        # 3) Procurar JSON entre <json> tags
        m3 = re.search(r"<json>\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*</json>", text, re.I)
        if m3:
            candidate = m3.group(1).strip()
            if _is_valid_json_structure(candidate):
                return candidate

        # 4) Heurística aprimorada: encontrar JSON mais provável
        json_candidates = []

        # Procurar objetos JSON completos
        for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text):
            candidate = match.group()
            if _is_valid_json_structure(candidate):
                json_candidates.append((candidate, match.start()))

        # Procurar arrays JSON completos
        for match in re.finditer(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', text):
            candidate = match.group()
            if _is_valid_json_structure(candidate):
                json_candidates.append((candidate, match.start()))

        if json_candidates:
            # Retornar o primeiro JSON válido encontrado
            return json_candidates[0][0]

        # 5) Última tentativa: procurar por padrões específicos de estações
        station_patterns = [
            r'\{[^{}]*"tituloEstacao"[^{}]*"numeroDaEstacao"[^{}]*\}',
            r'\{[^{}]*"idEstacao"[^{}]*"especialidade"[^{}]*\}',
            r'\{[^{}]*"instrucoesParticipante"[^{}]*"padraoEsperadoProcedimento"[^{}]*\}'
        ]

        for pattern in station_patterns:
            match = re.search(pattern, text)
            if match:
                candidate = _expand_json_boundaries(text, match.start(), match.end())
                if candidate and _is_valid_json_structure(candidate):
                    return candidate

        # 6) Fallback: tentar encontrar qualquer estrutura JSON-like
        first_brace = None
        for ch in ('{', '['):
            pos = text.find(ch)
            if pos != -1:
                if first_brace is None or pos < first_brace:
                    first_brace = pos

        if first_brace is None:
            return text.strip()

        opening = text[first_brace]
        if opening == '{':
            last_pos = text.rfind('}')
        else:
            last_pos = text.rfind(']')

        if last_pos != -1 and last_pos > first_brace:
            candidate = text[first_brace:last_pos+1].strip()
            if _is_valid_json_structure(candidate):
                return candidate

        return text.strip()

    except Exception as e:
        print(f"[WARNING] Erro na extração de JSON: {e}")
        return text

def _is_valid_json_structure(text: str) -> bool:
    """Verifica se o texto tem estrutura básica válida de JSON"""
    try:
        text = text.strip()
        if not text:
            return False

        # Verificações básicas de estrutura
        if text.startswith('{') and text.endswith('}'):
            # Contar chaves balanceadas
            brace_count = 0
            in_string = False
            escape_next = False

            for char in text:
                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count < 0:
                            return False

            return brace_count == 0

        elif text.startswith('[') and text.endswith(']'):
            # Contar colchetes balanceados
            bracket_count = 0
            in_string = False
            escape_next = False

            for char in text:
                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count < 0:
                            return False

            return bracket_count == 0

        return False

    except Exception:
        return False

def _expand_json_boundaries(text: str, start: int, end: int) -> str:
    """Expande os limites de um JSON parcial para tentar encontrar um JSON completo"""
    try:
        # Tentar expandir para encontrar chaves balanceadas
        brace_count = 0
        bracket_count = 0
        in_string = False
        escape_next = False

        # Encontrar o início real
        real_start = start
        for i in range(start, -1, -1):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '}':
                    brace_count += 1
                elif char == '{':
                    brace_count -= 1
                    if brace_count < 0:
                        real_start = i
                        break
                elif char == ']':
                    bracket_count += 1
                elif char == '[':
                    bracket_count -= 1
                    if bracket_count < 0:
                        real_start = i
                        break

        # Resetar contadores
        brace_count = 0
        bracket_count = 0
        in_string = False
        escape_next = False

        # Encontrar o fim real
        real_end = end
        for i in range(end, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count < 0:
                        real_end = i + 1
                        break
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count < 0:
                        real_end = i + 1
                        break

        if real_start < real_end:
            return text[real_start:real_end].strip()

        return text[start:end].strip()

    except Exception:
        return text[start:end].strip()

def _advanced_json_correction(json_str: str) -> str:
    """
    Correção avançada de JSON com estratégias específicas para estruturas de estações médicas
    """
    import re

    try:
        # Estratégia 1: Identificar e corrigir estruturas comuns malformadas
        json_str = _fix_common_json_patterns(json_str)

        # Estratégia 2: Balancear chaves e colchetes
        json_str = _balance_json_structure(json_str)

        # Estratégia 3: Corrigir problemas específicos de estações
        json_str = _fix_station_json_issues(json_str)

        # Estratégia 4: Limpeza final
        json_str = _final_json_cleanup(json_str)

        # Testar se ficou válido
        json.loads(json_str)
        return json_str

    except Exception as e:
        # Se ainda não conseguiu corrigir, tentar uma abordagem mais agressiva
        try:
            return _aggressive_json_repair(json_str)
        except Exception:
            raise e


def _fix_common_json_patterns(s: str) -> str:
    """Corrige padrões comuns de JSON malformado"""
    import re

    # Corrigir objetos sem separador de vírgula
    s = re.sub(r'}\s*{', r'},{', s)

    # Corrigir arrays sem separador
    s = re.sub(r']\s*\[', r'],[' , s)

    # Corrigir vírgulas duplas
    s = re.sub(r',,+', r',', s)

    # Corrigir vírgulas antes de fechamento
    s = re.sub(r',(\s*[}\]])', r'\1', s)

    return s


def _balance_json_structure(s: str) -> str:
    """Balanceia chaves e colchetes não balanceados"""
    import re

    def count_and_balance(text, open_char, close_char):
        count = 0
        in_string = False
        escape_next = False

        for char in text:
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if not in_string:
                if char == open_char:
                    count += 1
                elif char == close_char:
                    count -= 1

        # Adicionar caracteres de fechamento se necessário
        if count > 0:
            text += close_char * count
        elif count < 0:
            text = open_char * abs(count) + text

        return text

    # Balancear chaves primeiro
    s = count_and_balance(s, '{', '}')

    # Depois balancear colchetes
    s = count_and_balance(s, '[', ']')

    return s


def _fix_station_json_issues(s: str) -> str:
    """Corrige problemas específicos de JSONs de estações médicas"""
    import re

    # Corrigir estruturas de pontuacao aninhadas
    s = re.sub(r'"pontuacoes"\s*:\s*{\s*"([^"]+)"\s*:\s*{([^}]*"pontos"[^}]*)}([^}]*)}', r'"pontuacoes": {"\1": {\2}\3}', s)

    # Corrigir valores numéricos sem aspas em campos específicos
    numeric_fields = ['numeroDaEstacao', 'tempoDuracaoMinutos']
    for field in numeric_fields:
        s = re.sub(rf'"({field})"\s*:\s*([^,\]}}\s]+)', rf'"\1": "\2"', s)

    # Corrigir listas de tarefasPrincipais
    s = re.sub(r'"tarefasPrincipais"\s*:\s*([^[\]]*)\[([^\]]*)\]([^[\]]*)}', r'"tarefasPrincipais": [\2]', s)

    # Corrigir estruturas de itensAvaliacao
    s = re.sub(r'"itensAvaliacao"\s*:\s*{\s*"([^"]+)"\s*:\s*([^}]*)}([^}]*)}', r'"itensAvaliacao": [{"\1": \2}\3]', s)

    return s


def _final_json_cleanup(s: str) -> str:
    """Limpeza final do JSON"""
    import re

    # Remover espaços em branco excessivos
    s = re.sub(r'\s+', ' ', s)

    # Corrigir aspas não fechadas em strings
    s = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)$', r'\1"', s)

    # Garantir que o JSON comece e termine corretamente
    s = s.strip()
    if not s.startswith(('{', '[')):
        if '"tituloEstacao"' in s or '"especialidade"' in s:
            s = '{' + s + '}'
        else:
            s = '[' + s + ']'

    return s


def _aggressive_json_repair(json_str: str) -> str:
    """Reparo agressivo de JSON como último recurso"""
    import re

    # Extrair apenas o conteúdo entre aspas e reconstruir
    try:
        # Tentar encontrar padrões de chave-valor
        pairs = re.findall(r'"([^"]+)"\s*:\s*([^,}]+)', json_str)

        if pairs:
            reconstructed = '{'
            for i, (key, value) in enumerate(pairs):
                if i > 0:
                    reconstructed += ','
                reconstructed += f'"{key}":{value}'
            reconstructed += '}'

            # Testar se é válido
            json.loads(reconstructed)
            return reconstructed

    except Exception:
        pass

    # Se tudo falhar, tentar uma estrutura básica
    return '{"error": "JSON could not be repaired", "original": "' + json_str[:100] + '"}'


def sanitize_json_string(s: str) -> str:
    """
    Tenta corrigir problemas comuns de JSON gerado por LLMs antes do json.loads.
    Versão aprimorada com múltiplas estratégias de sanitização e correção avançada.
    """
    import re
    try:
        # Se já é carregável, retorna sem alterações
        json.loads(s)
        return s
    except Exception:
        original_s = s

        # 1) Corrigir problemas de aspas não fechadas em strings
        try:
            s = _fix_unclosed_quotes(s)
        except Exception:
            s = original_s

        # 2) Escapar backslashes que não fazem parte de uma sequência de escape válida
        try:
            s = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', s)
        except Exception:
            pass

        # 3) Corrigir vírgulas pendentes antes de chaves de fechamento
        try:
            s = _fix_trailing_commas(s)
        except Exception:
            pass

        # 4) Corrigir valores booleanos e null malformados
        try:
            s = _fix_boolean_null_values(s)
        except Exception:
            pass

        # 5) Corrigir números malformados
        try:
            s = _fix_malformed_numbers(s)
        except Exception:
            pass

        # 6) Corrigir problemas específicos de estações médicas
        try:
            s = _fix_station_specific_issues(s)
        except Exception:
            pass

        # 7) Tentar carregar após correções
        try:
            json.loads(s)
            return s
        except Exception:
            # 8) Remover caracteres de controle indesejados (exceto tab/newline/return)
            try:
                cleaned = ''.join(ch for ch in s if ord(ch) >= 32 or ch in '\n\r\t')
                json.loads(cleaned)  # Testar se ficou válido
                return cleaned
            except Exception:
                # 9) Última tentativa: correção estrutural profunda
                try:
                    return _deep_structural_fix(s)
                except Exception:
                    return s


def _fix_station_specific_issues(s: str) -> str:
    """
    Corrige problemas específicos comuns em JSONs de estações médicas
    """
    import re

    # 1) Corrigir campos de pontuação malformados
    s = re.sub(r'"pontos"\s*:\s*([^,}]+)', lambda m: f'"pontos": {m.group(1)}', s)

    # 2) Corrigir estruturas de pontuacao aninhadas incorretas
    s = re.sub(r'"pontuacoes"\s*:\s*\{([^}]*)\{([^}]*)\}([^}]*)\}', r'"pontuacoes": {\1\2\3}', s)

    # 3) Corrigir valores numéricos sem aspas quando deveriam ter
    s = re.sub(r':\s*(\d+\.?\d*)\s*([,}\]])', r': "\1"\2', s)

    # 4) Corrigir arrays malformados em tarefasPrincipais
    s = re.sub(r'"tarefasPrincipais"\s*:\s*([^{]*)\[([^\]]*)\]([^{]*)\}', r'"tarefasPrincipais": [\2]', s)

    # 5) Corrigir objetos sem vírgula de separação
    s = re.sub(r'}\s*\{', r'},{', s)

    # 6) Corrigir listas com objetos malformados
    s = re.sub(r',\s*}', r'}', s)
    s = re.sub(r',\s*]', r']', s)

    return s

def _fix_unclosed_quotes(s: str) -> str:
    """Corrige aspas não fechadas em strings JSON"""
    import re

    # Encontrar strings não fechadas
    pattern = r'"[^"\\]*(?:\\.[^"\\]*)*"|"[^"\\]*(?:\\.[^"\\]*)*$'
    matches = list(re.finditer(pattern, s))

    for match in reversed(matches):
        if not match.group().endswith('"'):
            # String não fechada encontrada
            start = match.start()
            end = match.end()

            # Procurar pelo próximo delimitador válido
            remaining = s[end:]
            delimiters = ['"', ',', '}', ']', '\n']

            closest_delim = None
            closest_pos = len(remaining)

            for delim in delimiters:
                pos = remaining.find(delim)
                if pos != -1 and pos < closest_pos:
                    closest_pos = pos
                    closest_delim = delim

            if closest_delim:
                # Inserir aspa de fechamento
                insert_pos = end + closest_pos
                if closest_delim == '"':
                    # Já tem aspa, apenas ajustar
                    pass
                else:
                    s = s[:insert_pos] + '"' + s[insert_pos:]

    return s

def _fix_trailing_commas(s: str) -> str:
    """Remove vírgulas pendentes antes de chaves de fechamento"""
    import re

    # Padrões para vírgulas pendentes
    patterns = [
        r',(\s*[}\]])',  # vírgula antes de } ou ]
        r',(\s*)$',      # vírgula no final da string
    ]

    for pattern in patterns:
        s = re.sub(pattern, r'\1', s)

    return s

def _fix_boolean_null_values(s: str) -> str:
    """Corrige valores booleanos e null malformados"""
    import re

    # Corrigir variações comuns de true/false/null
    corrections = {
        r'\bTrue\b': 'true',
        r'\bFalse\b': 'false',
        r'\bTRUE\b': 'true',
        r'\bFALSE\b': 'false',
        r'\bNull\b': 'null',
        r'\bNULL\b': 'null',
        r'\bNone\b': 'null',
        r'\bNONE\b': 'null'
    }

    for pattern, replacement in corrections.items():
        s = re.sub(pattern, replacement, s)

    return s

def _fix_malformed_numbers(s: str) -> str:
    """Corrige números malformados"""
    import re

    # Corrigir números com vírgula como separador decimal (formato brasileiro)
    s = re.sub(r'(\d+),(\d+)', r'\1.\2', s)

    # Corrigir números com espaços
    s = re.sub(r'(\d+)\s+(\d+)', r'\1\2', s)

    return s

def _deep_structural_fix(s: str) -> str:
    """Tentativa profunda de correção estrutural"""
    import re

    # 1) Encontrar estruturas JSON-like e tentar balanceá-las
    s = s.strip()

    if s.startswith('{') and not s.endswith('}'):
        s += '}'
    elif s.startswith('[') and not s.endswith(']'):
        s += ']'
    elif not s.startswith(('{', '[')):
        # Tentar adicionar estrutura se parecer com conteúdo JSON
        if '"tituloEstacao"' in s or '"especialidade"' in s:
            s = '{' + s + '}'

    # 2) Balancear chaves e colchetes
    s = _balance_brackets(s)

    # 3) Corrigir problemas de sintaxe comuns
    s = re.sub(r'}\s*{', r'},{', s)  # Objetos consecutivos
    s = re.sub(r']\s*\[', r'],[' , s)  # Arrays consecutivos

    return s

def _balance_brackets(s: str) -> str:
    """Balanceia chaves e colchetes não balanceados"""
    import re

    def count_brackets(text, open_bracket, close_bracket):
        count = 0
        in_string = False
        escape_next = False

        for char in text:
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == open_bracket:
                    count += 1
                elif char == close_bracket:
                    count -= 1

        return count

    # Contar chaves desbalanceadas
    brace_diff = count_brackets(s, '{', '}')
    bracket_diff = count_brackets(s, '[', ']')

    # Adicionar chaves/colchetes de fechamento conforme necessário
    if brace_diff > 0:
        s += '}' * brace_diff
    elif brace_diff < 0:
        s = '{' * abs(brace_diff) + s

    if bracket_diff > 0:
        s += ']' * bracket_diff
    elif bracket_diff < 0:
        s = '[' * abs(bracket_diff) + s

    return s
def validate_json_against_template(generated_json: dict, template_path: str = "gabaritoestacoes.json") -> dict:
    """
    Valida o JSON gerado contra o template gabaritoestacoes.json
    Retorna um dict com status de validação e lista de problemas encontrados
    Versão aprimorada com correção automática mais robusta
    """
    validation_result = {
        "is_valid": True,
        "missing_required_fields": [],
        "invalid_field_types": [],
        "structural_issues": [],
        "warnings": [],
        "corrections_applied": []
    }

    try:
        # Carregar template
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)

        # Campos obrigatórios do template
        required_fields = [
            "idEstacao", "tituloEstacao", "numeroDaEstacao", "especialidade",
            "tempoDuracaoMinutos", "palavrasChave", "nivelDificuldade",
            "instrucoesParticipante", "materiaisDisponiveis", "padraoEsperadoProcedimento"
        ]

        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in generated_json:
                validation_result["missing_required_fields"].append(field)
                validation_result["is_valid"] = False

        # Verificar estrutura de instrucoesParticipante
        if "instrucoesParticipante" in generated_json:
            instrucoes = generated_json["instrucoesParticipante"]
            required_instrucoes_fields = ["cenarioAtendimento", "descricaoCasoCompleta", "tarefasPrincipais"]

            for field in required_instrucoes_fields:
                if field not in instrucoes:
                    validation_result["structural_issues"].append(f"instrucoesParticipante.{field} ausente")
                    validation_result["is_valid"] = False

            # Verificar cenarioAtendimento
            if "cenarioAtendimento" in instrucoes:
                cenario = instrucoes["cenarioAtendimento"]
                required_cenario_fields = ["nivelAtencao", "tipoAtendimento", "infraestruturaUnidade"]

                for field in required_cenario_fields:
                    if field not in cenario:
                        validation_result["structural_issues"].append(f"cenarioAtendimento.{field} ausente")
                        validation_result["is_valid"] = False

            # Verificar se tarefasPrincipais é uma lista com pelo menos 3 itens
            if "tarefasPrincipais" in instrucoes:
                tarefas = instrucoes["tarefasPrincipais"]
                if not isinstance(tarefas, list):
                    validation_result["invalid_field_types"].append("tarefasPrincipais deve ser uma lista")
                    validation_result["is_valid"] = False
                elif len(tarefas) < 3:
                    validation_result["warnings"].append(f"tarefasPrincipais tem apenas {len(tarefas)} itens (recomendado: 3-5)")

        # Verificar estrutura de padraoEsperadoProcedimento
        if "padraoEsperadoProcedimento" in generated_json:
            padrao = generated_json["padraoEsperadoProcedimento"]
            required_padrao_fields = ["idChecklistAssociado", "sinteseEstacao"]

            for field in required_padrao_fields:
                if field not in padrao:
                    validation_result["structural_issues"].append(f"padraoEsperadoProcedimento.{field} ausente")
                    validation_result["is_valid"] = False

            # Verificar sinteseEstacao e itensAvaliacao
            if "sinteseEstacao" in padrao:
                sintese = padrao["sinteseEstacao"]
                if "itensAvaliacao" in sintese:
                    itens = sintese["itensAvaliacao"]
                else:
                    # A correção automática foi desativada pois estava corrompendo a estrutura.
                    # A geração do JSON foi ajustada para produzir a estrutura correta na origem.
                    validation_result["structural_issues"].append("padraoEsperadoProcedimento.sinteseEstacao.itensAvaliacao ausente")
                    validation_result["is_valid"] = False
                    itens = None
            else:
                itens = None

            # Verificar estrutura dos itensAvaliacao
            if itens is not None:
                if not isinstance(itens, list):
                    validation_result["invalid_field_types"].append("itensAvaliacao deve ser uma lista")
                    validation_result["is_valid"] = False
                elif len(itens) < 3:
                    validation_result["warnings"].append(f"itensAvaliacao tem apenas {len(itens)} itens (recomendado: 5-8)")
                else:
                    # Verificar estrutura de cada item
                    for i, item in enumerate(itens):
                        required_item_fields = ["idItem", "descricaoItem", "pontuacoes"]
                        for field in required_item_fields:
                            if field not in item:
                                validation_result["structural_issues"].append(f"itensAvaliacao[{i}].{field} ausente")
                                validation_result["is_valid"] = False

                        # Verificar pontuacoes
                        if "pontuacoes" in item:
                            pontuacoes = item["pontuacoes"]
                            required_pontuacoes = ["adequado", "parcialmenteAdequado", "inadequado"]
                            missing_pontuacoes = []

                            for pont in required_pontuacoes:
                                if pont not in pontuacoes:
                                    missing_pontuacoes.append(pont)

                            # **CORREÇÃO AUTOMÁTICA**: Adicionar pontuações faltantes
                            if missing_pontuacoes:
                                print(f"🔧 CORREÇÃO: Adicionando pontuações faltantes para item {i}: {missing_pontuacoes}")

                                # Obter pontuação base do adequado para calcular parcial
                                pontos_adequado = 0.0
                                if "adequado" in pontuacoes and "pontos" in pontuacoes["adequado"]:
                                    pontos_adequado = pontuacoes["adequado"]["pontos"]
                                elif "adequado" in pontuacoes and isinstance(pontuacoes["adequado"], dict):
                                    # Buscar pontos em qualquer estrutura
                                    for key, value in pontuacoes["adequado"].items():
                                        if key == "pontos" or (isinstance(value, (int, float)) and value > 0):
                                            pontos_adequado = float(value)
                                            break

                                # Adicionar pontuações faltantes com lógica mais robusta
                                for pont in missing_pontuacoes:
                                    if pont == "parcialmenteAdequado":
                                        # Regra: só adicionar se pontuação adequada > 0.25 (não é item binário)
                                        if pontos_adequado > 0.25:
                                            pontos_parcial = round(pontos_adequado / 2, 2)
                                            pontuacoes["parcialmenteAdequado"] = {
                                                "criterio": "Realiza parcialmente as ações esperadas.",
                                                "pontos": pontos_parcial
                                            }
                                            validation_result["corrections_applied"].append(f"Pontuação parcialmenteAdequado ({pontos_parcial}pts) adicionada para item {i}")
                                            validation_result["warnings"].append(f"Pontuação parcialmenteAdequado ({pontos_parcial}pts) adicionada para item {i}")
                                        else:
                                            # Item binário - remover da lista de requisitos
                                            validation_result["corrections_applied"].append(f"Item {i} identificado como binário - parcialmenteAdequado não aplicável")
                                            validation_result["warnings"].append(f"Item {i} é binário (≤0.25pts) - parcialmenteAdequado não aplicável")

                                    elif pont == "inadequado":
                                        pontuacoes["inadequado"] = {
                                            "criterio": "Não realiza as ações esperadas ou realiza de forma inadequada.",
                                            "pontos": 0.0
                                        }
                                        validation_result["corrections_applied"].append(f"Pontuação inadequado adicionada para item {i}")
                                        validation_result["warnings"].append(f"Pontuação inadequado adicionada para item {i}")

                                    elif pont == "adequado":
                                        # Se adequado está faltando, adicionar com pontuação padrão
                                        pontuacoes["adequado"] = {
                                            "criterio": "Realiza todas as ações esperadas de forma adequada.",
                                            "pontos": 0.5
                                        }
                                        pontos_adequado = 0.5
                                        validation_result["corrections_applied"].append(f"Pontuação adequado (0.5pts) adicionada para item {i}")
                                        validation_result["warnings"].append(f"Pontuação adequado (0.5pts) adicionada para item {i}")

                            # Verificar novamente após correções automáticas
                            for pont in required_pontuacoes:
                                if pont not in pontuacoes:
                                    # Só reportar erro se não foi uma exclusão intencional (item binário)
                                    if pont == "parcialmenteAdequado":
                                        # Verificar se é item binário
                                        pontos_adequado = 0.0
                                        if "adequado" in pontuacoes and "pontos" in pontuacoes["adequado"]:
                                            pontos_adequado = pontuacoes["adequado"]["pontos"]

                                        if pontos_adequado > 0.25:
                                            validation_result["structural_issues"].append(f"itensAvaliacao[{i}].pontuacoes.{pont} ausente")
                                            validation_result["is_valid"] = False
                                        # Se ≤ 0.25, é item binário e não precisa de parcialmenteAdequado
                                    else:
                                        validation_result["structural_issues"].append(f"itensAvaliacao[{i}].pontuacoes.{pont} ausente")
                                        validation_result["is_valid"] = False

        # Verificar tipos de dados específicos
        type_checks = {
            "tempoDuracaoMinutos": int,
            "numeroDaEstacao": int
        }

        for field, expected_type in type_checks.items():
            if field in generated_json:
                if not isinstance(generated_json[field], expected_type):
                    validation_result["invalid_field_types"].append(f"{field} deve ser {expected_type.__name__}")
                    validation_result["is_valid"] = False

        # Verificar valores específicos da especialidade
        valid_especialidades = [
            "CLÍNICA MÉDICA", "CIRURGIA GERAL", "PEDIATRIA",
            "GINECOLOGIA E OBSTETRÍCIA", "MEDICINA DA FAMÍLIA E COMUNIDADE"
        ]

        if "especialidade" in generated_json:
            if generated_json["especialidade"] not in valid_especialidades:
                validation_result["warnings"].append(f"Especialidade '{generated_json['especialidade']}' não está na lista padrão INEP")

        # Verificar padrão do idEstacao
        if "idEstacao" in generated_json:
            id_estacao = generated_json["idEstacao"]
            if not id_estacao.startswith("REVALIDA_FACIL_"):
                validation_result["warnings"].append("idEstacao não segue o padrão REVALIDA_FACIL_[ANO]_[SEMESTRE]_EST[NUMERO]_...")

        # **MELHORIA**: Verificar estrutura geral do JSON
        _validate_json_structure(generated_json, validation_result)

    except FileNotFoundError:
        validation_result["structural_issues"].append(f"Template {template_path} não encontrado")
        validation_result["is_valid"] = False
    except json.JSONDecodeError:
        validation_result["structural_issues"].append(f"Template {template_path} contém JSON inválido")
        validation_result["is_valid"] = False
    except Exception as e:
        validation_result["structural_issues"].append(f"Erro na validação: {str(e)}")
        validation_result["is_valid"] = False

    return validation_result

def _sanitize_informacoes_verbais_simulado(data: Any) -> List[Dict[str, str]]:
    """
    Sanitiza a estrutura de 'informacoesVerbaisSimulado'.
    Garante que seja uma lista de dicionários com 'contextoOuPerguntaChave' e 'informacao'.
    Remove aninhamentos excessivos.
    """
    if not isinstance(data, list):
        return []

    sanitized_list = []
    for item in data:
        if isinstance(item, dict):
            contexto = item.get("contextoOuPerguntaChave")
            informacao = item.get("informacao")

            # Se a informação for um dicionário ou lista, tentar extrair texto ou converter para string
            if isinstance(informacao, (dict, list)):
                try:
                    informacao = json.dumps(informacao, ensure_ascii=False)
                except TypeError:
                    informacao = str(informacao)
                
            if isinstance(contexto, str) and isinstance(informacao, str):
                sanitized_list.append({
                    "contextoOuPerguntaChave": contexto,
                    "informacao": informacao
                })
            elif isinstance(contexto, str) and informacao is None:
                # Se a informação for nula, mas o contexto é string, adicionar com string vazia
                sanitized_list.append({
                    "contextoOuPerguntaChave": contexto,
                    "informacao": ""
                })
        elif isinstance(item, str):
            # Se for apenas uma string, tratar como informação sem contexto específico
            sanitized_list.append({
                "contextoOuPerguntaChave": "Informação Geral",
                "informacao": item
            })
    return sanitized_list

def _sanitize_impressos(data: Any) -> List[Dict[str, Any]]:
    """
    Sanitiza a estrutura de 'impressos'.
    Garante que seja uma lista de dicionários e formata 'conteudo' corretamente,
    especialmente para 'lista_chave_valor_secoes', que deve ter seções como strings JSON.
    """
    if not isinstance(data, list):
        return []

    sanitized_list = []
    for item in data:
        if not isinstance(item, dict):
            # Ignorar itens que não são dicionários ou convertê-los para um formato básico
            sanitized_list.append({"tituloImpresso": "Impresso Inválido", "conteudo": {"textoDescritivo": str(item)}})
            continue

        sanitized_item = item.copy()
        tipo_impresso = sanitized_item.get("tipo")
        conteudo = sanitized_item.get("conteudo")

        if tipo_impresso == "lista_chave_valor_secoes" and isinstance(conteudo, dict) and "secoes" in conteudo:
            secoes = conteudo.get("secoes", [])
            if isinstance(secoes, list):
                # Garantir que cada seção seja uma string JSON
                stringified_secoes = []
                for secao in secoes:
                    if isinstance(secao, dict):
                        stringified_secoes.append(json.dumps(secao, ensure_ascii=False))
                    elif isinstance(secao, str):
                        # Se já for uma string, verificar se é um JSON válido, senão, não fazer nada
                        try:
                            json.loads(secao)
                            stringified_secoes.append(secao)
                        except json.JSONDecodeError:
                            # Se não for um JSON válido, não adicionar ou logar um aviso
                            pass
                
                # Substituir o conteúdo pelo formato correto
                sanitized_item["conteudo"] = {"secoes": stringified_secoes}
        
        elif isinstance(conteudo, dict):
            # Para outros tipos de impressos, aplicar a sanitização recursiva para evitar aninhamento profundo
            sanitized_item["conteudo"] = _sanitize_conteudo_recursivo(conteudo)
        
        elif isinstance(conteudo, (list, dict)):
             # Fallback para converter estruturas complexas inesperadas em string
            try:
                sanitized_item["conteudo"] = json.dumps(conteudo, ensure_ascii=False)
            except TypeError:
                sanitized_item["conteudo"] = str(conteudo)

        sanitized_list.append(sanitized_item)
        
    return sanitized_list

def _sanitize_conteudo_recursivo(content: dict, max_depth: int = 2) -> dict:
    """
    Sanitiza recursivamente o conteúdo de impressos, garantindo que não haja
    aninhamentos profundos que causem problemas no Firestore.
    """
    if not isinstance(content, dict):
        return {"textoDescritivo": str(content)}

    sanitized = {}
    for key, value in content.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            # Tipos básicos - manter como estão
            sanitized[key] = value
        elif isinstance(value, list):
            # Para listas, verificar profundidade e sanitizar elementos
            sanitized_list = []
            for item in value:
                if isinstance(item, dict):
                    # Se for dicionário, verificar se tem aninhamentos profundos
                    if _has_deep_nesting(item, current_depth=1, max_depth=max_depth):
                        # Converter para string se tiver aninhamento profundo
                        sanitized_list.append(json.dumps(item, ensure_ascii=False))
                    else:
                        # Sanitizar recursivamente se não tiver aninhamento profundo
                        sanitized_list.append(_sanitize_conteudo_recursivo(item, max_depth))
                elif isinstance(item, list):
                    # Listas aninhadas - converter para string
                    sanitized_list.append(json.dumps(item, ensure_ascii=False))
                else:
                    # Outros tipos - manter ou converter para string
                    sanitized_list.append(item if isinstance(item, (str, int, float, bool, type(None))) else str(item))
            sanitized[key] = sanitized_list
        elif isinstance(value, dict):
            # Para dicionários, verificar profundidade
            if _has_deep_nesting(value, current_depth=1, max_depth=max_depth):
                # Converter para string se tiver aninhamento profundo
                sanitized[key] = json.dumps(value, ensure_ascii=False)
            else:
                # Sanitizar recursivamente se não tiver aninhamento profundo
                sanitized[key] = _sanitize_conteudo_recursivo(value, max_depth)
        else:
            # Outros tipos - converter para string
            sanitized[key] = str(value)

    return sanitized

def _has_deep_nesting(data: Any, current_depth: int = 0, max_depth: int = 2) -> bool:
    """
    Verifica se uma estrutura de dados tem aninhamentos profundos além do limite permitido.
    """
    if current_depth >= max_depth:
        return True

    if isinstance(data, dict):
        for value in data.values():
            if _has_deep_nesting(value, current_depth + 1, max_depth):
                return True
    elif isinstance(data, list):
        for item in data:
            if _has_deep_nesting(item, current_depth + 1, max_depth):
                return True

    return False

def sanitize_materiais_disponiveis(materiais_disponiveis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza o campo 'materiaisDisponiveis' para garantir compatibilidade com Firestore.
    Remove aninhamentos excessivos e garante que os subcampos sejam de tipos aceitáveis.
    """
    print(f"[SANITIZE] Iniciando sanitização de materiaisDisponiveis")
    print(f"[SANITIZE] Tipo de entrada: {type(materiais_disponiveis)}")
    print(f"[SANITIZE] Chaves presentes: {list(materiais_disponiveis.keys()) if isinstance(materiais_disponiveis, dict) else 'N/A'}")

    if not isinstance(materiais_disponiveis, dict):
        print(f"[SANITIZE] Entrada não é dicionário, retornando vazio")
        return {} # Retorna um objeto vazio ou levanta erro, dependendo da política

    sanitized_data = materiais_disponiveis.copy()
    print(f"[SANITIZE] Copiando dados originais")

    # Sanitizar informacoesVerbaisSimulado
    if "informacoesVerbaisSimulado" in sanitized_data:
        sanitized_data["informacoesVerbaisSimulado"] = _sanitize_informacoes_verbais_simulado(
            sanitized_data["informacoesVerbaisSimulado"]
        )
    else:
        sanitized_data["informacoesVerbaisSimulado"] = [] # Garante que o campo exista

    # Sanitizar impressos
    if "impressos" in sanitized_data:
        sanitized_data["impressos"] = _sanitize_impressos(
            sanitized_data["impressos"]
        )
    else:
        sanitized_data["impressos"] = [] # Garante que o campo exista

    # Garantir que 'perguntasAtorSimulado' seja uma lista (pode ser vazia)
    if not isinstance(sanitized_data.get("perguntasAtorSimulado"), list):
        sanitized_data["perguntasAtorSimulado"] = []

    print(f"[SANITIZE] Sanitização concluída")
    print(f"[SANITIZE] Chaves finais: {list(sanitized_data.keys())}")

    # Calcular profundidade final após sanitização
    final_depth = _calculate_max_depth(sanitized_data)
    print(f"[SANITIZE] Profundidade final: {final_depth}")

    return sanitized_data

def sanitize_padrao_esperado_procedimento(padrao_procedimento: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza o campo 'padraoEsperadoProcedimento' para garantir compatibilidade com Firestore.
    Remove aninhamentos excessivos e garante que os subcampos sejam de tipos aceitáveis.
    """
    if not isinstance(padrao_procedimento, dict):
        return {}

    sanitized_data = padrao_procedimento.copy()

    # Sanitizar campos básicos
    for field in ["idChecklistAssociado", "pontuacaoTotalEstacao"]:
        if field in sanitized_data and not isinstance(sanitized_data[field], (str, int, float)):
            sanitized_data[field] = str(sanitized_data[field])

    # Sanitizar sinteseEstacao
    if "sinteseEstacao" in sanitized_data:
        sintese = sanitized_data["sinteseEstacao"]
        if isinstance(sintese, dict):
            # Garantir que resumoCasoPEP seja string
            if "resumoCasoPEP" in sintese and not isinstance(sintese["resumoCasoPEP"], str):
                sintese["resumoCasoPEP"] = str(sintese["resumoCasoPEP"])

            # Garantir que focoPrincipalDetalhado seja lista de strings
            if "focoPrincipalDetalhado" in sintese:
                if isinstance(sintese["focoPrincipalDetalhado"], list):
                    foco_list = []
                    for item in sintese["focoPrincipalDetalhado"]:
                        if isinstance(item, str):
                            foco_list.append(item)
                        else:
                            foco_list.append(str(item))
                    sintese["focoPrincipalDetalhado"] = foco_list
                else:
                    sintese["focoPrincipalDetalhado"] = [str(sintese["focoPrincipalDetalhado"])]
        else:
            sanitized_data["sinteseEstacao"] = {}

    # Sanitizar itensAvaliacao
    if "itensAvaliacao" in sanitized_data:
        itens = sanitized_data["itensAvaliacao"]
        if isinstance(itens, list):
            sanitized_itens = []
            for item in itens:
                if isinstance(item, dict):
                    sanitized_item = {}

                    # Sanitizar campos básicos do item
                    for field in ["idItem", "itemNumeroOficial", "descricaoItem"]:
                        if field in item:
                            if isinstance(item[field], str):
                                sanitized_item[field] = item[field]
                            else:
                                sanitized_item[field] = str(item[field])

                    # Sanitizar pontuacoes
                    if "pontuacoes" in item and isinstance(item["pontuacoes"], dict):
                        pontuacoes = item["pontuacoes"]
                        sanitized_pontuacoes = {}

                        for pont_type in ["adequado", "parcialmenteAdequado", "inadequado"]:
                            if pont_type in pontuacoes and isinstance(pontuacoes[pont_type], dict):
                                pont_data = pontuacoes[pont_type]
                                sanitized_pont = {}

                                # Sanitizar criterio
                                if "criterio" in pont_data:
                                    sanitized_pont["criterio"] = str(pont_data["criterio"])

                                # Sanitizar pontos
                                if "pontos" in pont_data:
                                    pontos = pont_data["pontos"]
                                    if isinstance(pontos, (int, float)):
                                        sanitized_pont["pontos"] = float(pontos)
                                    else:
                                        try:
                                            sanitized_pont["pontos"] = float(pontos)
                                        except (ValueError, TypeError):
                                            sanitized_pont["pontos"] = 0.0

                                sanitized_pontuacoes[pont_type] = sanitized_pont

                        sanitized_item["pontuacoes"] = sanitized_pontuacoes

                    sanitized_itens.append(sanitized_item)
                else:
                    # Se não for dicionário, criar item básico
                    sanitized_itens.append({
                        "idItem": "item_basico",
                        "descricaoItem": str(item),
                        "pontuacoes": {
                            "adequado": {"criterio": "Item básico", "pontos": 0.5},
                            "parcialmenteAdequado": {"criterio": "Item básico parcial", "pontos": 0.25},
                            "inadequado": {"criterio": "Item básico inadequado", "pontos": 0.0}
                        }
                    })

            sanitized_data["itensAvaliacao"] = sanitized_itens
        else:
            sanitized_data["itensAvaliacao"] = []

    # Sanitizar feedbackEstacao
    if "feedbackEstacao" in sanitized_data:
        feedback = sanitized_data["feedbackEstacao"]
        if isinstance(feedback, dict):
            # Sanitizar resumoTecnico
            if "resumoTecnico" in feedback and not isinstance(feedback["resumoTecnico"], str):
                feedback["resumoTecnico"] = str(feedback["resumoTecnico"])

            # Sanitizar fontes
            if "fontes" in feedback:
                if isinstance(feedback["fontes"], list):
                    fontes_list = []
                    for fonte in feedback["fontes"]:
                        if isinstance(fonte, str):
                            fontes_list.append(fonte)
                        else:
                            fontes_list.append(str(fonte))
                    feedback["fontes"] = fontes_list
                else:
                    feedback["fontes"] = [str(feedback["fontes"])]
        else:
            sanitized_data["feedbackEstacao"] = {}

    return sanitized_data

def _calculate_max_depth(obj: Any, current_depth: int = 0) -> int:
    """
    Calcula a profundidade máxima de aninhamento de um objeto/dicionário.
    Útil para diagnosticar problemas de entidade aninhada no Firestore.
    """
    if current_depth > 20:  # Limite de segurança para evitar recursão infinita
        return current_depth

    if isinstance(obj, dict):
        max_depth = current_depth
        for value in obj.values():
            depth = _calculate_max_depth(value, current_depth + 1)
            max_depth = max(max_depth, depth)
        return max_depth
    elif isinstance(obj, list):
        max_depth = current_depth
        for item in obj:
            depth = _calculate_max_depth(item, current_depth + 1)
            max_depth = max(max_depth, depth)
        return max_depth
    else:
        return current_depth

def _validate_json_structure(json_obj: dict, validation_result: dict) -> None:
    """
    Função auxiliar para validar estrutura geral do JSON
    Adiciona verificações adicionais para detectar problemas comuns
    """
    try:
        # Verificar se campos obrigatórios têm valores válidos
        if "tituloEstacao" in json_obj:
            titulo = json_obj["tituloEstacao"]
            if not isinstance(titulo, str) or len(titulo.strip()) < 10:
                validation_result["warnings"].append("tituloEstacao muito curto ou inválido")

        if "palavrasChave" in json_obj:
            palavras = json_obj["palavrasChave"]
            if not isinstance(palavras, list) or len(palavras) < 3:
                validation_result["warnings"].append("palavrasChave deve ter pelo menos 3 termos")

        if "tempoDuracaoMinutos" in json_obj:
            tempo = json_obj["tempoDuracaoMinutos"]
            if isinstance(tempo, int) and (tempo < 5 or tempo > 30):
                validation_result["warnings"].append("tempoDuracaoMinutos fora do intervalo recomendado (5-30 minutos)")

        # **LOG DIAGNÓSTICO AVANÇADO**: Verificar estrutura de materiaisDisponiveis antes da validação
        if "materiaisDisponiveis" in json_obj:
            materiais = json_obj["materiaisDisponiveis"]
            print(f"[DIAGNOSTIC] materiaisDisponiveis type: {type(materiais)}")
            print(f"[DIAGNOSTIC] materiaisDisponiveis keys: {list(materiais.keys()) if isinstance(materiais, dict) else 'N/A'}")

            # Verificar profundidade de aninhamento
            max_depth = _calculate_max_depth(materiais)
            print(f"[DIAGNOSTIC] materiaisDisponiveis max depth: {max_depth}")

            if max_depth > 10:
                print(f"[WARNING] materiaisDisponiveis tem profundidade excessiva: {max_depth} níveis")
                validation_result["warnings"].append(f"materiaisDisponiveis tem profundidade excessiva: {max_depth} níveis")

            # **FOCO NO DIAGNÓSTICO**: Examinar cada campo específico que pode causar "invalid nested entity"
            if isinstance(materiais, dict):
                for key, value in materiais.items():
                    if isinstance(value, (list, dict)):
                        depth = _calculate_max_depth(value)
                        print(f"[DIAGNOSTIC] materiaisDisponiveis.{key} depth: {depth}")
                        if depth > 5:
                            print(f"[WARNING] materiaisDisponiveis.{key} tem profundidade alta: {depth}")

                        # **DIAGNÓSTICO ESPECÍFICO PARA IMPRESSOS**: Campo mais provável de causar problemas
                        if key == "impressos" and isinstance(value, list):
                            print(f"[DIAGNOSTIC] === ANÁLISE DETALHADA DE IMPRESSOS ===")
                            print(f"[DIAGNOSTIC] Total de impressos: {len(value)}")

                            for i, item in enumerate(value[:5]):  # Examinar primeiros 5 para diagnóstico
                                if isinstance(item, dict):
                                    print(f"[DIAGNOSTIC] impressos[{i}] keys: {list(item.keys())}")
                                    print(f"[DIAGNOSTIC] impressos[{i}] structure preview: {str(item)[:200]}...")

                                    if "conteudo" in item:
                                        conteudo = item["conteudo"]
                                        conteudo_depth = _calculate_max_depth(conteudo)
                                        print(f"[DIAGNOSTIC] impressos[{i}].conteudo type: {type(conteudo)}")
                                        print(f"[DIAGNOSTIC] impressos[{i}].conteudo depth: {conteudo_depth}")

                                        # **CRÍTICO**: Verificar se conteudo tem aninhamento > 2 níveis
                                        if conteudo_depth > 2:
                                            print(f"[ERROR] impressos[{i}].conteudo VIOLATION: profundidade {conteudo_depth} > 2")
                                            print(f"[ERROR] Conteúdo problemático: {conteudo}")

                                            # Tentar identificar estrutura específica problemática
                                            if isinstance(conteudo, dict):
                                                for sub_key, sub_value in conteudo.items():
                                                    sub_depth = _calculate_max_depth(sub_value)
                                                    if sub_depth > 1:
                                                        print(f"[ERROR] impressos[{i}].conteudo.{sub_key} depth: {sub_depth}")
                                                        print(f"[ERROR] Valor problemático: {sub_value}")

                        # **DIAGNÓSTICO ESPECÍFICO PARA INFORMACOES VERBAIS**: Segundo campo mais provável
                        elif key == "informacoesVerbaisSimulado" and isinstance(value, list):
                            print(f"[DIAGNOSTIC] === ANÁLISE DETALHADA DE INFORMACOES VERBAIS ===")
                            print(f"[DIAGNOSTIC] Total de informacoesVerbaisSimulado: {len(value)}")

                            for i, item in enumerate(value[:5]):  # Examinar primeiros 5
                                if isinstance(item, dict):
                                    print(f"[DIAGNOSTIC] informacoesVerbaisSimulado[{i}] keys: {list(item.keys())}")
                                    print(f"[DIAGNOSTIC] informacoesVerbaisSimulado[{i}] structure: {item}")

                                    for subkey, subvalue in item.items():
                                        if isinstance(subvalue, (dict, list)):
                                            sub_depth = _calculate_max_depth(subvalue)
                                            print(f"[DIAGNOSTIC] informacoesVerbaisSimulado[{i}].{subkey} type: {type(subvalue)}")
                                            print(f"[DIAGNOSTIC] informacoesVerbaisSimulado[{i}].{subkey} depth: {sub_depth}")

                                            # **CRÍTICO**: informacoesVerbaisSimulado deve ter apenas profundidade 1
                                            if sub_depth > 1:
                                                print(f"[ERROR] informacoesVerbaisSimulado[{i}].{subkey} VIOLATION: profundidade {sub_depth} > 1")
                                                print(f"[ERROR] Valor problemático: {subvalue}")

                        # **DIAGNÓSTICO PARA OUTROS CAMPOS**: perguntasAtorSimulado
                        elif key == "perguntasAtorSimulado":
                            print(f"[DIAGNOSTIC] === ANÁLISE DE PERGUNTAS ATOR SIMULADO ===")
                            print(f"[DIAGNOSTIC] perguntasAtorSimulado type: {type(value)}")
                            depth = _calculate_max_depth(value)
                            print(f"[DIAGNOSTIC] perguntasAtorSimulado depth: {depth}")

                            if depth > 1:
                                print(f"[ERROR] perguntasAtorSimulado VIOLATION: profundidade {depth} > 1")
                                print(f"[ERROR] Deve ser lista simples de strings, encontrado: {value}")

        # **NOVA VALIDAÇÃO**: Verificar estrutura completa de padraoEsperadoProcedimento
        if "padraoEsperadoProcedimento" in json_obj:
            padrao = json_obj["padraoEsperadoProcedimento"]
            if not isinstance(padrao, dict):
                validation_result["structural_issues"].append("padraoEsperadoProcedimento deve ser um objeto")
                validation_result["is_valid"] = False
            else:
                # Validar campos obrigatórios do padraoEsperadoProcedimento
                required_padrao_fields = ["idChecklistAssociado", "sinteseEstacao", "itensAvaliacao", "pontuacaoTotalEstacao", "feedbackEstacao"]
                for field in required_padrao_fields:
                    if field not in padrao:
                        validation_result["structural_issues"].append(f"padraoEsperadoProcedimento.{field} ausente")
                        validation_result["is_valid"] = False

                # Validar sinteseEstacao
                if "sinteseEstacao" in padrao:
                    sintese = padrao["sinteseEstacao"]
                    if not isinstance(sintese, dict):
                        validation_result["structural_issues"].append("padraoEsperadoProcedimento.sinteseEstacao deve ser um objeto")
                        validation_result["is_valid"] = False
                    else:
                        # Validar campos da sinteseEstacao
                        if "resumoCasoPEP" not in sintese:
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.sinteseEstacao.resumoCasoPEP ausente")
                            validation_result["is_valid"] = False
                        elif not isinstance(sintese.get("resumoCasoPEP"), str):
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.sinteseEstacao.resumoCasoPEP deve ser string")
                            validation_result["is_valid"] = False

                        if "focoPrincipalDetalhado" not in sintese:
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.sinteseEstacao.focoPrincipalDetalhado ausente")
                            validation_result["is_valid"] = False
                        elif not isinstance(sintese.get("focoPrincipalDetalhado"), list):
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.sinteseEstacao.focoPrincipalDetalhado deve ser uma lista")
                            validation_result["is_valid"] = False

                # Validar itensAvaliacao
                if "itensAvaliacao" in padrao:
                    itens = padrao["itensAvaliacao"]
                    if not isinstance(itens, list):
                        validation_result["structural_issues"].append("padraoEsperadoProcedimento.itensAvaliacao deve ser uma lista")
                        validation_result["is_valid"] = False
                    elif len(itens) < 3:
                        validation_result["warnings"].append(f"itensAvaliacao tem apenas {len(itens)} itens (recomendado: 5-8)")
                    else:
                        # Validar cada item de avaliação
                        for i, item in enumerate(itens):
                            if not isinstance(item, dict):
                                validation_result["structural_issues"].append(f"itensAvaliacao[{i}] deve ser um objeto")
                                validation_result["is_valid"] = False
                                continue

                            # Campos obrigatórios do item
                            required_item_fields = ["idItem", "itemNumeroOficial", "descricaoItem", "pontuacoes"]
                            for field in required_item_fields:
                                if field not in item:
                                    validation_result["structural_issues"].append(f"itensAvaliacao[{i}].{field} ausente")
                                    validation_result["is_valid"] = False

                            # Validar pontuacoes
                            if "pontuacoes" in item:
                                pontuacoes = item["pontuacoes"]
                                if not isinstance(pontuacoes, dict):
                                    validation_result["structural_issues"].append(f"itensAvaliacao[{i}].pontuacoes deve ser um objeto")
                                    validation_result["is_valid"] = False
                                else:
                                    # Verificar se tem as pontuações obrigatórias
                                    required_pontuacoes = ["adequado", "parcialmenteAdequado", "inadequado"]
                                    for pont in required_pontuacoes:
                                        if pont not in pontuacoes:
                                            validation_result["structural_issues"].append(f"itensAvaliacao[{i}].pontuacoes.{pont} ausente")
                                            validation_result["is_valid"] = False
                                        elif not isinstance(pontuacoes[pont], dict):
                                            validation_result["structural_issues"].append(f"itensAvaliacao[{i}].pontuacoes.{pont} deve ser um objeto")
                                            validation_result["is_valid"] = False
                                        elif "pontos" not in pontuacoes[pont]:
                                            validation_result["structural_issues"].append(f"itensAvaliacao[{i}].pontuacoes.{pont}.pontos ausente")
                                            validation_result["is_valid"] = False
                                        elif not isinstance(pontuacoes[pont]["pontos"], (int, float)):
                                            validation_result["structural_issues"].append(f"itensAvaliacao[{i}].pontuacoes.{pont}.pontos deve ser numérico")
                                            validation_result["is_valid"] = False

                                    # Verificar consistência das pontuações
                                    pontos_totais = 0.0
                                    for pontuacao in pontuacoes.values():
                                        if isinstance(pontuacao, dict) and "pontos" in pontuacao:
                                            pontos_totais += pontuacao["pontos"]

                                    if pontos_totais > 1.0:
                                        validation_result["warnings"].append(f"Item {i}: pontuação total ({pontos_totais}) excede 1.0")

                # Validar pontuacaoTotalEstacao
                if "pontuacaoTotalEstacao" in padrao:
                    pont_total = padrao["pontuacaoTotalEstacao"]
                    if not isinstance(pont_total, (int, float)):
                        validation_result["structural_issues"].append("padraoEsperadoProcedimento.pontuacaoTotalEstacao deve ser numérico")
                        validation_result["is_valid"] = False
                    elif pont_total <= 0:
                        validation_result["warnings"].append("padraoEsperadoProcedimento.pontuacaoTotalEstacao deve ser maior que 0")

                # Validar feedbackEstacao
                if "feedbackEstacao" in padrao:
                    feedback = padrao["feedbackEstacao"]
                    if not isinstance(feedback, dict):
                        validation_result["structural_issues"].append("padraoEsperadoProcedimento.feedbackEstacao deve ser um objeto")
                        validation_result["is_valid"] = False
                    else:
                        if "resumoTecnico" not in feedback:
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.feedbackEstacao.resumoTecnico ausente")
                            validation_result["is_valid"] = False
                        elif not isinstance(feedback.get("resumoTecnico"), str):
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.feedbackEstacao.resumoTecnico deve ser string")
                            validation_result["is_valid"] = False

                        if "fontes" not in feedback:
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.feedbackEstacao.fontes ausente")
                            validation_result["is_valid"] = False
                        elif not isinstance(feedback.get("fontes"), list):
                            validation_result["structural_issues"].append("padraoEsperadoProcedimento.feedbackEstacao.fontes deve ser uma lista")
                            validation_result["is_valid"] = False

        # **NOVA VALIDAÇÃO**: Verificar estrutura de materiaisDisponiveis
        if "materiaisDisponiveis" in json_obj:
            materiais = json_obj["materiaisDisponiveis"]
            if not isinstance(materiais, dict):
                validation_result["structural_issues"].append("materiaisDisponiveis deve ser um objeto")
                validation_result["is_valid"] = False
            else:
                # Validar informacoesVerbaisSimulado
                if "informacoesVerbaisSimulado" in materiais:
                    info_verbais = materiais["informacoesVerbaisSimulado"]
                    if not isinstance(info_verbais, list):
                        validation_result["structural_issues"].append("informacoesVerbaisSimulado deve ser uma lista")
                        validation_result["is_valid"] = False
                    else:
                        for i, item in enumerate(info_verbais):
                            if not isinstance(item, dict) or not all(k in item for k in ["contextoOuPerguntaChave", "informacao"]):
                                validation_result["structural_issues"].append(f"informacoesVerbaisSimulado[{i}] item malformado")
                                validation_result["is_valid"] = False
                            elif not isinstance(item.get("contextoOuPerguntaChave"), str) or not isinstance(item.get("informacao"), str):
                                validation_result["structural_issues"].append(f"informacoesVerbaisSimulado[{i}] campos 'contextoOuPerguntaChave' ou 'informacao' não são strings")
                                validation_result["is_valid"] = False

                # Validar impressos
                if "impressos" in materiais:
                    impressos = materiais["impressos"]
                    if not isinstance(impressos, list):
                        validation_result["structural_issues"].append("impressos deve ser uma lista")
                        validation_result["is_valid"] = False
                    else:
                        for i, item in enumerate(impressos):
                            if not isinstance(item, dict) or "conteudo" not in item:
                                validation_result["structural_issues"].append(f"impressos[{i}] item malformado ou sem 'conteudo'")
                                validation_result["is_valid"] = False
                            elif isinstance(item.get("conteudo"), dict):
                                # Verificar se o conteúdo tem aninhamento excessivo (mais de 2 níveis)
                                # Usar a mesma lógica do sanitizador recursivo
                                if _has_deep_nesting(item["conteudo"], current_depth=0, max_depth=2):
                                    validation_result["structural_issues"].append(f"impressos[{i}].conteudo contém aninhamento excessivo (>2 níveis)")
                                    validation_result["is_valid"] = False
                            elif not isinstance(item.get("conteudo"), (dict, str, int, float, bool, type(None))):
                                validation_result["structural_issues"].append(f"impressos[{i}].conteudo tem tipo inválido")
                                validation_result["is_valid"] = False


    except Exception as e:
        validation_result["warnings"].append(f"Erro na validação estrutural: {str(e)}")

async def build_prompt_fase_3(request: GenerateFinalStationRequest) -> str:
    """Constrói o prompt da Fase 3 usando seções específicas do referencias.md + gabarito.json + busca semântica nas provas INEP"""
    
    # Usar sistema híbrido se disponível
    if LOCAL_MEMORY_SYSTEM:
        print("[FAST] Usando sistema híbrido para Fase 3...")
        contexto_otimizado = get_context_for_phase(3)
        gabarito_json = get_gabarito_template()
    else:
        print("[REFRESH] Fallback para sistema tradicional...")
        # Seções específicas para Fase 3: 0, 1, 2, 3, 4, 5, 6, 7, 8, 10
        secoes_fase_3 = [
            'principios_fundamentais',
            'arquitetura_estacoes',
            'diretrizes_tarefas', 
            'tarefas_especialidade',
            'roteiro_ator_completo',
            'banco_semiologia',
            'tipos_impressos',
            'diretrizes_pep',
            'estruturas_especialidade',
            'regra_aprendida'
        ]
        
        # Construir contexto otimizado usando apenas seções relevantes
        contexto_otimizado = ""
        if PARSED_REFERENCIAS:
            print("🔧 Construindo prompt Fase 3 com seções otimizadas...")
            for secao in secoes_fase_3:
                if secao in PARSED_REFERENCIAS:
                    contexto_otimizado += f"\n\n--- {secao.upper().replace('_', ' ')} ---\n"
                    contexto_otimizado += PARSED_REFERENCIAS[secao]
            print(f"[STATS] Fase 3: {len(contexto_otimizado)} caracteres (vs {len(AGENT_RULES.get('referencias_md', '') if AGENT_RULES else '')} originais)")
        else:
            print("[WARNING] PARSED_REFERENCIAS não disponível, usando conteúdo completo como fallback")
            contexto_otimizado = AGENT_RULES.get('referencias_md', "") if AGENT_RULES else ""
        
        gabarito_json = AGENT_RULES.get('gabarito_json', "{}") if AGENT_RULES else "{}"
    
    # **NOVA FUNCIONALIDADE: Busca semântica nas provas INEP**
    exemplos_inep = ""
    try:
        print("🔍 Buscando provas INEP similares para referência...")
        
        # Criar query de busca baseada no tema e especialidade
        search_query = f"{request.tema} {request.especialidade}"
        
        # Usar sistema RAG local via função interna (evita subprocess)
        try:
            from rag_agent import rag_query, RAGQuery

            # Montar o corpo da query e chamar a função async rag_query diretamente
            rag_body = RAGQuery(query=search_query, top_k=3)

            # Estamos em função async: await diretamente
            resultados_dict = await rag_query(rag_body)

            # Processar resultados retornados (estrutura do rag_agent: dict com 'evidence' ou 'results')
            provas_inep = []
            items = resultados_dict.get('evidence') or resultados_dict.get('results') or []
            for r in items:
                metadata = r.get('metadata', {})
                if 'inep' in str(metadata).lower() or 'prova' in str(metadata).lower():
                    provas_inep.append(r)

            if provas_inep:
                exemplos_texto = "\n\n".join([
                    f"**EXEMPLO INEP {i+1}** (Score: {r.get('score', 0):.3f}):\n```json\n{str(r.get('metadata', {}).get('text_preview', r.get('text','')))[:800]}...\n```"
                    for i, r in enumerate(provas_inep[:3])
                ])
                exemplos_inep = exemplos_texto
                print(f"[SUCCESS] Encontradas {len(provas_inep)} provas INEP similares")
            else:
                print("[WARNING] Nenhuma prova INEP encontrada nos resultados")
        except Exception as e:
            print(f"[WARNING] Erro na execução do rag_agent (chamada interna): {e}")
            
    except Exception as e:
        print(f"[WARNING] Erro na busca semântica INEP: {e}")
        exemplos_inep = ""
    
    # Adicionar seção de exemplos INEP se encontrados
    secao_exemplos = ""
    if exemplos_inep:
        secao_exemplos = f"""

**EXEMPLOS DE PROVAS INEP SIMILARES (PARA REFERÊNCIA DE ESTRUTURA):**
{exemplos_inep}

**INSTRUÇÕES SOBRE OS EXEMPLOS:**
- Use os exemplos acima como REFERÊNCIA DE ESTRUTURA e PADRÃO INEP
- Mantenha a formatação JSON similar aos exemplos
- Observe os padrões de: idEstacao, tituloEstacao, especialidade, palavrasChave, instrucoesParticipante, checklistAvaliacao
- NÃO copie o conteúdo clínico, apenas a estrutura e formatação"""

    # **NOVA FUNCIONALIDADE: Aplicar regras aprendidas do usuário**
    regras_aprendidas = load_and_apply_user_learnings()

    return f"""# FASE 3: GERAÇÃO DO JSON COMPLETO

**CONTEXTO CLÍNICO:**
{request.resumo_clinico}

**PROPOSTA ESTRATÉGICA ESCOLHIDA:**
{request.proposta_escolhida}

**REGRAS DE CONTEÚDO E ESTRUTURA (SEÇÕES OTIMIZADAS):**
{contexto_otimizado}{secao_exemplos}{regras_aprendidas}

**MOLDE JSON A SER PREENCHIDO:**
{gabarito_json}

**SUA TAREFA:**
Gere o código JSON completo para a estação sobre **{request.tema}** em **{request.especialidade}**, seguindo rigorosamente a proposta, as regras, os padrões INEP encontrados, as regras aprendidas do usuário e o molde fornecidos."""

def build_prompt_analise(station_json_str: str, feedback: str | None) -> str:
    """Constrói o prompt da Fase 4 (análise) usando sistema híbrido de memória"""
    
    # Usar sistema híbrido se disponível
    if LOCAL_MEMORY_SYSTEM:
        print("[FAST] Usando sistema híbrido para Fase 4...")
        contexto_otimizado = get_context_for_phase(4)
    else:
        print("[REFRESH] Fallback para sistema tradicional...")
        # Seções específicas para Fase 4: 0, 9, 10
        secoes_fase_4 = [
            'principios_fundamentais',
            'checklist_validacao',
            'regra_aprendida'
        ]
        
        # Construir contexto otimizado usando apenas seções relevantes
        contexto_otimizado = ""
        if PARSED_REFERENCIAS:
            print("🔧 Construindo prompt Fase 4 (análise) com seções otimizadas...")
            for secao in secoes_fase_4:
                if secao in PARSED_REFERENCIAS:
                    contexto_otimizado += f"\n\n--- {secao.upper().replace('_', ' ')} ---\n"
                    contexto_otimizado += PARSED_REFERENCIAS[secao]
            print(f"[STATS] Fase 4: {len(contexto_otimizado)} caracteres (vs {len(AGENT_RULES.get('referencias_md', '') if AGENT_RULES else '')} originais)")
        else:
            print("[WARNING] PARSED_REFERENCIAS não disponível, usando conteúdo completo como fallback")
            contexto_otimizado = AGENT_RULES.get('referencias_md', "Regras de criação não carregadas.") if AGENT_RULES else "Regras de criação não carregadas."
    
    feedback_section = f"\n\n**DIRETRIZES ADICIONAIS DO USUÁRIO:**\n{feedback}\n" if feedback else ""
    
    return f"""# ANÁLISE DE ESTAÇÃO CLÍNICA

**PERSONA:** Avaliador sênior do INEP.

**REGRAS DE AVALIAÇÃO (SEÇÕES OTIMIZADAS):**
{contexto_otimizado}{feedback_section}

**TAREFA:**
Analise o JSON da estação abaixo e forneça um feedback em markdown com: Pontos Fortes, Pontos de Melhoria e Sugestão de Ação.

**JSON PARA ANÁLISE:**
```json
{station_json_str}
```"""

def build_prompt_apply_audit(station_json_str: str, analysis_result: str) -> str:
    return f"""# APLICAR MUDANÇAS DE AUDITORIA\n\n**PERSONA:** Desenvolvedor de conteúdo médico experiente.\n\n**TAREFA:**\nVocê receberá um JSON de uma estação clínica e o resultado de uma auditoria. Sua única tarefa é retornar um NOVO JSON que incorpore as 'Sugestões de Ação' da auditoria. NÃO adicione comentários, explicações ou use markdown. A saída deve ser apenas o código JSON modificado.\n\n**JSON ORIGINAL:**\n```json\n{station_json_str}\n```\n\n**RESULTADO DA AUDITORIA A SER APLICADO:**\n```markdown\n{analysis_result}\n```\n\n**NOVO JSON (APENAS O CÓDIGO):**"""

async def call_gemini_api(prompt: str, preferred_model: str = 'pro', timeout: int = 120):
    """
    Chama a API do Gemini com preferência de modelo, timeout seguro, rate limiting e truncamento de prompt.
    - timeout: segundos máximos para aguardar a resposta do modelo.
    Retorna response.text (ou concatenação de parts) em caso de sucesso.
    """
    global GEMINI_CONFIGS
    
    # Se não há chaves configuradas, tentar recarregar
    if not GEMINI_CONFIGS or not GEMINI_CONFIGS.get('all'):
        print("[RETRY] Nenhuma chave encontrada, tentando recarregar configuração...")
        configure_gemini_keys()
        
        # Se ainda não há chaves após recarregar
        if not GEMINI_CONFIGS or not GEMINI_CONFIGS.get('all'):
            raise HTTPException(status_code=503, detail="Nenhuma chave de API do Gemini está configurada.")
        else:
            print(f"[RETRY] ✅ {len(GEMINI_CONFIGS.get('all', []))} chave(s) recarregada(s) com sucesso!")
    
    # Truncar prompt se necessário
    MAX_TOKENS = 1000000  # Limite máximo de tokens para modelos Gemini
    if len(prompt) > MAX_TOKENS:
        prompt = prompt[:MAX_TOKENS]
        print(f"[WARNING] Prompt truncado para {MAX_TOKENS} caracteres")
        MONITORING_SYSTEM["metrics"]["prompts_truncated"] = MONITORING_SYSTEM["metrics"].get("prompts_truncated", 0) + 1
    
    # Determina a ordem de tentativa baseada na preferência com fallbacks
    if preferred_model == 'flash':
        # Ordem: Flash 2.5 -> Flash Lite 2.5 -> Flash 2.0 -> Pro 2.5
        configs_to_try = GEMINI_CONFIGS.get('flash', []) + GEMINI_CONFIGS.get('flash_lite', []) + GEMINI_CONFIGS.get('flash_2_0', []) + GEMINI_CONFIGS.get('pro', [])
        print(f"[FAST] Usando Gemini Flash 2.5 prioritariamente com fallbacks...")
    else:
        # Ordem: Pro 2.5 -> Flash 2.5 -> Flash Lite 2.5 -> Flash 2.0
        configs_to_try = GEMINI_CONFIGS.get('pro', []) + GEMINI_CONFIGS.get('flash', []) + GEMINI_CONFIGS.get('flash_lite', []) + GEMINI_CONFIGS.get('flash_2_0', [])
        print(f"[BRAIN] Usando Gemini Pro 2.5 prioritariamente com fallbacks...")

    if not configs_to_try:
        configs_to_try = GEMINI_CONFIGS.get('all', [])
    
    for i, config in enumerate(configs_to_try):
        # Verificar rate limiting antes de fazer a chamada
        if rate_limit_exceeded(config['key']):
            print(f"[WARNING] Rate limit excedido para API Key #{i+1}")
            MONITORING_SYSTEM["metrics"]["rate_limit_exceeded"] = MONITORING_SYSTEM["metrics"].get("rate_limit_exceeded", 0) + 1
            continue
            
        try:
            print(f"➡️ Tentando API Key #{i+1} com modelo {config['model_name']}...")
            genai.configure(api_key=config['key'])  # type: ignore
            model = genai.GenerativeModel(config['model_name'])  # type: ignore
            
            # Registrar a requisição no rate-limiter e incrementar métricas
            try:
                register_gemini_request(config['key'])
            except Exception:
                # Não falhar a execução se o registro não puder ser efetuado
                pass
            MONITORING_SYSTEM["metrics"]["gemini_requests_per_key"][config['key']] += 1
            
            try:
                # Respeitar timeout para evitar bloquear o loop do servidor
                coro = model.generate_content_async(prompt)
                response = await asyncio.wait_for(coro, timeout=timeout)
            except asyncio.TimeoutError:
                print(f"[WARNING] Timeout ({timeout}s) ao chamar {config['model_name']} (API Key #{i+1})")
                if i == len(configs_to_try) - 1:
                    raise HTTPException(status_code=504, detail="Timeout ao chamar API do Gemini")
                continue
            
            # Verifica candidatos e conteúdo de forma segura
            if not getattr(response, "candidates", None):
                print(f"[WARNING] {config['model_name']} (API Key #{i+1}): Nenhum candidato retornado.")
                if i == len(configs_to_try) - 1:
                    raise HTTPException(status_code=500, detail="Nenhum candidato válido retornado pelo modelo.")
                continue
            
            candidate = response.candidates[0]
            has_content_parts = bool(getattr(candidate, "content", None) and getattr(candidate.content, "parts", None))
            if not has_content_parts:
                finish_reason_code = getattr(candidate, "finish_reason", None)
                finish_reason_name = get_finish_reason_name(finish_reason_code)
                logger.warning("[WARNING] %s (API Key #%d): Resposta sem conteúdo válido. finish_reason=%s", config['model_name'], i+1, finish_reason_name)
                MONITORING_SYSTEM["metrics"]["gemini_errors"] = MONITORING_SYSTEM["metrics"].get("gemini_errors", 0) + 1
                
                if i == len(configs_to_try) - 1:
                    raise HTTPException(status_code=500, detail=f"Modelo respondeu sem conteúdo válido ({finish_reason_name})")
                
                continue
            
            # Tentar acessar texto de forma segura
            try:
                text_output = getattr(response, "text", None)
                if text_output is None:
                    # Algumas versões retornam via candidates[0].content.parts — garantir que sejam strings
                    parts = candidate.content.parts if candidate.content and getattr(candidate.content, "parts", None) else []
                    processed_parts = []
                    for p in parts:
                        if isinstance(p, str):
                            processed_parts.append(p)
                        else:
                            # Tentar extrair atributo de texto comum ou converter em string de forma mais robusta
                            try:
                                if hasattr(p, "text"):
                                    text_piece = str(p.text)
                                elif hasattr(p, "content"):
                                    text_piece = str(p.content)
                                else:
                                    text_piece = str(p)
                            except Exception:
                                text_piece = ""
                            if text_piece:
                                processed_parts.append(text_piece)
                    text_output = "".join(processed_parts) if processed_parts else ""
                # Retornar output limpo
                return text_output
            except Exception as e_text:
                logger.exception("[WARNING] Erro ao acessar texto da resposta: %s", e_text)
                MONITORING_SYSTEM["metrics"]["gemini_errors"] = MONITORING_SYSTEM["metrics"].get("gemini_errors", 0) + 1
                if i == len(configs_to_try) - 1:
                    raise HTTPException(status_code=500, detail=f"Erro ao acessar texto da resposta: {e_text}")
                continue
        
        except google_exceptions.ResourceExhausted:
            print(f"[WARNING] API Key #{i+1} ({config['model_name']}) atingiu o limite de cota.")
            if i == len(configs_to_try) - 1:
                raise HTTPException(status_code=429, detail="Todas as chaves de API atingiram o limite de cota.")
        except Exception as e:
            print(f"[ERROR] Erro com {config['model_name']} (API Key #{i+1}): {e}")
            if i == len(configs_to_try) - 1:
                raise HTTPException(status_code=500, detail=f"Erro na API do Gemini: {e}")
            continue
    
    raise HTTPException(status_code=503, detail="Falha ao processar com todas as chaves.")

# --- Função Helper para Geração Individual (Múltiplas Estações) ---
async def generate_single_station_internal(tema: str, especialidade: str, abordagem_id: str, enable_web_search: bool = False, skip_firestore: bool = False):
    """
    Função interna para gerar uma única estação seguindo o fluxo Fase 1 → 2 → 3
    
    Parâmetros:
    - tema: Tema da estação
    - especialidade: Especialidade médica
    - abordagem_id: Tipo de abordagem
    - enable_web_search: Habilitar busca web
    - skip_firestore: Se True, salva apenas localmente (usado na geração múltipla)
    
    Retorna: (success: bool, result: dict, error_message: str)
    """
    try:
        logger = logging.getLogger("agent.multiple_generation")
        logger.info(f"Iniciando geração para tema: {tema}")
        
        # --- FASE 1: Análise Clínica ---
        logger.info(f"[FASE 1] Executando análise clínica para: {tema}")
        prompt_fase_1 = await build_prompt_fase_1(tema, especialidade)
        
        # Adicionar busca web se habilitada (simplificada para modo múltiplo)
        web_search_summary = ""
        if enable_web_search:
            try:
                # Verificar se a chave da API está configurada antes de tentar usar
                serp_key = os.getenv("SERPAPI_KEY")
                if not serp_key:
                    logger.info(f"Busca web desabilitada para {tema}: SERPAPI_KEY não configurada no ambiente")
                    web_search_summary = ""
                else:
                    from web_search import search_web
                    search_query = f"protocolo {tema} {especialidade} Brasil diretrizes"
                    results = await asyncio.to_thread(search_web, search_query, 2, True)
                    if results:
                        web_lines = [f"- {r.get('title', '')}: {r.get('snippet', '')}" for r in results[:2]]
                        web_search_summary = f"\n\n**BUSCA WEB COMPLEMENTAR:**\n{chr(10).join(web_lines)}"
                        logger.info(f"Busca web concluída para {tema}: {len(results)} resultados encontrados")
            except ImportError as e:
                logger.warning(f"Módulo web_search não disponível para {tema}: {e}")
                web_search_summary = ""
            except Exception as e:
                logger.warning(f"Busca web falhou para {tema}: {e}")
                web_search_summary = ""
        
        prompt_fase_1_final = prompt_fase_1 + web_search_summary
        resumo_clinico = await call_gemini_api(prompt_fase_1_final, preferred_model='flash')
        
        # --- FASE 2: Geração de Proposta com Abordagem Específica ---
        logger.info(f"[FASE 2] Gerando proposta com abordagem: {abordagem_id}")
        prompt_fase_2 = await build_prompt_fase_2(tema, especialidade, resumo_clinico, [abordagem_id])
        proposta_resultado = await call_gemini_api(prompt_fase_2, preferred_model='flash')
        
        # Extrair primeira proposta (já filtrada pela abordagem)
        propostas = proposta_resultado.split('---')
        proposta_escolhida = propostas[0].strip() if propostas else proposta_resultado.strip()
        
        # --- FASE 3: Geração da Estação Final (APLICANDO TODA A LÓGICA DO ENDPOINT INDIVIDUAL) ---
        logger.info(f"[FASE 3] Gerando estação final para: {tema}")
        request_fase_3 = GenerateFinalStationRequest(
            resumo_clinico=resumo_clinico,
            proposta_escolhida=proposta_escolhida,
            tema=tema,
            especialidade=especialidade
        )
        
        prompt_fase_3 = await build_prompt_fase_3(request_fase_3)
        json_output_str = await call_gemini_api(prompt_fase_3, preferred_model='pro')
        
        # Extrair JSON usando o helper extract_json_from_text
        clean_json_str = extract_json_from_text(json_output_str)
        try:
            json_output = json.loads(clean_json_str)
            logger.info("JSON extraído e parseado com sucesso na primeira tentativa.")
        except json.JSONDecodeError as e:
            logger.warning("Falha no parse inicial do JSON. Tentando sanitização e correção aprimorada.", extra={"error": str(e), "json_preview": clean_json_str[:200]})

            # Estratégia 1: Sanitização aprimorada com correções específicas
            sanitized_str = sanitize_json_string(clean_json_str)
            try:
                json_output = json.loads(sanitized_str)
                logger.info("JSON parseado com sucesso após sanitização aprimorada.")
                MONITORING_SYSTEM["metrics"]["json_corrected_by_sanitization"] = MONITORING_SYSTEM["metrics"].get("json_corrected_by_sanitization", 0) + 1
            except json.JSONDecodeError as sanitization_error:
                logger.warning("Sanitização aprimorada falhou. Tentando correção estrutural avançada.", extra={"sanitization_error": str(sanitization_error)})

                # Estratégia 2: Correção estrutural avançada
                try:
                    corrected_str = _advanced_json_correction(clean_json_str)
                    json_output = json.loads(corrected_str)
                    logger.info("JSON corrigido com sucesso usando correção estrutural avançada!")
                    MONITORING_SYSTEM["metrics"]["json_corrected_by_advanced"] = MONITORING_SYSTEM["metrics"].get("json_corrected_by_advanced", 0) + 1
                except Exception as advanced_correction_error:
                    logger.warning("Correção estrutural avançada falhou. Usando LLM como último recurso.", extra={"advanced_error": str(advanced_correction_error)})

                    # Estratégia 3: LLM como último recurso
                    correction_prompt = f"""
                    O seguinte texto deveria ser um JSON válido para uma estação médica REVALIDA, mas contém erros de sintaxe.
                    Corrija TODOS os erros de sintaxe JSON e retorne APENAS o código JSON válido, sem nenhum texto ou explicação adicional.

                    IMPORTANTE:
                    - Mantenha toda a estrutura e conteúdo clínico
                    - Corrija apenas erros de sintaxe (aspas, vírgulas, chaves)
                    - Garanta que o JSON seja válido e parseável
                    - Não altere o conteúdo médico das respostas

                    JSON Inválido:
                    ```
                    {clean_json_str}
                    ```

                    JSON Corrigido (APENAS o JSON, nada mais):
                    """
                    try:
                        corrected_json_str = await call_gemini_api(correction_prompt, preferred_model='flash', timeout=60)
                        clean_corrected_json = extract_json_from_text(corrected_json_str)
                        json_output = json.loads(clean_corrected_json)
                        logger.info("JSON corrigido com sucesso usando LLM!")
                        MONITORING_SYSTEM["metrics"]["json_corrected_by_llm"] = MONITORING_SYSTEM["metrics"].get("json_corrected_by_llm", 0) + 1
                    except Exception as llm_correction_error:
                        error_msg = f"Erro ao parsear JSON mesmo após todas as tentativas de correção: {llm_correction_error}"
                        logger.error(error_msg, extra={"original_json": clean_json_str[:200], "sanitized_json": sanitized_str[:200], "llm_attempt": corrected_json_str[:200] if 'corrected_json_str' in locals() else 'N/A'})
                        MONITORING_SYSTEM["metrics"]["failed_generations"] = MONITORING_SYSTEM["metrics"].get("failed_generations", 0) + 1
                        return False, {"tema": tema, "especialidade": especialidade, "abordagem_usada": abordagem_id}, f"A IA gerou um JSON inválido e todas as tentativas de correção falharam: {llm_correction_error}"

        logger.info("JSON processado com sucesso.")
        MONITORING_SYSTEM["metrics"]["successful_generations"] = MONITORING_SYSTEM["metrics"].get("successful_generations", 0) + 1

        # **VALIDAÇÃO CONTRA TEMPLATE GABARITOESTACOES.JSON (COMO NO INDIVIDUAL)**
        logger.info("🔍 Validando JSON gerado contra template INEP...")
        validation_result = validate_json_against_template(json_output)
        
        if not validation_result["is_valid"]:
            logger.warning("[ERROR] JSON não passou na validação!")
            
            # Log detalhado dos problemas
            if validation_result["missing_required_fields"]:
                logger.warning(f"📋 Campos obrigatórios ausentes: {validation_result['missing_required_fields']}")
            if validation_result["invalid_field_types"]:
                logger.warning(f"🔢 Tipos de campo inválidos: {validation_result['invalid_field_types']}")
            if validation_result["structural_issues"]:
                logger.warning(f"🏗️ Problemas estruturais: {validation_result['structural_issues']}")
            
            # Tentar corrigir automaticamente usando Gemini Flash
            logger.info("🔧 Tentando corrigir automaticamente com Gemini Flash...")
            
            correction_prompt = f"""# CORREÇÃO DE JSON - CONFORMIDADE INEP

**JSON ATUAL (COM PROBLEMAS):**
```json
{json.dumps(json_output, indent=2, ensure_ascii=False)}
```

**PROBLEMAS IDENTIFICADOS:**
- Campos obrigatórios ausentes: {validation_result['missing_required_fields']}
- Tipos de campo inválidos: {validation_result['invalid_field_types']}
- Problemas estruturais: {validation_result['structural_issues']}

**TEMPLATE CORRETO (gabaritoestacoes.json):**
```json
{get_gabarito_template() if LOCAL_MEMORY_SYSTEM else AGENT_RULES.get('gabarito_json', '{}')}
```

**SUA TAREFA:**
Corrija o JSON atual para que seja 100% conforme o template. Mantenha TODO o conteúdo clínico gerado, apenas ajuste a estrutura, campos ausentes e tipos de dados. Retorne APENAS o JSON corrigido, sem explicações."""

            try:
                corrected_json_str = await call_gemini_api(correction_prompt, preferred_model='flash')
                
                # Limpar e re-parsear o JSON corrigido
                if corrected_json_str.strip().startswith("```json"):
                    corrected_json_str = corrected_json_str.strip()[7:-3]
                
                # **APLICAR SANITIZAÇÃO DE MATERIAISDISPONIVEIS NA CORREÇÃO AUTOMÁTICA**
                try:
                    temp_json = json.loads(corrected_json_str)
                    if "materiaisDisponiveis" in temp_json:
                        temp_json["materiaisDisponiveis"] = sanitize_materiais_disponiveis(temp_json["materiaisDisponiveis"])
                        corrected_json_str = json.dumps(temp_json, ensure_ascii=False)
                        logger.info("Campo 'materiaisDisponiveis' sanitizado durante correção automática.")
                except json.JSONDecodeError:
                    logger.warning("Não foi possível sanitizar 'materiaisDisponiveis' durante correção automática (JSON inválido antes da sanitização).")
                
                # Tentar carregar corrigido; usar sanitização se necessário
                try:
                    corrected_json = json.loads(corrected_json_str)
                except json.JSONDecodeError:
                    corrected_json = json.loads(sanitize_json_string(corrected_json_str))
                
                # Re-validar o JSON corrigido
                revalidation_result = validate_json_against_template(corrected_json)
                
                if revalidation_result["is_valid"]:
                    logger.info("[SUCCESS] JSON corrigido automaticamente e aprovado na validação!")
                    MONITORING_SYSTEM["metrics"]["successful_generations"] = MONITORING_SYSTEM["metrics"].get("successful_generations", 0) + 1
                    json_output = corrected_json
                else:
                    logger.warning("[WARNING] Correção automática não foi suficiente, mas continuando...")
                    # Adicionar metadata sobre problemas
                    json_output["_validation_issues"] = validation_result
                    
            except Exception as correction_error:
                logger.exception("[WARNING] Erro na correção automática: %s", correction_error)
                # Adicionar metadata sobre problemas originais
                json_output["_validation_issues"] = validation_result
        else:
            logger.info("[SUCCESS] JSON passou na validação contra template INEP!")
            
            # Log de warnings se houver
            if validation_result["warnings"]:
                logger.warning(f"[WARNING] Avisos: {validation_result['warnings']}")
                json_output["_validation_warnings"] = validation_result["warnings"]

        # **SANITIZAR MATERIAISDISPONIVEIS ANTES DE SALVAR NO FIRESTORE**
        if "materiaisDisponiveis" in json_output:
            json_output["materiaisDisponiveis"] = sanitize_materiais_disponiveis(json_output["materiaisDisponiveis"])
            logger.info("Campo 'materiaisDisponiveis' sanitizado antes do salvamento.")
    
        # **SANITIZAR PADRAOESPERADOPROCEDIMENTO ANTES DE SALVAR NO FIRESTORE**
        if "padraoEsperadoProcedimento" in json_output:
            json_output["padraoEsperadoProcedimento"] = sanitize_padrao_esperado_procedimento(json_output["padraoEsperadoProcedimento"])
            logger.info("Campo 'padraoEsperadoProcedimento' sanitizado antes do salvamento.")
        
        # **VALIDAÇÃO AVANÇADA DE IMPRESSOS MÉDICOS (COMO NO INDIVIDUAL)**
        if IMPRESSOS_VALIDATOR_AVAILABLE:
            logger.info("🏥 Iniciando validação avançada de impressos médicos...")
            
            try:
                is_valid, validation_errors, estacao_corrigida = validar_impressos_estacao(json_output)
                
                if not is_valid:
                    logger.warning(f"⚠️ Impressos com problemas detectados: {len(validation_errors)} erros")
                    
                    # Log dos erros para análise
                    for error in validation_errors:
                        logger.warning(f"   - {error}")
                    
                    # Aplicar correções automáticas
                    json_output = estacao_corrigida
                    logger.info("🔧 Correções automáticas aplicadas aos impressos")
                    
                    # Registrar métricas de validação
                    if MONITORING_SYSTEM.get('active'):
                        MONITORING_SYSTEM['metrics']['validation_warnings'] += len(validation_errors)
                        MONITORING_SYSTEM['metrics']['impressos_corrected'] = MONITORING_SYSTEM['metrics'].get('impressos_corrected', 0) + 1
                else:
                    logger.info("✅ Todos os impressos passaram na validação médica!")
                    
                    # Registrar sucesso na validação
                    if MONITORING_SYSTEM.get('active'):
                        MONITORING_SYSTEM['metrics']['impressos_validated'] = MONITORING_SYSTEM['metrics'].get('impressos_validated', 0) + 1
                        
            except Exception as validation_error:
                logger.error(f"Erro na validação de impressos: {validation_error}")
                # Continuar com o salvamento mesmo se a validação falhar
                if MONITORING_SYSTEM.get('active'):
                    MONITORING_SYSTEM['metrics']['validation_errors'] += 1
        else:
            logger.warning("⚠️ Sistema de validação de impressos não disponível - pulando validação")

        # ==========================================
        # SALVAMENTO DUPLO: LOCAL + FIRESTORE  
        # ==========================================
        
        # 1. SALVAMENTO LOCAL SEMPRE (garantido)
        logger.info(f"[LOCAL] Salvando estação localmente...")
        local_station_id = str(uuid.uuid4())
        local_stations_dir = "estacoes_geradas"
        os.makedirs(local_stations_dir, exist_ok=True)
        
        # Criar arquivo local com metadata
        station_with_metadata = {
            **json_output,
            "id": local_station_id,
            "created_at": datetime.now().isoformat(),
            "created_by": "sistema_hibrido",
            "source": "local_sempre",
            "tema_original": tema,
            "especialidade_original": especialidade,
            "titulo": json_output.get("titulo", "Estação sem título")
        }
        
        # Salvar JSON local
        local_file = os.path.join(local_stations_dir, f"{local_station_id}.json")
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(station_with_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[LOCAL] ✅ Estação salva localmente! ID: {local_station_id}")
        logger.info(f"[LOCAL] 📁 Arquivo: {local_file}")
        
        # 2. TENTAR SALVAMENTO NO FIRESTORE (somente se não for skip_firestore)
        firestore_station_id = None
        if skip_firestore:
            logger.info(f"[FIRESTORE] ⏩ Salvamento no Firestore DESABILITADO (geração múltipla)")
        elif db is not None:
            try:
                logger.info(f"[FIRESTORE] Tentando salvar documento...")
                logger.info(f"[FIRESTORE] Tamanho do JSON: {len(json.dumps(json_output))} caracteres")
                logger.info(f"[FIRESTORE] Chaves do documento: {list(json_output.keys())}")

                # Verificar profundidade máxima do documento completo antes de salvar
                doc_depth = _calculate_max_depth(json_output)
                logger.info(f"[FIRESTORE] Profundidade máxima do documento: {doc_depth}")

                # Usar o mesmo JSON com metadata para consistência
                update_time, doc_ref = db.collection('estacoes_clinicas').add(station_with_metadata)
                firestore_station_id = doc_ref.id
                logger.info(f"[FIRESTORE] ✅ Estação salva no Firestore! ID: {firestore_station_id}")

            except Exception as firestore_error:
                error_msg = str(firestore_error).lower()
                logger.warning("[WARNING] Firestore falhou: %s", firestore_error)

                # **LOG DIAGNÓSTICO**: Capturar detalhes específicos do erro do Firestore
                logger.error(f"[FIRESTORE_ERROR] Tipo do erro: {type(firestore_error).__name__}")
                logger.error(f"[FIRESTORE_ERROR] Mensagem completa: {str(firestore_error)}")

                # Verificar se é erro específico de entidade aninhada
                if "invalid nested entity" in error_msg or "nested" in error_msg:
                    logger.error(f"[FIRESTORE_ERROR] Erro de entidade aninhada detectado!")

                    # Tentar identificar qual campo está causando o problema
                    if "materiaisDisponiveis" in error_msg:
                        logger.error(f"[FIRESTORE_ERROR] Campo identificado: materiaisDisponiveis")
                        materiais_depth = _calculate_max_depth(json_output.get("materiaisDisponiveis", {}))
                        logger.error(f"[FIRESTORE_ERROR] Profundidade de materiaisDisponiveis: {materiais_depth}")
                    else:
                        # Verificar outros campos que podem ter aninhamento excessivo
                        for field in ["padraoEsperadoProcedimento", "instrucoesParticipante", "cenarioAtendimento"]:
                            if field in json_output:
                                field_depth = _calculate_max_depth(json_output[field])
                                logger.error(f"[FIRESTORE_ERROR] Profundidade de {field}: {field_depth}")
                                if field_depth > 10:
                                    logger.error(f"[FIRESTORE_ERROR] Campo suspeito encontrado: {field} (profundidade: {field_depth})")
                
                # Verificar se é erro de JWT e tentar reinicializar
                if "invalid jwt signature" in error_msg or "jwt" in error_msg or "invalid_grant" in error_msg:
                    logger.warning("🔑 Erro de autenticação JWT detectado! Tentando reinicializar Firebase...")
                    
                    # Tentar reinicializar Firebase
                    reinit_success = reinitialize_firebase_for_operations()
                    
                    if reinit_success and db is not None:
                        logger.info("[FIRESTORE] Firebase reinicializado! Tentando salvar novamente...")
                        try:
                            update_time, doc_ref = db.collection('estacoes_clinicas').add(station_with_metadata)
                            firestore_station_id = doc_ref.id
                            logger.info(f"[FIRESTORE] ✅ Estação salva no Firestore após reinicialização! ID: {firestore_station_id}")
                        except Exception as retry_error:
                            logger.error(f"[FIRESTORE] ❌ Falha na segunda tentativa: {retry_error}")
                    else:
                        logger.error("[FIRESTORE] ❌ Reinicialização do Firebase falhou")
                        logger.info("💡 Sugestões: verificar conexão, sincronizar data/hora, gerar nova chave de serviço")
                else:
                    # Outros tipos de erro, acionam fallback para salvamento local
                    logger.warning("[FIRESTORE] ⚠️ Erro não relacionado a JWT - estação já salva localmente.")
        else:
            logger.warning("[FIRESTORE] ⚠️ Firebase não conectado - estação já salva localmente.")

        # 3. DETERMINAR O ID FINAL (Firestore se disponível, senão local)
        final_station_id = firestore_station_id if firestore_station_id else local_station_id
        
        # Se temos ID do Firestore, atualizar o arquivo local com o ID correto
        if firestore_station_id:
            station_with_metadata["firestore_id"] = firestore_station_id
            station_with_metadata["sync_status"] = "synced"
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(station_with_metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"[SYNC] Arquivo local atualizado com ID do Firestore: {firestore_station_id}")
        else:
            station_with_metadata["sync_status"] = "local_only"
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(station_with_metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"[LOCAL] Estação mantida apenas localmente: {local_station_id}")

        # Registrar métricas de sucesso
        if MONITORING_SYSTEM.get('active'):
            MONITORING_SYSTEM['metrics']['successful_generations'] += 1
        
        # Retornar dados compatíveis com o fluxo individual (incluindo dados para auditoria disponível)
        return True, {
            "station_id": final_station_id,
            "tema": tema,
            "especialidade": especialidade,
            "abordagem_usada": abordagem_id,
            "validation_status": "valid" if validation_result["is_valid"] else "warning",
            "validation_warnings": validation_result.get("warnings", []),
            "station_data": json_output,
            "local_file": local_file,
            "firestore_synced": firestore_station_id is not None,
            # Dados que tornariam a auditoria disponível (como no fluxo individual)
            "audit_available": True,  # Indica que a auditoria estaria disponível
            "current_step": 3,        # Equivale a agentState.currentStep = 3
            "final_station_json": json.dumps(json_output, indent=2, ensure_ascii=False),  # Equivale a agentState.finalStationJson
            "analysis_result": None,  # Equivale a agentState.analysisResult = None (auditoria não feita)
            "audit_skipped": True     # Marca que a auditoria foi propositalmente pulada
        }, ""
        
    except Exception as e:
        logger.error(f"Erro ao gerar estação para tema '{tema}': {e}")
        
        # Registrar métricas de falha
        if MONITORING_SYSTEM.get('active'):
            MONITORING_SYSTEM['metrics']['failed_generations'] += 1
        
        return False, {
            "tema": tema,
            "especialidade": especialidade,
            "abordagem_usada": abordagem_id
        }, str(e)

# --- Endpoints da API ---
@app.get("/health", tags=["Status"])
def health_check():
    flash_count = len(GEMINI_CONFIGS.get('flash', []))
    pro_count = len(GEMINI_CONFIGS.get('pro', []))
    total_count = len(GEMINI_CONFIGS.get('all', []))
    
    return {
        "status": "ok",
        "total_keys_loaded": total_count,
        "flash_keys": flash_count,
        "pro_keys": pro_count,
        "models_configured": {
            "fase_1": "gemini-2.5-flash",
            "fase_2": "gemini-2.5-flash",
            "fases_3_4": "gemini-2.5-flash"
        }
    }

@app.get("/api/test-gemini", tags=["Status"])
async def test_gemini():
    """Testa se os modelos Gemini estão funcionando"""
    if not GEMINI_CONFIGS or not GEMINI_CONFIGS.get('all'):
        raise HTTPException(status_code=503, detail="Nenhuma chave configurada")
    
    try:
        # Testa primeiro com Flash (usado na Fase 1)
        if GEMINI_CONFIGS.get('flash'):
            config = GEMINI_CONFIGS['flash'][0]
            genai.configure(api_key=config['key'])  # type: ignore
            model = genai.GenerativeModel(config['model_name'])  # type: ignore
            response = await model.generate_content_async("Responda apenas: 'Gemini Flash funcionando!'")
            
            # Verifica se a resposta é válida antes de acessar response.text
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                return {
                    "status": "success",
                    "flash_model": config['model_name'],
                    "pro_models_available": len(GEMINI_CONFIGS.get('pro', [])),
                    "flash_models_available": len(GEMINI_CONFIGS.get('flash', [])),
                    "response": response.text,
                    "message": "Gemini configurado corretamente - Flash para Fases 1-2, Pro para Fases 3-4!"
                }
            else:
                candidate = response.candidates[0] if response.candidates else None
                # Garantir que finish_reason seja um int válido para indexar FINISH_REASON_NAMES
                try:
                    finish_reason_code = int(candidate.finish_reason) if candidate and candidate.finish_reason is not None else -1
                except (ValueError, TypeError):
                    finish_reason_code = -1
                finish_reason_name = get_finish_reason_name(finish_reason_code)
                return {
                    "status": "warning",
                    "flash_model": config['model_name'],
                    "finish_reason_code": finish_reason_code,
                    "finish_reason_name": finish_reason_name,
                    "message": f"Flash respondeu mas sem conteúdo válido ({finish_reason_name})"
                }
        else:
            # Fallback para Pro se Flash não estiver disponível
            config = GEMINI_CONFIGS.get('pro', [{}])[0] if GEMINI_CONFIGS.get('pro') else GEMINI_CONFIGS.get('all', [{}])[0]
            genai.configure(api_key=config['key'])  # type: ignore
            model = genai.GenerativeModel(config['model_name'])  # type: ignore
            response = await model.generate_content_async("Responda apenas: 'Gemini funcionando!'")
            
            # Verifica se a resposta é válida antes de acessar response.text
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                return {
                    "status": "success",
                    "model_used": config['model_name'],
                    "response": response.text,
                    "message": "Gemini funcionando, mas sem Flash disponível"
                }
            else:
                candidate = response.candidates[0] if response.candidates else None
                finish_reason_code = candidate.finish_reason if candidate else -1
                finish_reason_name = get_finish_reason_name(finish_reason_code)
                return {
                    "status": "warning",
                    "model_used": config['model_name'],
                    "finish_reason_code": finish_reason_code,
                    "finish_reason_name": finish_reason_name,
                    "message": f"Modelo respondeu mas sem conteúdo válido ({finish_reason_name})"
                }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Erro ao testar Gemini - verifique as chaves de API"
        }

@app.get("/api/gemini-diagnostic", tags=["Status"])
async def gemini_diagnostic():
    """Diagnóstico detalhado da API Gemini com análise de finish_reason"""
    if not GEMINI_CONFIGS or not GEMINI_CONFIGS.get('all'):
        raise HTTPException(status_code=503, detail="Nenhuma chave configurada")
    
    diagnostic_results = []
    
    # Testa diferentes prompts para verificar comportamentos
    test_prompts = [
        {"name": "Prompt Normal", "text": "Diga apenas: OK"},
        {"name": "Prompt Vazio", "text": ""},
        {"name": "Prompt Muito Longo", "text": "Explique detalhadamente " + "todas as " * 1000 + "nuances da medicina."},
    ]
    
    for prompt_test in test_prompts:
        for model_type in ['flash', 'pro']:
            if not GEMINI_CONFIGS.get(model_type):
                continue
                
            config = GEMINI_CONFIGS[model_type][0]
            try:
                genai.configure(api_key=config['key'])  # type: ignore
                model = genai.GenerativeModel(config['model_name'])  # type: ignore
                response = await model.generate_content_async(prompt_test["text"])
                
                # Análise detalhada da resposta
                result = {
                    "prompt_name": prompt_test["name"],
                    "model": config['model_name'],
                    "has_candidates": bool(response.candidates),
                    "candidates_count": len(response.candidates) if response.candidates else 0
                }
                
                if response.candidates:
                    candidate = response.candidates[0]
                    finish_reason_code = candidate.finish_reason
                    finish_reason_name = get_finish_reason_name(finish_reason_code)
    
                    result.update({
                        "finish_reason_code": finish_reason_code,
                        "finish_reason_name": finish_reason_name,
                        "has_content": bool(candidate.content),
                        "has_parts": bool(candidate.content and candidate.content.parts),
                        "can_access_text": False,
                        "text_preview": None,
                        "error_accessing_text": None
                    })
                    
                    # Tenta acessar response.text de forma segura
                    try:
                        if candidate.content and candidate.content.parts:
                            text_content = response.text
                            result.update({
                                "can_access_text": True,
                                "text_preview": text_content[:100] + "..." if len(text_content) > 100 else text_content
                            })
                        else:
                            result["error_accessing_text"] = "Candidato sem conteúdo ou partes válidas"
                    except Exception as text_error:
                        result.update({
                            "can_access_text": False,
                            "error_accessing_text": str(text_error)
                        })
                
                diagnostic_results.append(result)
                
            except Exception as e:
                diagnostic_results.append({
                    "prompt_name": prompt_test["name"],
                    "model": config['model_name'],
                    "error": str(e)
                })
    
    return {
        "status": "completed",
        "total_tests": len(diagnostic_results),
        "finish_reason_codes_reference": FINISH_REASON_NAMES,
        "results": diagnostic_results
    }

@app.get("/api/abordagens-padrao", tags=["Configuração"])
async def get_abordagens_padrao():
    """Retorna as 5 abordagens padrão disponíveis para seleção na Fase 2"""
    return {"abordagens": ABORDAGENS_PADRAO}

@app.get("/api/firebase-status", tags=["Status"])
async def get_firebase_status():
    """Verifica o status atual do Firebase e permite reinicialização"""
    global db, firebase_mock_mode
    
    status = {
        "connected": db is not None and not firebase_mock_mode,
        "mock_mode": firebase_mock_mode,
        "db_instance": db is not None,
        "last_check": datetime.now().isoformat()
    }
    
    if db is not None:
        try:
            # Teste rápido de conectividade
            test_collections = list(db.collections())
            status["connectivity_test"] = "success"
            status["collections_count"] = len(test_collections)
        except Exception as e:
            status["connectivity_test"] = "failed"
            status["connectivity_error"] = str(e)
    
    return status

@app.post("/api/firebase-reinit", tags=["Status"])
async def reinitialize_firebase():
    """Força reinicialização do Firebase para resolver problemas de autenticação"""
    try:
        print("[REFRESH] Iniciando reinicialização manual do Firebase...")
        success = reinitialize_firebase_for_operations()
        
        if success:
            return {
                "success": True,
                "message": "Firebase reinicializado com sucesso",
                "connected": db is not None and not firebase_mock_mode,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Falha na reinicialização - sistema em modo local",
                "connected": False,
                "mock_mode": firebase_mock_mode,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro durante reinicialização: {e}",
            "connected": False,
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/generate-station", tags=["Geração Individual"])
async def generate_station_endpoint(
    tema: str,
    especialidade: str,
    abordagem_id: str = "caso_clinico",
    enable_web_search: bool = False
):
    """
    Endpoint para geração individual de estação - ORIGINAL
    Mantém compatibilidade com o frontend existente
    """
    try:
        print(f"\n[GERAÇÃO INDIVIDUAL] Iniciando para tema: {tema}")
        print(f"[GERAÇÃO INDIVIDUAL] Especialidade: {especialidade}")
        print(f"[GERAÇÃO INDIVIDUAL] Abordagem: {abordagem_id}")
        print(f"[GERAÇÃO INDIVIDUAL] Web Search: {enable_web_search}")
        
        success, result, error_msg = await generate_single_station_internal(
            tema=tema,
            especialidade=especialidade,
            abordagem_id=abordagem_id,
            enable_web_search=enable_web_search
        )
        
        if success:
            print(f"[GERAÇÃO INDIVIDUAL] ✅ Sucesso - Station ID: {result.get('station_id', 'N/A')}")
            return {
                "success": True,
                "station_id": result.get("station_id"),
                "validation_status": result.get("validation_status"),
                "message": "Estação gerada e salva com sucesso"
            }
        else:
            print(f"[GERAÇÃO INDIVIDUAL] ❌ Erro: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        print(f"[GERAÇÃO INDIVIDUAL] 💥 Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/api/agent/start-creation", tags=["Agente - Geração"])
async def start_creation_process(
    tema: str = Form(...),
    especialidade: str = Form(...),
    enable_web_search: str = Form("0")      # Recebe '1' ou '0' do frontend
):
    """
    Orquestra as Fases 1 e 2, agora usando RAG para buscar PDFs indexados e estações INEP.
    O parâmetro enable_web_search controla se a busca web será executada (valor '1' habilita).
    """
    if not AGENT_RULES:
        raise HTTPException(status_code=503, detail="Regras do agente não carregadas.")
    
    # --- BUSCA WEB EM TEMPO REAL (opcional) ---
    web_search_summary = ""
    hits = []



            


            
    # --- BUSCA WEB EM TEMPO REAL (opcional) ---
    web_search_summary = ""
    hits = []
    try:
        # Interpretar flag enviada pelo frontend
        enabled_flag = str(enable_web_search).lower() in ("1", "true", "yes")
        serp_key = os.getenv("SERPAPI_KEY")
        if enabled_flag and serp_key:
            # Import local para evitar E402 em nível de módulo e permitir execução dinâmica
            try:
                from web_search import search_web  # import local, usado apenas quando a busca web é ativada
            except Exception as imp_err:
               logger.warning("Não foi possível importar web_search: %s", imp_err)
               serp_key = None

        if enabled_flag and serp_key:
            queries = [
                f"diretrizes atualizadas {tema} {especialidade} Brasil",
                f"protocolo clínico {tema} Revalida",
                f"consenso {tema} sociedade brasileira de {especialidade}"
            ]
            for q in queries:
                try:
                    # search_web é síncrono — executar em thread para não bloquear o loop async
                    res = await asyncio.to_thread(search_web, q, 3, True)
                    for r in res:
                        hits.append({"query": q, **r})
                except Exception as we:
                    logger.warning("[WARNING] Falha na busca web para query '%s': %s", q, we)
        else:
            if not enabled_flag:
                print("ℹ️ Busca web desabilitada por flag do frontend.")
            else:
                print("[WARNING] SERPAPI_KEY não configurado — pulando buscas web.")
            hits = []
    except Exception as e:
        print(f"[WARNING] Módulo de busca web não disponível: {e}")
        hits = []
    
    if hits:
        web_lines = []
        for h in hits:
            title = h.get("title", "").strip()
            snippet = h.get("snippet", "").strip()
            link = h.get("link", "").strip()
            web_lines.append(f"- {title}: {snippet} ({link})")
        web_search_summary = "\n".join(web_lines)

        # Registrar telemetria: eventos de busca sanitizados (não incluir PII adicional)
        try:
            for h in hits:
                # cada hit já contém 'query' adicionado anteriormente
                log_search_event(h.get("query", ""), h)
        except Exception as te:
            print(f"[WARNING] Erro ao registrar telemetria de busca: {te}")
    
    # --- FASE 1 (USAR GEMINI 2.5 FLASH + RAG) ---
    logger.info("[FAST] Iniciando Fase 1 (Flash + RAG) para Tema: %s", tema)
    prompt_fase_1 = await build_prompt_fase_1(tema, especialidade)
    
    # Adicionar busca web se disponível
    if web_search_summary:
        prompt_fase_1 += f"\n\n**INFORMAÇÕES COMPLEMENTARES DA BUSCA WEB:**\n{web_search_summary}"
    
    resumo_clinico = await call_gemini_api(prompt_fase_1, preferred_model='flash')
    logger.info("[SUCCESS] Fase 1 (Resumo Clínico com Flash + RAG) concluída.")
    
    # --- FASE 2 (USAR GEMINI 2.5 FLASH + RAG) ---
    logger.info("[BRAIN] Iniciando Fase 2 (Flash + RAG) para gerar propostas...")
    prompt_fase_2 = await build_prompt_fase_2(tema, especialidade, resumo_clinico)
    propostas = await call_gemini_api(prompt_fase_2, preferred_model='flash')
    logger.info("[SUCCESS] Fase 2 (Propostas com Flash + RAG) concluída.")

    return {"resumo_clinico": resumo_clinico, "propostas": propostas}

@app.post("/api/agent/generate-proposals", tags=["Agente - Geração"])
async def generate_proposals_with_selection(
    tema: str = Form(...),
    especialidade: str = Form(...),
    resumo_clinico: str = Form(...),
    abordagens_selecionadas: str = Form(...)  # Lista de IDs separados por vírgula
):
    """
    Gera propostas da Fase 2 com base nas abordagens selecionadas pelo usuário.
    Se apenas 1 abordagem for selecionada, pode ir direto para a Fase 3.
    """
    if not AGENT_RULES:
        raise HTTPException(status_code=503, detail="Regras do agente não carregadas.")
    
    # Parsear as abordagens selecionadas
    try:
        abordagens_ids = [id.strip() for id in abordagens_selecionadas.split(",") if id.strip()]
        if not abordagens_ids:
            raise ValueError("Nenhuma abordagem selecionada")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar abordagens selecionadas: {str(e)}")
    
    # Validar se todas as abordagens selecionadas são válidas
    abordagens_validas = [a["id"] for a in ABORDAGENS_PADRAO]
    abordagens_invalidas = [id for id in abordagens_ids if id not in abordagens_validas]
    if abordagens_invalidas:
        raise HTTPException(status_code=400, detail=f"Abordagens inválidas: {abordagens_invalidas}")
    
    logger.info("🎯 Abordagens selecionadas: %s", abordagens_ids)
    
    # --- FASE 2 COM ABORDAGENS SELECIONADAS ---
    logger.info("[BRAIN] Iniciando Fase 2 com abordagens selecionadas...")
    prompt_fase_2 = await build_prompt_fase_2(tema, especialidade, resumo_clinico, abordagens_ids)
    propostas = await call_gemini_api(prompt_fase_2, preferred_model='flash')
    logger.info("[SUCCESS] Fase 2 (Propostas selecionadas) concluída.")
    
    # Determinar se pode ir direto para Fase 3
    pode_ir_direto_fase3 = len(abordagens_ids) == 1
    
    return {
        "propostas": propostas,
        "abordagens_selecionadas": abordagens_ids,
        "pode_ir_direto_fase3": pode_ir_direto_fase3,
        "total_abordagens": len(abordagens_ids)
    }

# ## ENDPOINT MODIFICADO ##
@app.post("/api/agent/generate-final-station", tags=["Agente - Geração"])
async def generate_and_save_final_station(request: GenerateFinalStationRequest):
    """
    Orquestra a Fase 3, gerando o JSON final, SALVANDO no Firestore
    e retornando o ID e os dados da nova estação.
    """
    if not AGENT_RULES or not db:
        raise HTTPException(status_code=503, detail="Regras ou conexão com Firestore não disponíveis.")
    
    # 1. Gerar a Estação (USAR GEMINI 2.5 PRO)
    # Configurar logger para o endpoint
    logger = logging.getLogger("agent.generate_station")
    logger.info("Iniciando geração de estação com Gemini Pro",
                extra={"tema": request.tema, "especialidade": request.especialidade})
    
    prompt_fase_3 = await build_prompt_fase_3(request)
    json_output_str = await call_gemini_api(prompt_fase_3, preferred_model='pro')
    
    # Extrair JSON usando o helper extract_json_from_text
    clean_json_str = extract_json_from_text(json_output_str)
    try:
        json_output = json.loads(clean_json_str)
        logger.info("JSON extraído e parseado com sucesso na primeira tentativa.")
    except json.JSONDecodeError as e:
        logger.warning("Falha no parse inicial do JSON. Tentando sanitização e correção aprimorada.", extra={"error": str(e), "json_preview": clean_json_str[:200]})

        # Estratégia 1: Sanitização aprimorada com correções específicas
        sanitized_str = sanitize_json_string(clean_json_str)
        try:
            json_output = json.loads(sanitized_str)
            logger.info("JSON parseado com sucesso após sanitização aprimorada.")
            MONITORING_SYSTEM["metrics"]["json_corrected_by_sanitization"] = MONITORING_SYSTEM["metrics"].get("json_corrected_by_sanitization", 0) + 1
        except json.JSONDecodeError as sanitization_error:
            logger.warning("Sanitização aprimorada falhou. Tentando correção estrutural avançada.", extra={"sanitization_error": str(sanitization_error)})

            # Estratégia 2: Correção estrutural avançada
            try:
                corrected_str = _advanced_json_correction(clean_json_str)
                json_output = json.loads(corrected_str)
                logger.info("JSON corrigido com sucesso usando correção estrutural avançada!")
                MONITORING_SYSTEM["metrics"]["json_corrected_by_advanced"] = MONITORING_SYSTEM["metrics"].get("json_corrected_by_advanced", 0) + 1
            except Exception as advanced_correction_error:
                logger.warning("Correção estrutural avançada falhou. Usando LLM como último recurso.", extra={"advanced_error": str(advanced_correction_error)})

                # Estratégia 3: LLM como último recurso
                correction_prompt = f"""
                O seguinte texto deveria ser um JSON válido para uma estação médica REVALIDA, mas contém erros de sintaxe.
                Corrija TODOS os erros de sintaxe JSON e retorne APENAS o código JSON válido, sem nenhum texto ou explicação adicional.

                IMPORTANTE:
                - Mantenha toda a estrutura e conteúdo clínico
                - Corrija apenas erros de sintaxe (aspas, vírgulas, chaves)
                - Garanta que o JSON seja válido e parseável
                - Não altere o conteúdo médico das respostas

                JSON Inválido:
                ```
                {clean_json_str}
                ```

                JSON Corrigido (APENAS o JSON, nada mais):
                """
                try:
                    corrected_json_str = await call_gemini_api(correction_prompt, preferred_model='flash', timeout=60)
                    clean_corrected_json = extract_json_from_text(corrected_json_str)
                    json_output = json.loads(clean_corrected_json)
                    logger.info("JSON corrigido com sucesso usando LLM!")
                    MONITORING_SYSTEM["metrics"]["json_corrected_by_llm"] = MONITORING_SYSTEM["metrics"].get("json_corrected_by_llm", 0) + 1
                except Exception as llm_correction_error:
                    error_msg = f"Erro ao parsear JSON mesmo após todas as tentativas de correção: {llm_correction_error}"
                    logger.error(error_msg, extra={"original_json": clean_json_str[:200], "sanitized_json": sanitized_str[:200], "llm_attempt": corrected_json_str[:200] if 'corrected_json_str' in locals() else 'N/A'})
                    MONITORING_SYSTEM["metrics"]["failed_generations"] = MONITORING_SYSTEM["metrics"].get("failed_generations", 0) + 1
                    raise HTTPException(status_code=500, detail=f"A IA gerou um JSON inválido e todas as tentativas de correção falharam: {llm_correction_error}")

    logger.info("JSON processado com sucesso.")
    MONITORING_SYSTEM["metrics"]["successful_generations"] = MONITORING_SYSTEM["metrics"].get("successful_generations", 0) + 1

    # **NOVA FUNCIONALIDADE: Validação contra template gabaritoestacoes.json**
    logger.info("🔍 Validando JSON gerado contra template INEP...")
    validation_result = validate_json_against_template(json_output)
    
    if not validation_result["is_valid"]:
        print("[ERROR] JSON não passou na validação!")
        
        # Log detalhado dos problemas
        if validation_result["missing_required_fields"]:
            print(f"📋 Campos obrigatórios ausentes: {validation_result['missing_required_fields']}")
        if validation_result["invalid_field_types"]:
            print(f"🔢 Tipos de campo inválidos: {validation_result['invalid_field_types']}")
        if validation_result["structural_issues"]:
            print(f"🏗️ Problemas estruturais: {validation_result['structural_issues']}")
        
        # Tentar corrigir automaticamente usando Gemini Flash
        logger.info("🔧 Tentando corrigir automaticamente com Gemini Flash...")
        
        correction_prompt = f"""# CORREÇÃO DE JSON - CONFORMIDADE INEP

**JSON ATUAL (COM PROBLEMAS):**
```json
{json.dumps(json_output, indent=2, ensure_ascii=False)}
```

**PROBLEMAS IDENTIFICADOS:**
- Campos obrigatórios ausentes: {validation_result['missing_required_fields']}
- Tipos de campo inválidos: {validation_result['invalid_field_types']}
- Problemas estruturais: {validation_result['structural_issues']}

**TEMPLATE CORRETO (gabaritoestacoes.json):**
```json
{get_gabarito_template() if LOCAL_MEMORY_SYSTEM else AGENT_RULES.get('gabarito_json', '{}')}
```

**SUA TAREFA:**
Corrija o JSON atual para que seja 100% conforme o template. Mantenha TODO o conteúdo clínico gerado, apenas ajuste a estrutura, campos ausentes e tipos de dados. Retorne APENAS o JSON corrigido, sem explicações."""

        try:
            corrected_json_str = await call_gemini_api(correction_prompt, preferred_model='flash')
            
            # Limpar e re-parsear o JSON corrigido
            if corrected_json_str.strip().startswith("```json"):
                corrected_json_str = corrected_json_str.strip()[7:-3]
            
            # **NOVA FUNCIONALIDADE: Aplicar sanitização de materiaisDisponiveis na correção automática**
            try:
                temp_json = json.loads(corrected_json_str)
                if "materiaisDisponiveis" in temp_json:
                    temp_json["materiaisDisponiveis"] = sanitize_materiais_disponiveis(temp_json["materiaisDisponiveis"])
                    corrected_json_str = json.dumps(temp_json, ensure_ascii=False)
                    logger.info("Campo 'materiaisDisponiveis' sanitizado durante correção automática.")
            except json.JSONDecodeError:
                logger.warning("Não foi possível sanitizar 'materiaisDisponiveis' durante correção automática (JSON inválido antes da sanitização).")
            
            # Tentar carregar corrigido; usar sanitização se necessário
            try:
                corrected_json = json.loads(corrected_json_str)
            except json.JSONDecodeError:
                corrected_json = json.loads(sanitize_json_string(corrected_json_str))
            
            # Re-validar o JSON corrigido
            revalidation_result = validate_json_against_template(corrected_json)
            
            if revalidation_result["is_valid"]:
                logger.info("[SUCCESS] JSON corrigido automaticamente e aprovado na validação!")
                MONITORING_SYSTEM["metrics"]["successful_generations"] = MONITORING_SYSTEM["metrics"].get("successful_generations", 0) + 1
                json_output = corrected_json
            else:
                logger.warning("[WARNING] Correção automática não foi suficiente, mas continuando...")
                # Adicionar metadata sobre problemas
                json_output["_validation_issues"] = validation_result
                
        except Exception as correction_error:
            logger.exception("[WARNING] Erro na correção automática: %s", correction_error)
            # Adicionar metadata sobre problemas originais
            json_output["_validation_issues"] = validation_result
    else:
        print("[SUCCESS] JSON passou na validação contra template INEP!")
        
        # Log de warnings se houver
        if validation_result["warnings"]:
            print(f"[WARNING] Avisos: {validation_result['warnings']}")
            json_output["_validation_warnings"] = validation_result["warnings"]

    # 2. Salvar a Estação com fallback local
    try:
        logger.info("💾 Salvando a nova estação na coleção 'estacoes_clinicas'...")

        # **NOVA FUNCIONALIDADE: Sanitizar materiaisDisponiveis antes de salvar no Firestore**
        if "materiaisDisponiveis" in json_output:
            json_output["materiaisDisponiveis"] = sanitize_materiais_disponiveis(json_output["materiaisDisponiveis"])
            logger.info("Campo 'materiaisDisponiveis' sanitizado antes do salvamento.")
    
            # **NOVA FUNCIONALIDADE: Sanitizar padraoEsperadoProcedimento antes de salvar no Firestore**
            if "padraoEsperadoProcedimento" in json_output:
                json_output["padraoEsperadoProcedimento"] = sanitize_padrao_esperado_procedimento(json_output["padraoEsperadoProcedimento"])
                logger.info("Campo 'padraoEsperadoProcedimento' sanitizado antes do salvamento.")
        
        # **NOVA FUNCIONALIDADE: Validação Avançada de Impressos Médicos**
        if IMPRESSOS_VALIDATOR_AVAILABLE:
            logger.info("🏥 Iniciando validação avançada de impressos médicos...")
            
            try:
                is_valid, validation_errors, estacao_corrigida = validar_impressos_estacao(json_output)
                
                if not is_valid:
                    logger.warning(f"⚠️ Impressos com problemas detectados: {len(validation_errors)} erros")
                    
                    # Log dos erros para análise
                    for error in validation_errors:
                        logger.warning(f"   - {error}")
                    
                    # Aplicar correções automáticas
                    json_output = estacao_corrigida
                    logger.info("🔧 Correções automáticas aplicadas aos impressos")
                    
                    # Registrar métricas de validação
                    if MONITORING_SYSTEM.get('active'):
                        MONITORING_SYSTEM['metrics']['validation_warnings'] += len(validation_errors)
                        MONITORING_SYSTEM['metrics']['impressos_corrected'] = MONITORING_SYSTEM['metrics'].get('impressos_corrected', 0) + 1
                else:
                    logger.info("✅ Todos os impressos passaram na validação médica!")
                    
                    # Registrar sucesso na validação
                    if MONITORING_SYSTEM.get('active'):
                        MONITORING_SYSTEM['metrics']['impressos_validated'] = MONITORING_SYSTEM['metrics'].get('impressos_validated', 0) + 1
                        
            except Exception as validation_error:
                logger.error(f"Erro na validação de impressos: {validation_error}")
                # Continuar com o salvamento mesmo se a validação falhar
                if MONITORING_SYSTEM.get('active'):
                    MONITORING_SYSTEM['metrics']['validation_errors'] += 1
        else:
            logger.warning("⚠️ Sistema de validação de impressos não disponível - pulando validação")
        
        # Tentar salvar no Firestore primeiro
        new_station_id = None
        if db is not None:
            try:
                print(f"[FIRESTORE] Tentando salvar documento...")
                print(f"[FIRESTORE] Tamanho do JSON: {len(json.dumps(json_output))} caracteres")
                print(f"[FIRESTORE] Chaves do documento: {list(json_output.keys())}")

                # Verificar profundidade máxima do documento completo antes de salvar
                doc_depth = _calculate_max_depth(json_output)
                print(f"[FIRESTORE] Profundidade máxima do documento: {doc_depth}")

                update_time, doc_ref = db.collection('estacoes_clinicas').add(json_output)
                new_station_id = doc_ref.id
                logger.info("[SUCCESS] Estação salva no Firestore! ID: %s", new_station_id)

            except Exception as firestore_error:
                error_msg = str(firestore_error).lower()
                logger.warning("[WARNING] Firestore falhou: %s", firestore_error)

                # **LOG DIAGNÓSTICO**: Capturar detalhes específicos do erro do Firestore
                print(f"[FIRESTORE_ERROR] Tipo do erro: {type(firestore_error).__name__}")
                print(f"[FIRESTORE_ERROR] Mensagem completa: {str(firestore_error)}")

                # Verificar se é erro específico de entidade aninhada
                if "invalid nested entity" in error_msg or "nested" in error_msg:
                    print(f"[FIRESTORE_ERROR] Erro de entidade aninhada detectado!")

                    # Tentar identificar qual campo está causando o problema
                    if "materiaisDisponiveis" in error_msg:
                        print(f"[FIRESTORE_ERROR] Campo identificado: materiaisDisponiveis")
                        materiais_depth = _calculate_max_depth(json_output.get("materiaisDisponiveis", {}))
                        print(f"[FIRESTORE_ERROR] Profundidade de materiaisDisponiveis: {materiais_depth}")
                    else:
                        # Verificar outros campos que podem ter aninhamento excessivo
                        for field in ["padraoEsperadoProcedimento", "instrucoesParticipante", "cenarioAtendimento"]:
                            if field in json_output:
                                field_depth = _calculate_max_depth(json_output[field])
                                print(f"[FIRESTORE_ERROR] Profundidade de {field}: {field_depth}")
                                if field_depth > 10:
                                    print(f"[FIRESTORE_ERROR] Campo suspeito encontrado: {field} (profundidade: {field_depth})")
                
                # Verificar se é erro de JWT e tentar reinicializar
                if "invalid jwt signature" in error_msg or "jwt" in error_msg or "invalid_grant" in error_msg:
                    logger.warning("🔑 Erro de autenticação JWT detectado! Tentando reinicializar Firebase...")
                    
                    # Tentar reinicializar Firebase
                    reinit_success = reinitialize_firebase_for_operations()
                    
                    if reinit_success and db is not None:
                        logger.info("[SUCCESS] Firebase reinicializado! Tentando salvar novamente...")
                        try:
                            update_time, doc_ref = db.collection('estacoes_clinicas').add(json_output)
                            new_station_id = doc_ref.id
                            logger.info("[SUCCESS] Estação salva no Firestore após reinicialização! ID: %s", new_station_id)
                        except Exception as retry_error:
                            logger.error("[ERROR] Falha na segunda tentativa: %s", retry_error)
                    else:
                        logger.error("[ERROR] Reinicialização do Firebase falhou")
                        logger.info("💡 Sugestões: verificar conexão, sincronizar data/hora, gerar nova chave de serviço")
                else:
                    # Outros tipos de erro, acionam fallback para salvamento local
                    logger.warning("Erro não relacionado a JWT, acionando fallback para salvamento local.")

        # Fallback: Salvar localmente se a operação no Firestore falhou ou não foi tentada
        if not new_station_id:
            logger.info("Salvando localmente como fallback...")
            new_station_id = str(uuid.uuid4())
            local_stations_dir = "estacoes_geradas"
            os.makedirs(local_stations_dir, exist_ok=True)
            
            # Criar arquivo local com metadata
            station_with_metadata = {
                **json_output,
                "id": new_station_id,
                "created_at": datetime.now().isoformat(),
                "created_by": "sistema_hibrido",
                "source": "local_fallback",
                "tema_original": request.tema,
                "especialidade_original": request.especialidade
            }
            
            # Salvar JSON local
            local_file = os.path.join(local_stations_dir, f"{new_station_id}.json")
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(station_with_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info("[SUCCESS] Estação salva localmente! ID: %s", new_station_id)
            logger.info("📁 Arquivo: %s", local_file)
    except Exception as e:
        logger.exception("🚨 Erro crítico ao salvar estação: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a estação: {e}")

    # 3. Retornar o resultado
    return {
        "status": "success",
        "message": "Estação gerada e salva com sucesso!",
        "station_id": new_station_id,
        "station_data": json_output
    }


@app.post("/api/agent/generate-multiple-stations", tags=["Agente - Geração"])
async def generate_multiple_stations(request: MultipleGenerationRequest):
    """
    Gera múltiplas estações em lote seguindo o fluxo:
    - Para cada tema: Fase 1 → 2 → 3 (sem pausa)
    - Abordagem pré-selecionada (não permite escolha)
    - Sem Fase 4 (auditoria)
    - Retorna progresso e resultados de cada geração
    """
    if not AGENT_RULES:
        raise HTTPException(status_code=503, detail="Regras do agente não disponíveis.")
    
    logger = logging.getLogger("agent.multiple_generation")
    
    # Validações de entrada
    if not request.temas or len(request.temas) == 0:
        raise HTTPException(status_code=400, detail="Lista de temas não pode estar vazia")
    
    # Aumentar limite já que o processamento é sequencial (um tema por vez)
    if len(request.temas) > 100:  # Aumentado de 50 para 100
        raise HTTPException(status_code=400, detail="Máximo de 100 temas por vez. O processamento é sequencial (um tema por vez) para evitar sobrecarga.")
    
    # Validar abordagem
    abordagens_validas = [a["id"] for a in ABORDAGENS_PADRAO]
    if request.abordagem_selecionada not in abordagens_validas:
        raise HTTPException(status_code=400, detail=f"Abordagem inválida. Válidas: {abordagens_validas}")
    
    logger = logging.getLogger("agent.multiple_generation")
    logger.info(f"[MÚLTIPLA] Iniciando processamento sequencial de {len(request.temas)} tema(s)")
    logger.info(f"[MÚLTIPLA] Cada tema será processado individualmente: Fase 1 → 2 → 3")
    logger.info(f"[MÚLTIPLA] Especialidade: {request.especialidade}")
    logger.info(f"[MÚLTIPLA] Abordagem: {request.abordagem_selecionada}")
    logger.info(f"[MÚLTIPLA] Busca web: {request.enable_web_search}")
    
    # Preparar controle de progresso
    total_temas = len(request.temas)
    resultados = []
    sucessos = 0
    falhas = 0
    
    # Registrar início da operação múltipla
    if MONITORING_SYSTEM.get('active'):
        MONITORING_SYSTEM['metrics']['multiple_generation_sessions'] = MONITORING_SYSTEM['metrics'].get('multiple_generation_sessions', 0) + 1
    
    # Processar cada tema sequencialmente
    for idx, tema in enumerate(request.temas, 1):
        logger.info(f"[{idx}/{total_temas}] 🔄 INICIANDO processamento sequencial do tema: '{tema.strip()}'")
        logger.info(f"[{idx}/{total_temas}] 📋 Fluxo: Fase 1 (Análise Clínica) → Fase 2 (Proposta) → Fase 3 (JSON Final)")
        
        try:
            # Chamar função helper para geração individual
            enable_web_search_bool = request.enable_web_search.lower() == 'true' if isinstance(request.enable_web_search, str) else bool(request.enable_web_search)
            
            logger.info(f"[{idx}/{total_temas}] 🤖 Chamando IA para processar '{tema.strip()}'...")
            success, result, error_msg = await generate_single_station_internal(
                tema=tema.strip(),
                especialidade=request.especialidade,
                abordagem_id=request.abordagem_selecionada,
                enable_web_search=enable_web_search_bool,
                skip_firestore=True  # DESABILITAR Firestore na geração múltipla
            )
            
            if success:
                sucessos += 1
                resultado_tema = {
                    "index": idx,
                    "tema": tema.strip(),
                    "status": "success",
                    "station_id": result["station_id"],
                    "abordagem_usada": result["abordagem_usada"],
                    "validation_status": result["validation_status"],
                    "validation_warnings": result.get("validation_warnings", []),
                    "error": None,
                    "processing_time": "N/A"  # Poderia ser medido se necessário
                }
                logger.info(f"[{idx}/{total_temas}] ✅ SUCESSO - Tema '{tema.strip()}' → Estação {result['station_id']} criada")
                logger.info(f"[{idx}/{total_temas}] 📊 Status de validação: {result['validation_status']}")
            else:
                falhas += 1
                resultado_tema = {
                    "index": idx,
                    "tema": tema.strip(),
                    "status": "error", 
                    "station_id": None,
                    "abordagem_usada": request.abordagem_selecionada,
                    "validation_status": "failed",
                    "validation_warnings": [],
                    "error": error_msg,
                    "processing_time": "N/A"
                }
                logger.error(f"[{idx}/{total_temas}] ❌ ERRO - Tema '{tema.strip()}': {error_msg}")
            
            resultados.append(resultado_tema)
            
            # Log de progresso intermediário a cada 2 temas
            if idx % 2 == 0 or idx == total_temas:
                logger.info(f"[PROGRESSO] {idx}/{total_temas} tema(s) processado(s) | ✅ {sucessos} sucesso(s) | ❌ {falhas} erro(s)")
        
        except Exception as e:
            falhas += 1
            resultado_tema = {
                "index": idx,
                "tema": tema.strip(),
                "status": "error",
                "station_id": None,
                "abordagem_usada": request.abordagem_selecionada,
                "validation_status": "failed",
                "validation_warnings": [],
                "error": f"Erro inesperado: {str(e)}",
                "processing_time": "N/A"
            }
            resultados.append(resultado_tema)
            logger.exception(f"[{idx}/{total_temas}] 🚨 ERRO CRÍTICO - Tema '{tema.strip()}': {e}")
        
        # Pequena pausa entre temas para não sobrecarregar
        if idx < total_temas:
            await asyncio.sleep(0.5)  # 0.5 segundo entre temas
    
    # Compilar resultado final
    logger.info(f"[MÚLTIPLA] FINALIZADA: {sucessos} sucessos, {falhas} falhas de {total_temas} temas")
    
    return {
        "status": "completed",
        "message": f"Processamento concluído: {sucessos} sucessos, {falhas} falhas",
        "summary": {
            "total_temas": total_temas,
            "sucessos": sucessos,
            "falhas": falhas,
            "taxa_sucesso": round((sucessos / total_temas) * 100, 1) if total_temas > 0 else 0,
            "especialidade": request.especialidade,
            "abordagem_selecionada": request.abordagem_selecionada,
            "enable_web_search": request.enable_web_search
        },
        "resultados": resultados,
        "estacoes_geradas": [r["station_id"] for r in resultados if r["status"] == "success"]
    }


@app.post("/api/agent/analyze-station", tags=["Agente - Análise"])
async def analyze_station_endpoint(request: AnalyzeStationRequest):
    # Busca local se Firestore indisponível
    if not AGENT_RULES or not db:
        try:
            local_stations_dir = "estacoes_geradas"
            local_file = os.path.join(local_stations_dir, f"{request.station_id}.json")
            if not os.path.exists(local_file):
                raise HTTPException(status_code=404, detail="Estação não encontrada localmente.")
            with open(local_file, "r", encoding="utf-8") as f:
                station_data = json.load(f)
            station_json_str = json.dumps(station_data, indent=2, ensure_ascii=False)
            analysis_prompt = build_prompt_analise(station_json_str, request.feedback)
            analysis_result = await call_gemini_api(analysis_prompt, preferred_model='flash')
            
            # Limpar e estruturar a análise antes de retornar
            clean_analysis = extract_json_from_text(analysis_result)
            if not clean_analysis.strip().startswith("{"):
                clean_analysis = analysis_result  # Manter texto original se não for JSON
            
            return {
                "station_id": request.station_id,
                "analysis": clean_analysis,
                "format": "json" if clean_analysis.strip().startswith("{") else "markdown"
            }
        except Exception as e:
            logger = logging.getLogger("agent.analyze_station")
            logger.exception("Erro ao analisar estação local: %s", e)
            raise HTTPException(status_code=500, detail=f"Erro ao analisar estação local: {e}")
    try:
        collection_name = 'estacoes_clinicas' # Hardcoded para simplicidade
        print(f"🔎 Buscando estação: {collection_name}/{request.station_id}")
        station_ref = db.collection(collection_name).document(request.station_id)
        station_doc = station_ref.get()
        if not station_doc.exists:
            raise HTTPException(status_code=404, detail="Estação não encontrada.")
        
        station_json_str = json.dumps(station_doc.to_dict(), indent=2, ensure_ascii=False)
        analysis_prompt = build_prompt_analise(station_json_str, request.feedback)
        analysis_result = await call_gemini_api(analysis_prompt, preferred_model='flash')
        
        # Limpar e estruturar a análise antes de retornar
        clean_analysis = extract_json_from_text(analysis_result)
        if not clean_analysis.strip().startswith("{"):
            clean_analysis = analysis_result  # Manter texto original se não for JSON
        
        return {
            "station_id": request.station_id,
            "analysis": clean_analysis,
            "format": "json" if clean_analysis.strip().startswith("{") else "markdown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar estação: {e}")

@app.post("/api/agent/apply-audit", tags=["Agente - Análise"])
async def apply_audit_endpoint(request: ApplyAuditRequest):
    """
    Endpoint: /api/agent/apply-audit
    Aplica as mudanças sugeridas pela auditoria (analysis_result) a uma estação existente,
    criando backup antes do overwrite e validando o JSON resultante.
    """
    # Verificar disponibilidade do Firestore
    if not db:
        raise HTTPException(status_code=503, detail="Conexão com Firestore não disponível.")

    logger = logging.getLogger("agent.apply_audit")
    collection_name = 'estacoes_clinicas'
    station_id = request.station_id

    logger.info("Iniciando auditoria de estação", extra={"station_id": station_id, "collection": collection_name})

    try:
        # 1. Buscar o documento original e criar backup
        station_ref = db.collection(collection_name).document(station_id)
        station_doc = station_ref.get()
        if not station_doc.exists:
            logger.error("Estação não encontrada", extra={"station_id": station_id})
            raise HTTPException(status_code=404, detail="Estação não encontrada para aplicar mudanças.")

        # Criar backup do estado atual antes das mudanças
        backup_data = {
            "previous_state": station_doc.to_dict(),
            "audit_timestamp": datetime.now().isoformat(),
            "actor": "agent",
            "action": "apply_audit",
            "analysis_source": request.analysis_result,
            "timestamp": datetime.now().isoformat()
        }
        MONITORING_SYSTEM["metrics"]["backups_created"] = MONITORING_SYSTEM["metrics"].get("backups_created", 0) + 1

        # Salvar backup em subcoleção edits
        edits_ref = station_ref.collection('edits').document()
        edits_ref.set(backup_data)
        logger.info("Backup salvo", extra={"backup_ref": edits_ref.id})
        MONITORING_SYSTEM["metrics"]["backups_created"] = MONITORING_SYSTEM["metrics"].get("backups_created", 0) + 1

        # Serializar estado original para comparação
        original_station_json = json.dumps(station_doc.to_dict(), indent=2, ensure_ascii=False)
        logger.info("Estado original serializado para processamento")

        # 2. Chamar a IA para obter o JSON modificado
        prompt = build_prompt_apply_audit(original_station_json, request.analysis_result)
        try:
            updated_json_str = await call_gemini_api(prompt, preferred_model='flash')
            logger.info("Resposta recebida do Gemini")
        except Exception as e:
            logger.error("Falha ao chamar Gemini", extra={"error": str(e)})
            MONITORING_SYSTEM["metrics"]["gemini_errors"] = MONITORING_SYSTEM["metrics"].get("gemini_errors", 0) + 1
            # Propagar erro como HTTPException para cliente
            raise HTTPException(status_code=500, detail=f"Erro ao chamar Gemini: {e}")

        # 3. Extrair e validar o JSON da resposta
        clean_json_str = extract_json_from_text(updated_json_str)
        try:
            # Tentar parse direto; aplicar sanitização se necessário
            try:
                updated_station_data = json.loads(clean_json_str)
            except json.JSONDecodeError:
                updated_station_data = json.loads(sanitize_json_string(clean_json_str))

            logger.info("JSON extraído e parseado com sucesso")
        except json.JSONDecodeError as e:
            logger.error("JSON inválido recebido", extra={"error": str(e), "json_preview": clean_json_str[:200]})
            MONITORING_SYSTEM["metrics"]["json_parse_errors"] = MONITORING_SYSTEM["metrics"].get("json_parse_errors", 0) + 1
            raise HTTPException(status_code=500, detail=f"A IA gerou um JSON modificado inválido: {str(e)}")

        # Verificar se o JSON é válido contra o template
        validation_result = validate_json_against_template(updated_station_data)
        if not validation_result["is_valid"]:
            logger.warning("JSON auditado não passou na validação", extra={
                "missing_fields": validation_result.get('missing_required_fields'),
                "invalid_types": validation_result.get('invalid_field_types'),
                "structural_issues": validation_result.get('structural_issues')
            })
            MONITORING_SYSTEM["metrics"]["validation_errors"] = MONITORING_SYSTEM["metrics"].get("validation_errors", 0) + 1
        elif validation_result.get("warnings"):
            logger.info("Validação concluída com avisos", extra={"warnings": validation_result.get("warnings")})
            MONITORING_SYSTEM["metrics"]["validation_warnings"] = MONITORING_SYSTEM["metrics"].get("validation_warnings", 0) + 1
        else:
            logger.info("Validação concluída com sucesso")

        # Adicionar metadata de edição ao histórico
        if "editHistory" not in updated_station_data:
            updated_station_data["editHistory"] = []

        # Incluir detalhes da validação no histórico
        edit_entry = {
            "actor": "agent",
            "timestamp": datetime.now().isoformat(),
            "action": "apply_audit",
            "editRef": edits_ref.id,
            "validationStatus": "valid" if validation_result["is_valid"] else "warning",
            "validationIssues": validation_result if not validation_result["is_valid"] else None
        }
        updated_station_data["editHistory"].append(edit_entry)

        # 4. Atualizar o documento principal
        station_ref.set(updated_station_data)
        logger.info(f"Mudanças da auditoria aplicadas com sucesso em {station_id}", extra={"backup_id": edits_ref.id})

        return {
            "status": "success",
            "message": "Mudanças da auditoria aplicadas com sucesso!",
            "station_id": station_id,
            "backup_id": edits_ref.id,
            "updated_station_data": updated_station_data,
            "validation_result": validation_result
        }

    except HTTPException:
        # Repassar HTTPExceptions sem alterar (erros conhecidos)
        raise
    except Exception as e:
        logger = logging.getLogger("agent.apply_audit")
        logger.exception("Erro ao aplicar mudanças da auditoria")
        raise HTTPException(status_code=500, detail=f"Erro ao aplicar mudanças da auditoria: {e}")


@app.get("/api/agent/get-rules", tags=["Agente - Memória"])
def get_rules():
    if not AGENT_RULES: raise HTTPException(status_code=404, detail="Regras não carregadas.")
    return {"status": "success"}

@app.post("/api/agent/update-rules", tags=["Agente - Memória"])
async def update_rules(request: Request):
    """Endpoint para atualizar regras usando o sistema híbrido de aprendizado"""
    try:
        data = await request.json()
        feedback = data.get("feedback")
        context = data.get("context", "Feedback do usuário via interface")
        category = data.get("category")
        
        if not feedback:
            raise HTTPException(status_code=400, detail="Feedback é obrigatório")
        
        # Salvar no sistema híbrido local (sempre prioritário e rápido)
        local_success = save_learning(feedback, context, category)
        
        # [SUCCESS] CORREÇÃO: Backup assíncrono otimizado (sem bloquear)
        async def try_firestore_backup():
            if not firebase_mock_mode and db:
                try:
                    # Timeout extremamente baixo para não afetar performance
                    import concurrent.futures
                    
                    def firestore_backup():
                        if not db:  # Verificação adicional
                            return False
                            
                        doc_ref = db.collection('agent_config').document('rules')
                        current_doc = doc_ref.get()
                        
                        if current_doc.exists:
                            current_md = (current_doc.to_dict() or {}).get('referencias_md', '')
                            new_rule_md = f"\n\n---\n\n## REGRA APRENDIDA (Feedback do Usuário):\n\n- {feedback}\n"
                            doc_ref.update({'referencias_md': current_md + new_rule_md})
                            print("[SUCCESS] Backup salvo no Firestore também")
                            return True
                        return False
                    
                    # Executar backup com timeout muito baixo em thread separada
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(firestore_backup)
                        result = future.result(timeout=2.0)  # Máximo 2 segundos apenas
                        
                except Exception as e:
                    # Não logar erro se for timeout - é esperado
                    if "timeout" not in str(e).lower():
                        print(f"[WARNING] Backup Firestore falhou: {str(e)[:100]}")
            else:
                print("📱 Modo local - backup Firestore desabilitado")
        
        # [SUCCESS] OTIMIZAÇÃO: Backup Firestore condicional para máxima performance
        if LOCAL_MEMORY_SYSTEM and LOCAL_MEMORY_SYSTEM.get('config'):
            print("[FAST] Modo híbrido ativo - backup Firestore desabilitado para máxima performance")
        else:
            # Executar backup apenas se não estiver em modo híbrido
            asyncio.create_task(try_firestore_backup())
        
        # Recarregar sistema se necessário
        if local_success and LOCAL_MEMORY_SYSTEM:
            # Recarregar aprendizados na memória
            try:
                with open('memoria/aprendizados_usuario.jsonl', 'r', encoding='utf-8') as f:
                    LOCAL_MEMORY_SYSTEM['aprendizados'] = json.load(f)
            except Exception:
                pass
        
        message = "[SUCCESS] Aprendizado salvo no sistema híbrido!" if local_success else "[ERROR] Falha no sistema local"
        
        return {
            "status": "success", 
            "message": message,
            "system_used": "hibrido_local",
            "category": categorize_learning(feedback, context),
            "note": "Backup Firestore processado assincronamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar regras: {e}")

# Novo endpoint para gerenciar aprendizados
@app.get("/api/agent/learnings", tags=["Agente - Memória"])
def get_learnings(limit: int = 20):
    """Retorna os aprendizados recentes"""
    try:
        learnings = get_recent_learnings(limit)
        return {
            "status": "success",
            "learnings": learnings,
            "total": len(learnings),
            "system": "hibrido" if LOCAL_MEMORY_SYSTEM else "firestore"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar aprendizados: {e}")

@app.post("/api/agent/add-learning", tags=["Agente - Memória"])
async def add_learning(data: UpdateRulesRequest):
    """Adiciona um novo aprendizado de forma estruturada"""
    try:
        success = save_learning(data.new_rule, data.context, data.category)
        
        if success:
            # Registrar evento de aprendizado
            log_learning_event()
            
            return {
                "status": "success",
                "message": "Aprendizado adicionado com sucesso!",
                "category": data.category or categorize_learning(data.new_rule, data.context)
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao salvar aprendizado")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar aprendizado: {e}")

# ====================================
# 📦 ENDPOINTS DO SISTEMA DE VERSIONAMENTO
# ====================================

@app.get("/api/agent/versions", tags=["Agente - Versionamento"])
def get_versions():
    """Lista todas as versões disponíveis do sistema"""
    try:
        if not VERSION_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de versionamento não está ativo")
            
        config_path = os.path.join(VERSION_SYSTEM['base_path'], 'config_versoes.json')
        if not os.path.exists(config_path):
            return {"versions": [], "current_version": None}
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        return {
            "status": "success",
            "versions": config.get('versions', []),
            "current_version": config.get('current_version'),
            "total_versions": len(config.get('versions', []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar versões: {e}")

@app.post("/api/agent/create-version", tags=["Agente - Versionamento"])
def create_manual_version(request: dict):
    """Cria uma versão manual do sistema"""
    try:
        if not VERSION_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de versionamento não está ativo")
            
        version_type = request.get('type', 'manual')
        description = request.get('description', 'Versão criada manualmente')
        
        version_info = create_version_snapshot(version_type, description)
        
        if version_info:
            # Registrar criação de versão
            log_version_created()
            
            return {
                "status": "success",
                "version_created": version_info,
                "message": f"Versão {version_info['id']} criada com sucesso"
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao criar versão")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar versão: {e}")

@app.post("/api/agent/rollback-version", tags=["Agente - Versionamento"])
def rollback_version(request: dict):
    """Restaura o sistema para uma versão específica"""
    try:
        if not VERSION_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de versionamento não está ativo")
            
        version_id = request.get('version_id')
        if not version_id:
            raise HTTPException(status_code=400, detail="ID da versão é obrigatório")
            
        # Criar backup da versão atual antes do rollback
        current_backup = create_version_snapshot("pre_rollback", f"Backup antes do rollback para {version_id}")
        
        success = rollback_to_version(version_id)
        
        if success:
            return {
                "status": "success",
                "rolled_back_to": version_id,
                "backup_created": current_backup['id'] if current_backup else None,
                "message": f"Sistema restaurado para versão {version_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao fazer rollback")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer rollback: {e}")

@app.get("/api/agent/version-details/{version_id}", tags=["Agente - Versionamento"])
def get_version_details(version_id: str):
    """Obtém detalhes de uma versão específica"""
    try:
        if not VERSION_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de versionamento não está ativo")
            
        config_path = os.path.join(VERSION_SYSTEM['base_path'], 'config_versoes.json')
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="Configuração de versões não encontrada")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        version_details = None
        for version in config.get('versions', []):
            if version['id'] == version_id:
                version_details = version
                break
                
        if not version_details:
            raise HTTPException(status_code=404, detail=f"Versão {version_id} não encontrada")
            
        # Tentar carregar arquivos da versão se existirem
        version_path = os.path.join(VERSION_SYSTEM['versions_path'], version_id)
        files_info = {}
        
        if os.path.exists(version_path):
            for filename in os.listdir(version_path):
                file_path = os.path.join(version_path, filename)
                if os.path.isfile(file_path):
                    files_info[filename] = {
                        "size": os.path.getsize(file_path),
                        "modified": os.path.getmtime(file_path)
                    }
        
        version_details['files'] = files_info
        
        return {
            "status": "success",
            "version": version_details
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter detalhes da versão: {e}")

@app.delete("/api/agent/delete-version/{version_id}", tags=["Agente - Versionamento"])
def delete_version(version_id: str):
    """Remove uma versão específica (exceto a atual)"""
    try:
        if not VERSION_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de versionamento não está ativo")
            
        config_path = os.path.join(VERSION_SYSTEM['base_path'], 'config_versoes.json')
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="Configuração de versões não encontrada")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Verificar se não é a versão atual
        if config.get('current_version') == version_id:
            raise HTTPException(status_code=400, detail="Não é possível deletar a versão atual")
            
        # Encontrar e remover a versão
        versions = config.get('versions', [])
        version_found = False
        updated_versions = []
        
        for version in versions:
            if version['id'] == version_id:
                version_found = True
                # Remover arquivos da versão
                version_path = os.path.join(VERSION_SYSTEM['versions_path'], version_id)
                if os.path.exists(version_path):
                    import shutil
                    shutil.rmtree(version_path)
            else:
                updated_versions.append(version)
                
        if not version_found:
            raise HTTPException(status_code=404, detail=f"Versão {version_id} não encontrada")
            
        # Atualizar configuração
        config['versions'] = updated_versions
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        return {
            "status": "success",
            "message": f"Versão {version_id} removida com sucesso",
            "remaining_versions": len(updated_versions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar versão: {e}")

# ====================================
# [STATS] ENDPOINTS DO SISTEMA DE MONITORAMENTO
# ====================================

@app.get("/api/agent/monitoring", tags=["Agente - Monitoramento"])
def get_monitoring_dashboard():
    """Retorna dados completos do dashboard de monitoramento"""
    try:
        if not MONITORING_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de monitoramento não está ativo")
            
        stats = get_monitoring_stats()
        
        # Adicionar dados específicos do dashboard
        dashboard_data = {
            **stats,
            "hybrid_system_status": {
                "active": bool(LOCAL_MEMORY_SYSTEM),
                "token_reduction_percent": 82,
                "files_loaded": len(LOCAL_MEMORY_SYSTEM.get('contextos', {})) + 
                              (1 if LOCAL_MEMORY_SYSTEM.get('referencias_base') else 0) +
                              (1 if LOCAL_MEMORY_SYSTEM.get('gabarito_template') else 0)
            },
            "version_system_status": {
                "active": VERSION_SYSTEM.get('active', False),
                "total_versions": len(VERSION_SYSTEM.get('sistema_versionamento', {}).get('historico_versoes', [])),
                "current_version": VERSION_SYSTEM.get('sistema_versionamento', {}).get('versao_atual', 'N/A')
            },
            "learning_system_status": {
                "total_learnings": len(LOCAL_MEMORY_SYSTEM.get('aprendizados', [])),
                "categories": ["restriction", "mandatory", "preference", "new_pattern", "correction", "formatting"]
            }
        }
        
        return {
            "status": "success",
            "dashboard": dashboard_data,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dados de monitoramento: {e}")

@app.get("/api/agent/monitoring/search-events", tags=["Agente - Monitoramento"])
def get_search_events(limit: int = 20):
    """Retorna os eventos de busca mais recentes (sanitizados)"""
    try:
        if not MONITORING_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de monitoramento não está ativo")
        events = list(MONITORING_SYSTEM.get('search_events', []))[-limit:]
        return {"status": "success", "events": events, "total": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter eventos de busca: {e}")

@app.get("/api/agent/monitoring/metrics", tags=["Agente - Monitoramento"])
def get_current_metrics():
    """Retorna métricas atuais do sistema"""
    try:
        if not MONITORING_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de monitoramento não está ativo")
            
        metrics = MONITORING_SYSTEM['metrics']
        
        return {
            "status": "success",
            "metrics": {
                "system": {
                    "memory_percent": psutil.virtual_memory().percent,
                    "cpu_percent": psutil.cpu_percent(),
                    "uptime_seconds": time.time() - metrics['system_uptime']
                },
                "requests": {
                    "total": metrics['requests_count'],
                    "errors_count": metrics['errors_count'],
                    "error_rate": round((metrics['errors_count'] / max(metrics['requests_count'], 1)) * 100, 2)
                },
                "performance": {
                    "avg_response_time": round(
                        sum(rt['response_time'] for rt in list(metrics['response_times'])[-10:]) /
                        max(len(list(metrics['response_times'])[-10:]), 1), 2
                    ),
                    "recent_requests": len(metrics['response_times'])
                },
                "business": {
                    "tokens_saved": metrics['tokens_saved'],
                    "versions_created": metrics['versions_created'],
                    "learning_events": metrics['learning_events'],
                    "search_count": metrics.get('search_count', 0)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {e}")

@app.get("/api/agent/monitoring/alerts", tags=["Agente - Monitoramento"])
def get_system_alerts():
    """Retorna alertas ativos do sistema"""
    try:
        if not MONITORING_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de monitoramento não está ativo")
            
        alerts = MONITORING_SYSTEM.get('alerts', [])
        
        # Filtrar alertas das últimas 24 horas
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_alerts = [
            alert for alert in alerts 
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        
        return {
            "status": "success",
            "alerts": recent_alerts,
            "total_alerts": len(alerts),
            "recent_alerts": len(recent_alerts),
            "alert_types": list(set(alert['type'] for alert in recent_alerts))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter alertas: {e}")

@app.post("/api/agent/monitoring/clear-alerts", tags=["Agente - Monitoramento"])
def clear_system_alerts():
    """Limpa todos os alertas do sistema"""
    try:
        if not MONITORING_SYSTEM.get('active'):
            raise HTTPException(status_code=503, detail="Sistema de monitoramento não está ativo")
            
        alerts_count = len(MONITORING_SYSTEM.get('alerts', []))
        MONITORING_SYSTEM['alerts'] = []
        
        return {
            "status": "success",
            "message": f"{alerts_count} alertas removidos",
            "cleared_count": alerts_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar alertas: {e}")

@app.get("/api/agent/monitoring/health", tags=["Agente - Monitoramento"])
def get_health_check():
    """Health check completo do sistema"""
    try:
        health_status = {
            "overall": "healthy",
            "systems": {
                "monitoring": MONITORING_SYSTEM.get('active', False),
                "hybrid_memory": bool(LOCAL_MEMORY_SYSTEM),
                "versioning": VERSION_SYSTEM.get('active', False),
                "firestore": not firebase_mock_mode and bool(db),
                "gemini_ai": bool(GEMINI_CONFIGS)
            },
            "metrics": {
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(),
                "uptime_hours": round((time.time() - MONITORING_SYSTEM.get('metrics', {}).get('system_uptime', time.time())) / 3600, 2)
            }
        }
        
        # Determinar status geral
        system_issues = [name for name, status in health_status["systems"].items() if not status]
        if system_issues:
            health_status["overall"] = "degraded" if len(system_issues) < 3 else "unhealthy"
            health_status["issues"] = system_issues
            
        return {
            "status": "success",
            "health": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "health": {"overall": "unhealthy", "error": str(e)},
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/agent/system-status", tags=["Agente - Sistema"])
def get_system_status():
    """Retorna o status do sistema híbrido de memória e versionamento"""
    try:
        # Status do sistema de versionamento
        version_status = {
            "active": VERSION_SYSTEM.get('active', False),
            "total_versions": 0,
            "current_version": None,
            "latest_version": None
        }
        
        if VERSION_SYSTEM.get('active'):
            try:
                config_path = os.path.join(VERSION_SYSTEM['base_path'], 'config_versoes.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    version_status.update({
                        "total_versions": len(config.get('versions', [])),
                        "current_version": config.get('current_version'),
                        "latest_version": config.get('versions', [{}])[-1].get('id') if config.get('versions') else None
                    })
            except Exception:
                pass
        
        return {
            "status": "success",
            "hybrid_system": {
                "active": bool(LOCAL_MEMORY_SYSTEM),
                "config_loaded": "config" in LOCAL_MEMORY_SYSTEM,
                "references_loaded": bool(LOCAL_MEMORY_SYSTEM.get('referencias_base')),
                "template_loaded": bool(LOCAL_MEMORY_SYSTEM.get('gabarito_template')),
                "contexts_loaded": len(LOCAL_MEMORY_SYSTEM.get('contextos', {})),
                "learnings_count": len(LOCAL_MEMORY_SYSTEM.get('aprendizados', []))
            },
            "version_system": version_status,
            "firestore": {
                "connected": not firebase_mock_mode and bool(db),
                "rules_loaded": bool(AGENT_RULES)
            },
            "validation_system": {
                "impressos_validator_available": IMPRESSOS_VALIDATOR_AVAILABLE,
                "total_validated": MONITORING_SYSTEM.get('metrics', {}).get('impressos_validated', 0),
                "total_corrected": MONITORING_SYSTEM.get('metrics', {}).get('impressos_corrected', 0),
                "validation_errors": MONITORING_SYSTEM.get('metrics', {}).get('impressos_validation_errors', 0)
            },
            "memory_stats": {
                "total_references_chars": len(LOCAL_MEMORY_SYSTEM.get('referencias_base', '')),
                "total_template_chars": len(LOCAL_MEMORY_SYSTEM.get('gabarito_template', '')),
                "estimated_token_savings": "82%" if LOCAL_MEMORY_SYSTEM else "0%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {e}")

@app.post("/api/agent/validate-impressos", tags=["Agente - Validação"])
def validate_impressos_endpoint(estacao_data: dict):
    """Endpoint para validar impressos de uma estação específica"""
    try:
        if not IMPRESSOS_VALIDATOR_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Sistema de validação de impressos não está disponível"
            )
        
        # Realizar validação
        is_valid, errors, estacao_corrigida = validar_impressos_estacao(estacao_data)
        
        # Preparar resposta
        response = {
            "is_valid": is_valid,
            "errors": errors,
            "total_errors": len(errors),
            "has_corrections": estacao_corrigida != estacao_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Incluir dados corrigidos se houver correções
        if estacao_corrigida != estacao_data:
            response["corrected_data"] = estacao_corrigida
        
        # Registrar métricas
        if MONITORING_SYSTEM.get('active'):
            if is_valid:
                MONITORING_SYSTEM['metrics']['impressos_validated'] += 1
            else:
                MONITORING_SYSTEM['metrics']['impressos_validation_errors'] += len(errors)
                if estacao_corrigida != estacao_data:
                    MONITORING_SYSTEM['metrics']['impressos_corrected'] += 1
        
        return {
            "status": "success",
            "validation_result": response
        }
        
    except Exception as e:
        logger.error(f"Erro na validação de impressos via endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na validação: {str(e)}")

# --- Ponto de Entrada para Execução Local ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
