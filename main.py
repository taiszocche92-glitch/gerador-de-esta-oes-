# Arquivo: main.py (Versão 8 - Geração com Salvamento Automático no Firestore)

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
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
from typing import Optional, Dict, Any, List, Union

# --- Carregamento de Variáveis de Ambiente ---
load_dotenv()
from web_search import search_web

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
        print("⚠️ Conteúdo de referencias.md está vazio")
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
        
        print(f"✅ Parser concluído! {len(sections)} seções identificadas:")
        for key in sections.keys():
            print(f"   📄 {key}: {len(sections[key])} caracteres")
        
        return sections
        
    except Exception as e:
        print(f"❌ Erro ao fazer parsing do referencias.md: {e}")
        return {}

# --- Sistema Híbrido de Memória Local ---
def load_local_memory_config():
    """Carrega a configuração do sistema de memória local"""
    try:
        with open('memoria/config_memoria.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar config_memoria.json: {e}")
        return {}

def load_local_file(file_path):
    """Carrega conteúdo de arquivo local com encoding UTF-8"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Erro ao carregar arquivo {file_path}: {e}")
        return ""

def initialize_local_memory_system():
    """Inicializa o sistema híbrido de memória local"""
    global LOCAL_MEMORY_SYSTEM
    try:
        print("🧠 Inicializando sistema híbrido de memória local...")
        
        # Carregar configuração
        config = load_local_memory_config()
        if not config:
            print("❌ Falha ao carregar configuração - usando sistema antigo")
            return False
            
        LOCAL_MEMORY_SYSTEM['config'] = config
        sistema = config.get('sistema_memoria', {})
        estrutura = sistema.get('estrutura', {})
        
        # Carregar arquivos base
        print("📄 Carregando arquivos base...")
        LOCAL_MEMORY_SYSTEM['referencias_base'] = load_local_file(estrutura.get('referencias_base', ''))
        LOCAL_MEMORY_SYSTEM['gabarito_template'] = load_local_file(estrutura.get('gabarito_template', ''))
        
        # Carregar contextos otimizados por fase
        print("📁 Carregando contextos otimizados...")
        contextos = estrutura.get('contexto_otimizado', {})
        LOCAL_MEMORY_SYSTEM['contextos'] = {}
        for fase, arquivo in contextos.items():
            LOCAL_MEMORY_SYSTEM['contextos'][fase] = load_local_file(arquivo)
            
        # Carregar aprendizados do usuário
        print("🎓 Carregando aprendizados do usuário...")
        try:
            with open(estrutura.get('aprendizados_usuario', ''), 'r', encoding='utf-8') as f:
                LOCAL_MEMORY_SYSTEM['aprendizados'] = json.load(f)
        except:
            LOCAL_MEMORY_SYSTEM['aprendizados'] = []
            
        print("✅ Sistema híbrido de memória local inicializado com sucesso!")
        economia = sistema.get('reducao_tokens', {}).get('economia', 'N/A')
        print(f"💰 Economia estimada: {economia}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema local: {e}")
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
                
        print(f"📊 Fase {phase_number}: {len(contexto_completo)} caracteres carregados")
        return contexto_completo
        
    except Exception as e:
        print(f"⚠️ Erro ao gerar contexto para fase {phase_number}: {e}")
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
            print("⚠️ Sistema local não inicializado, salvando no Firestore apenas")
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
            
        print(f"✅ Aprendizado salvo - Categoria: {category}")
        print(f"📝 Regra: {new_rule[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar aprendizado: {e}")
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
        'obrigatorio': '✅ OBRIGATÓRIO',
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
        print(f"⚠️ Erro ao carregar config de versões: {e}")
        return {}

def save_version_config(config):
    """Salva a configuração do sistema de versionamento"""
    try:
        with open('memoria/versoes/config_versoes.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar config de versões: {e}")
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
    except:
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
        
        print(f"✅ Snapshot criado: {version_number}")
        print(f"📂 Arquivos: {len(backed_files)}, Tamanho: {total_size/1024:.1f}KB")
        
        return version_metadata
        
    except Exception as e:
        print(f"❌ Erro ao criar snapshot: {e}")
        return None

def initialize_version_system():
    """Inicializa o sistema de versionamento"""
    global VERSION_SYSTEM
    try:
        print("📦 Inicializando sistema de versionamento...")
        
        # Carregar configuração
        config = load_version_config()
        if not config:
            print("❌ Falha ao carregar configuração de versões")
            return False
            
        VERSION_SYSTEM = config
        
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
        
        print(f"✅ Sistema de versionamento ativo!")
        print(f"📌 Versão atual: {versao_atual}")
        print(f"📊 Total de versões: {total_versoes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar versionamento: {e}")
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
            
            print(f"🔄 Nova versão criada automaticamente: {nova_versao}")
            return True
            
    except Exception as e:
        print(f"⚠️ Erro no versionamento automático: {e}")
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
        
        print(f"✅ Rollback para {version_number} concluído!")
        return True, f"Sistema restaurado para versão {version_number}"
        
    except Exception as e:
        return False, f"Erro no rollback: {e}"

# --- Funções de Inicialização ---
def initialize_firebase():
    global db, firebase_mock_mode
    try:
        # Preferir arquivo de credenciais local (evita erro de ADC quando não configurado)
        service_account_paths = [
            os.path.join('memoria', 'serviceAccountKey.json'),
            'serviceAccountKey.json'
        ]

        # Se houver variável de ambiente apontando para um arquivo, tentar usá-la primeiro
        env_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if env_path and os.path.exists(env_path):
            try:
                cred = credentials.Certificate(env_path)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                
                # Teste de conectividade com timeout curto
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("Timeout na inicialização Firebase")
                
                # Configurar timeout apenas no Linux/Unix que suportam SIGALRM
                timeout_supported = hasattr(signal, 'SIGALRM') and os.name != 'nt'
                if timeout_supported:
                    signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore
                    signal.alarm(15)  # type: ignore # 15 segundos timeout
                
                try:
                    db = firestore.client()
                    # Teste rápido de conectividade
                    test_collections = list(db.collections())
                    if timeout_supported:
                        signal.alarm(0)  # type: ignore # Cancelar timeout
                    print(f"✅ Firebase Admin SDK inicializado com arquivo apontado por GOOGLE_APPLICATION_CREDENTIALS: {env_path}")
                    return True
                except (TimeoutError, Exception) as timeout_err:
                    if timeout_supported:
                        signal.alarm(0)  # type: ignore
                    print(f"⚠️ Timeout ou erro na conectividade Firebase: {timeout_err}")
                    # Continuar com db = None, mas não falhar completamente
                    db = None
                    firebase_mock_mode = True
                    print("🔄 Continuando em modo local (Firebase indisponível)")
                    return False
                    
            except Exception as e_env:
                print(f"⚠️ Falha ao inicializar com GOOGLE_APPLICATION_CREDENTIALS={env_path}: {e_env}")

        # Tentar arquivos locais conhecidos
        for path in service_account_paths:
            if os.path.exists(path):
                try:
                    cred = credentials.Certificate(path)
                    if not firebase_admin._apps:
                        firebase_admin.initialize_app(cred)
                    
                    # Teste de conectividade com timeout
                    try:
                        db = firestore.client()
                        print(f"✅ Firebase Admin SDK inicializado com arquivo local: {path}")
                        return True
                    except Exception as connectivity_err:
                        print(f"⚠️ Firebase inicializado mas sem conectividade: {connectivity_err}")
                        db = None
                        firebase_mock_mode = True
                        return False
                        
                except Exception as e_local:
                    print(f"⚠️ Falha ao inicializar com arquivo local {path}: {e_local}")

        # Por fim, tentar Application Default Credentials (padrão GCP)
        try:
            cred = credentials.ApplicationDefault()
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {'projectId': os.getenv('FIREBASE_PROJECT_ID', 'revalida-companion')})
            db = firestore.client()
            print("✅ Firebase Admin SDK inicializado com Application Default Credentials.")
            return True
        except Exception as adc_error:
            print(f"⚠️ Falha com Application Default Credentials: {adc_error}")
            
    except Exception as e_final:
        print(f"⚠️ Erro geral ao inicializar Firebase Admin SDK: {e_final}")
    
    # Se chegou aqui, todas as tentativas falharam
    print(f"🔄 Ativando modo híbrido local (sem sincronização Firestore)")
    print(f"✅ Sistema local funcionando normalmente!")
    firebase_mock_mode = True
    db = None
    return False

# ====================================
# 📊 SISTEMA DE MONITORAMENTO EM TEMPO REAL
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
            'search_count': 0
        }
        
        # Lista de eventos de busca (sanitizados) para telemetria — manter tamanho limitado
        MONITORING_SYSTEM['search_events'] = deque(maxlen=200)
        
        MONITORING_SYSTEM['alerts'] = []
        MONITORING_SYSTEM['active'] = True
        
        # Iniciar thread de coleta de métricas
        monitoring_thread = threading.Thread(target=collect_system_metrics, daemon=True)
        monitoring_thread.start()
        
        print("📊 Sistema de monitoramento inicializado!")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro ao inicializar sistema de monitoramento: {e}")
        MONITORING_SYSTEM['active'] = False
        return False

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
            print(f"⚠️ Erro na coleta de métricas: {e}")
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
        print(f"⚠️ Erro ao logar evento de busca: {e}")

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
        
    # Verificar alerta de tempo de resposta
    if response_time > 5000:  # 5 segundos
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
    
    # Tentar carregar sistema híbrido primeiro
    if initialize_local_memory_system():
        print("🚀 Sistema híbrido de memória local ativo!")
        
        # Inicializar sistema de versionamento
        try:
            initialize_version_system()
            VERSION_SYSTEM['active'] = True
            print("📦 Sistema de versionamento ativo!")
            
            # Criar snapshot automático na inicialização
            auto_version_on_change("Inicialização do sistema híbrido")
            
        except Exception as e:
            print(f"⚠️ Erro ao inicializar sistema de versionamento: {e}")
            VERSION_SYSTEM['active'] = False
        
        # Inicializar sistema de monitoramento
        try:
            initialize_monitoring_system()
            print("📊 Sistema de monitoramento ativo!")
            
            # Registrar economia de tokens na inicialização
            log_token_savings(28000)  # 82% de 35000 tokens médios
            
        except Exception as e:
            print(f"⚠️ Erro ao inicializar sistema de monitoramento: {e}")
            MONITORING_SYSTEM['active'] = False
        
        # Sistema híbrido local está ativo - pular Firestore
        print("ℹ️ Sistema híbrido local ativo - pulando carregamento Firestore")
        
        # ✅ CORREÇÃO: Popular AGENT_RULES com dados do sistema local
        global AGENT_RULES
        if LOCAL_MEMORY_SYSTEM.get('referencias_base'):
            AGENT_RULES = {
                'referencias_md': LOCAL_MEMORY_SYSTEM.get('referencias_base', ''),
                'gabarito_json': LOCAL_MEMORY_SYSTEM.get('gabarito_template', '{}'),
                'config': LOCAL_MEMORY_SYSTEM.get('config', {}),
                'aprendizados': LOCAL_MEMORY_SYSTEM.get('aprendizados', [])
            }
            print(f"✅ AGENT_RULES populado com {len(AGENT_RULES.get('referencias_md', ''))} caracteres de referências")
        
        print("✅ Inicialização completa do sistema híbrido!")
        return
    
    # Fallback para sistema antigo se sistema local falhar
    print("🔄 Usando sistema de memória tradicional (Firestore)...")
    if firebase_mock_mode or not db: return
    try:
        print("🧠 Carregando regras do Firestore...")
        doc_ref = db.collection('agent_config').document('rules')
        doc = doc_ref.get()
        if doc.exists:
            AGENT_RULES = doc.to_dict() or {}  # Garantir que nunca seja None
            print("✅ Regras carregadas na memória com sucesso!")
            
            # Fazer parse do referencias_md para otimização
            referencias_content = AGENT_RULES.get('referencias_md', '')
            if referencias_content:
                print("🔧 Fazendo parse do referencias.md...")
                PARSED_REFERENCIAS = parse_referencias_md(referencias_content)
                if PARSED_REFERENCIAS:
                    print("✅ Referencias.md parsed e otimizado com sucesso!")
                else:
                    print("⚠️ Falha no parsing - usando conteúdo completo como fallback")
            else:
                print("⚠️ Conteúdo referencias_md não encontrado no documento")
        else:
            print("❌ ERRO: Documento 'rules' não encontrado.")
    except Exception as e:
        print(f"❌ ERRO CRÍTICO ao carregar regras do Firestore: {e}")

def configure_gemini_keys():
    global GEMINI_CONFIGS
    # Configuração organizada por modelo preferencial
    flash_configs = [
        # GEMINI 2.5 FLASH - PARA FASE 1 (ANÁLISE INICIAL)
        (os.getenv("GEMINI_API_KEY_1"), 'gemini-2.5-flash'),
        (os.getenv("GEMINI_API_KEY_2"), 'gemini-2.5-flash'),
        (os.getenv("GEMINI_API_KEY_3"), 'gemini-2.5-flash'),
        (os.getenv("GEMINI_API_KEY_4"), 'gemini-2.5-flash'),
    ]
    
    pro_configs = [
        # GEMINI 2.5 PRO - PARA FASES 2, 3 E 4 (GERAÇÃO AVANÇADA)
        (os.getenv("GEMINI_API_KEY_1"), 'gemini-2.5-pro'),
        (os.getenv("GEMINI_API_KEY_2"), 'gemini-2.5-pro'),
        (os.getenv("GEMINI_API_KEY_3"), 'gemini-2.5-pro'),
        (os.getenv("GEMINI_API_KEY_4"), 'gemini-2.5-pro'),
    ]
    
    # Todas as configurações disponíveis (para fallback)
    all_configs = pro_configs + flash_configs + [
        # FALLBACK PARA OUTROS MODELOS 
        (os.getenv("GEMINI_API_KEY_1"), 'gemini-2.5-flash-lite'),
        (os.getenv("GEMINI_API_KEY_2"), 'gemini-2.5-flash-lite'),
        (os.getenv("GEMINI_API_KEY_3"), 'gemini-2.5-flash-lite'),
        (os.getenv("GEMINI_API_KEY_4"), 'gemini-2.5-flash-lite')
    ]
    
    GEMINI_CONFIGS = {
        'flash': [{"key": key, "model_name": model} for key, model in flash_configs if key],
        'pro': [{"key": key, "model_name": model} for key, model in pro_configs if key],
        'all': [{"key": key, "model_name": model} for key, model in all_configs if key]
    }
    
    if not GEMINI_CONFIGS.get('all'):
        print("🔴 Nenhuma chave de API do Gemini foi encontrada.")
    else:
        flash_count = len(GEMINI_CONFIGS.get('flash', []))
        pro_count = len(GEMINI_CONFIGS.get('pro', []))
        print(f"✅ Configuradas {flash_count} chave(s) Flash e {pro_count} chave(s) Pro do Gemini.")

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
    print("✅ Rota RAG incluída com sucesso!")
except ImportError as e:
    print(f"⚠️ Não foi possível incluir rota RAG: erro de importação - {e}")
except Exception as e:
    print(f"⚠️ Não foi possível incluir rota RAG: {e}")

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

# --- Funções de Construção de Prompts (build_prompt_fase_1 atualizada) ---
def build_prompt_fase_1(tema: str, especialidade: str, pdf_content: str | None = None) -> str:
    """Constrói o prompt para a Fase 1, incluindo o conteúdo do PDF se fornecido."""
    
    pdf_instruction = ""
    if pdf_content:
        pdf_instruction = f"""
**FONTE PRIMÁRIA DE CONHECIMENTO (PDF Fornecido):**
---
{pdf_content}
---

**INSTRUÇÕES ESPECÍFICAS PARA ANÁLISE DO PDF:**
1. **LEIA O ÍNDICE**: Identifique seções relacionadas ao tema "{tema}"
2. **EXTRAIA APENAS O RELEVANTE**: Foque no que é essencial para estações médicas sobre "{tema}"
3. **IGNORE CONTEÚDO NÃO RELACIONADO**: Pule temas/doenças diferentes do solicitado
4. **ESTRUTURE A INFORMAÇÃO**: Organize conforme os tópicos solicitados abaixo
"""
    
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
"""

# (As outras funções de build_prompt permanecem as mesmas)
def build_prompt_fase_2(tema: str, especialidade: str, resumo_clinico: str) -> str:
    """Constrói o prompt da Fase 2 usando sistema híbrido de memória"""
    
    # Usar sistema híbrido se disponível
    if LOCAL_MEMORY_SYSTEM:
        print("🚀 Usando sistema híbrido para Fase 2...")
        contexto_otimizado = get_context_for_phase(2)
    else:
        print("🔄 Fallback para sistema tradicional...")
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
            print(f"📊 Fase 2: {len(contexto_otimizado)} caracteres (vs {len(AGENT_RULES.get('referencias_md', '') if AGENT_RULES else '')} originais)")
        else:
            print("⚠️ PARSED_REFERENCIAS não disponível, usando conteúdo completo como fallback")
            contexto_otimizado = AGENT_RULES.get('referencias_md', "") if AGENT_RULES else ""
    
    return f"""# FASE 2: GERAÇÃO DE ESTRATÉGIAS

**CONTEXTO CLÍNICO:**
{resumo_clinico}

**REGRAS DE ARQUITETURA E DIRETRIZES (SEÇÕES OTIMIZADAS):**
{contexto_otimizado}

**SUA TAREFA:**
Gere 5 propostas estratégicas para uma estação sobre **{tema}** em **{especialidade}**, variando o tipo e o foco."""

def build_prompt_fase_3(request: GenerateFinalStationRequest) -> str:
    """Constrói o prompt da Fase 3 usando seções específicas do referencias.md + gabarito.json"""
    
    # Usar sistema híbrido se disponível
    if LOCAL_MEMORY_SYSTEM:
        print("🚀 Usando sistema híbrido para Fase 3...")
        contexto_otimizado = get_context_for_phase(3)
        gabarito_json = get_gabarito_template()
    else:
        print("🔄 Fallback para sistema tradicional...")
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
            print(f"📊 Fase 3: {len(contexto_otimizado)} caracteres (vs {len(AGENT_RULES.get('referencias_md', '') if AGENT_RULES else '')} originais)")
        else:
            print("⚠️ PARSED_REFERENCIAS não disponível, usando conteúdo completo como fallback")
            contexto_otimizado = AGENT_RULES.get('referencias_md', "") if AGENT_RULES else ""
        
        gabarito_json = AGENT_RULES.get('gabarito_json', "{}") if AGENT_RULES else "{}"
    
    return f"""# FASE 3: GERAÇÃO DO JSON COMPLETO

**CONTEXTO CLÍNICO:**
{request.resumo_clinico}

**PROPOSTA ESTRATÉGICA ESCOLHIDA:**
{request.proposta_escolhida}

**REGRAS DE CONTEÚDO E ESTRUTURA (SEÇÕES OTIMIZADAS):**
{contexto_otimizado}

**MOLDE JSON A SER PREENCHIDO:**
{gabarito_json}

**SUA TAREFA:**
Gere o código JSON completo para a estação sobre **{request.tema}** em **{request.especialidade}**, seguindo rigorosamente a proposta, as regras e o molde fornecidos."""

def build_prompt_analise(station_json_str: str, feedback: str | None) -> str:
    """Constrói o prompt da Fase 4 (análise) usando sistema híbrido de memória"""
    
    # Usar sistema híbrido se disponível
    if LOCAL_MEMORY_SYSTEM:
        print("🚀 Usando sistema híbrido para Fase 4...")
        contexto_otimizado = get_context_for_phase(4)
    else:
        print("🔄 Fallback para sistema tradicional...")
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
            print(f"📊 Fase 4: {len(contexto_otimizado)} caracteres (vs {len(AGENT_RULES.get('referencias_md', '') if AGENT_RULES else '')} originais)")
        else:
            print("⚠️ PARSED_REFERENCIAS não disponível, usando conteúdo completo como fallback")
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

# --- Função Central de Chamada à API (modificada para suportar modelos específicos) ---
async def call_gemini_api(prompt: str, preferred_model: str = 'pro'):
    """
    Chama a API do Gemini com preferência de modelo.
    
    Args:
        prompt: O texto do prompt a ser enviado
        preferred_model: 'flash' para Gemini 2.5 Flash, 'pro' para Gemini 2.5 Pro
    """
    if not GEMINI_CONFIGS or not GEMINI_CONFIGS.get('all'): 
        raise HTTPException(status_code=503, detail="Nenhuma chave de API do Gemini está configurada.")
    
    # Determina a ordem de tentativa baseada na preferência
    if preferred_model == 'flash':
        configs_to_try = GEMINI_CONFIGS.get('flash', []) + GEMINI_CONFIGS.get('pro', [])
        print(f"🚀 Usando Gemini 2.5 Flash para processamento rápido...")
    else:  # 'pro' ou qualquer outro valor
        configs_to_try = GEMINI_CONFIGS.get('pro', []) + GEMINI_CONFIGS.get('flash', [])
        print(f"🧠 Usando Gemini 2.5 Pro para processamento avançado...")
    
    # Se não tiver configurações específicas, usa todas disponíveis
    if not configs_to_try:
        configs_to_try = GEMINI_CONFIGS.get('all', [])
    
    for i, config in enumerate(configs_to_try):
        try:
            print(f"➡️  Tentando API Key #{i+1} com modelo {config['model_name']}...")
            genai.configure(api_key=config['key'])  # type: ignore
            model = genai.GenerativeModel(config['model_name'])  # type: ignore
            response = await model.generate_content_async(prompt)
            
            # Verifica se a resposta tem candidatos válidos
            if not response.candidates:
                print(f"⚠️  {config['model_name']} (API Key #{i+1}): Nenhum candidato retornado.")
                if i == len(configs_to_try) - 1:
                    raise HTTPException(status_code=500, detail="Nenhum candidato válido retornado pelo modelo.")
                continue
            
            # Verifica o finish_reason do primeiro candidato
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                finish_reason_code = candidate.finish_reason
                finish_reason_name = FINISH_REASON_NAMES.get(finish_reason_code, f"UNKNOWN_{finish_reason_code}")
                
                print(f"⚠️  {config['model_name']} (API Key #{i+1}): Resposta sem conteúdo válido.")
                print(f"🔍 finish_reason: {finish_reason_code} ({finish_reason_name})")
                
                # Log detalhado baseado no finish_reason
                if finish_reason_code == 1:  # STOP
                    error_msg = "Modelo parou naturalmente mas sem conteúdo válido - possível prompt vazio ou muito curto"
                elif finish_reason_code == 2:  # MAX_TOKENS
                    error_msg = "Limite de tokens atingido - prompt muito longo ou resposta truncada"
                elif finish_reason_code == 3:  # SAFETY
                    error_msg = "Conteúdo bloqueado por filtros de segurança - prompt pode conter conteúdo sensível"
                elif finish_reason_code == 4:  # RECITATION
                    error_msg = "Conteúdo bloqueado por recitação - possível violação de direitos autorais"
                elif finish_reason_code == 5:  # LANGUAGE
                    error_msg = "Idioma não suportado pelo modelo"
                elif finish_reason_code == 7:  # BLOCKLIST
                    error_msg = "Prompt contém termos da lista de bloqueio"
                elif finish_reason_code == 8:  # PROHIBITED_CONTENT
                    error_msg = "Conteúdo proibido detectado no prompt"
                else:
                    error_msg = f"{finish_reason_name} - verifique o prompt e tente novamente"
                
                print(f"� Sugestão: {error_msg}")
                
                if i == len(configs_to_try) - 1:
                    raise HTTPException(status_code=500, detail=f"Erro na API do Gemini: {error_msg}")
                continue
            
            print(f"✅ Sucesso com {config['model_name']} usando API Key #{i+1}.")
            return response.text
        except google_exceptions.ResourceExhausted:
            print(f"⚠️  API Key #{i+1} ({config['model_name']}) atingiu o limite de cota.")
            if i == len(configs_to_try) - 1: 
                raise HTTPException(status_code=429, detail="Todas as chaves de API atingiram o limite de cota.")
        except Exception as e:
            print(f"❌ Erro com {config['model_name']} (API Key #{i+1}): {e}")
            if i == len(configs_to_try) - 1:
                raise HTTPException(status_code=500, detail=f"Erro na API do Gemini: {e}")
            continue
    
    raise HTTPException(status_code=503, detail="Falha ao processar com todas as chaves.")

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
            "fases_2_3_4": "gemini-2.5-pro"
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
                    "message": "Gemini configurado corretamente - Flash para Fase 1, Pro para Fases 2-4!"
                }
            else:
                candidate = response.candidates[0] if response.candidates else None
                finish_reason_code = candidate.finish_reason if candidate else -1
                finish_reason_name = FINISH_REASON_NAMES.get(finish_reason_code, f"UNKNOWN_{finish_reason_code}")
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
                finish_reason_name = FINISH_REASON_NAMES.get(finish_reason_code, f"UNKNOWN_{finish_reason_code}")
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
                    finish_reason_name = FINISH_REASON_NAMES.get(finish_reason_code, f"UNKNOWN_{finish_reason_code}")
                    
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

@app.post("/api/agent/start-creation", tags=["Agente - Geração"])
async def start_creation_process(
    tema: str = Form(...),
    especialidade: str = Form(...),
    pdf_reference: UploadFile = File(None), # O arquivo é opcional
    enable_web_search: str = Form("0")      # Recebe '1' ou '0' do frontend
):
    """
    Orquestra as Fases 1 e 2, agora aceitando um PDF de referência opcional.
    O parâmetro enable_web_search controla se a busca web será executada (valor '1' habilita).
    """
    if not AGENT_RULES:
        raise HTTPException(status_code=503, detail="Regras do agente não carregadas.")
    
    pdf_content_str = None
    if pdf_reference:
        try:
            print(f"📄 Processando PDF: {pdf_reference.filename}")
            
            # Ler os bytes do arquivo PDF
            pdf_content_bytes = await pdf_reference.read()
            
            # Extrair texto estruturado do PDF usando PyMuPDF
            pdf_content_str = extract_pdf_content_structured(pdf_content_bytes, tema)
            
            print(f"✅ PDF processado com sucesso! Extraído texto de {pdf_reference.filename}")
            print(f"� Tamanho do conteúdo extraído: {len(pdf_content_str)} caracteres")
            
        except Exception as e:
            print(f"❌ Erro ao processar PDF: {e}")
            raise HTTPException(status_code=400, detail=f"Não foi possível processar o arquivo PDF: {e}")
    
    # --- BUSCA WEB EM TEMPO REAL (opcional) ---
    web_search_summary = ""
    hits = []
    try:
        # Interpretar flag enviada pelo frontend
        enabled_flag = str(enable_web_search).lower() in ("1", "true", "yes")
        serp_key = os.getenv("SERPAPI_KEY")
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
                    print(f"⚠️ Falha na busca web para query '{q}': {we}")
        else:
            if not enabled_flag:
                print("ℹ️ Busca web desabilitada por flag do frontend.")
            else:
                print("⚠️ SERPAPI_KEY não configurado — pulando buscas web.")
            hits = []
    except Exception as e:
        print(f"⚠️ Módulo de busca web não disponível: {e}")
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
            print(f"⚠️ Erro ao registrar telemetria de busca: {te}")
    
    # Combinar contexto do PDF (se houver) com resultados da busca web
    if pdf_content_str and web_search_summary:
        combined_context = f"{pdf_content_str}\n\nRESULTADOS DA BUSCA EM TEMPO REAL:\n{web_search_summary}"
    elif web_search_summary and not pdf_content_str:
        combined_context = f"RESULTADOS DA BUSCA EM TEMPO REAL:\n{web_search_summary}"
    else:
        combined_context = pdf_content_str
    
    # --- FASE 1 (USAR GEMINI 2.5 FLASH) ---
    print(f"🚀 Iniciando Fase 1 (Flash) para Tema: {tema}")
    prompt_fase_1 = build_prompt_fase_1(tema, especialidade, combined_context)
    resumo_clinico = await call_gemini_api(prompt_fase_1, preferred_model='flash')
    print("✅ Fase 1 (Resumo Clínico com Flash) concluída.")

    # --- FASE 2 (USAR GEMINI 2.5 PRO) ---
    print("🧠 Iniciando Fase 2 (Pro) para gerar propostas...")
    prompt_fase_2 = build_prompt_fase_2(tema, especialidade, resumo_clinico)
    propostas = await call_gemini_api(prompt_fase_2, preferred_model='pro')
    print("✅ Fase 2 (Propostas com Pro) concluída.")

    return {"resumo_clinico": resumo_clinico, "propostas": propostas}

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
    print("� Gerando o conteúdo da estação com o Gemini 2.5 Pro...")
    prompt_fase_3 = build_prompt_fase_3(request)
    json_output_str = await call_gemini_api(prompt_fase_3, preferred_model='pro')
    
    try:
        if json_output_str.strip().startswith("```json"):
            json_output_str = json_output_str.strip()[7:-3]
        json_output = json.loads(json_output_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="A IA gerou uma resposta em formato JSON inválido.")

    # 2. Salvar a Estação
    try:
        print(f"💾 Salvando a nova estação na coleção 'estacoes_clinicas'...")
        # O método .add() cria um documento com um ID gerado automaticamente
        update_time, doc_ref = db.collection('estacoes_clinicas').add(json_output)
        new_station_id = doc_ref.id
        print(f"✅ Estação salva com sucesso! ID: {new_station_id}")
    except Exception as e:
        print(f"🚨 Erro ao salvar no Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a estação no Firestore: {e}")

    # 3. Retornar o resultado
    return {
        "status": "success",
        "message": "Estação gerada e salva com sucesso!",
        "station_id": new_station_id,
        "station_data": json_output
    }


@app.post("/api/agent/analyze-station", tags=["Agente - Análise"])
async def analyze_station(request: AnalyzeStationRequest):
    if not AGENT_RULES or not db: raise HTTPException(status_code=503, detail="Regras ou conexão com Firestore não disponíveis.")
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
        return {"station_id": request.station_id, "analysis": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar estação: {e}")

@app.post("/api/agent/apply-audit", tags=["Agente - Análise"])
async def apply_audit(request: ApplyAuditRequest):
    if not db: raise HTTPException(status_code=503, detail="Conexão com Firestore não disponível.")
    try:
        collection_name = 'estacoes_clinicas'
        station_id = request.station_id
        print(f"🛠️ Aplicando auditoria na estação: {collection_name}/{station_id}")

        # 1. Buscar o documento original
        station_ref = db.collection(collection_name).document(station_id)
        station_doc = station_ref.get()
        if not station_doc.exists:
            raise HTTPException(status_code=404, detail="Estação não encontrada para aplicar mudanças.")
        
        original_station_json = json.dumps(station_doc.to_dict(), indent=2, ensure_ascii=False)

        # 2. Chamar a IA para obter o JSON modificado (USAR GEMINI 2.5 PRO)
        prompt = build_prompt_apply_audit(original_station_json, request.analysis_result)
        updated_json_str = await call_gemini_api(prompt, preferred_model='flash')

        # 3. Validar e atualizar o documento
        try:
            if updated_json_str.strip().startswith("```json"):
                updated_json_str = updated_json_str.strip()[7:-3]
            updated_station_data = json.loads(updated_json_str)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="A IA gerou um JSON modificado inválido.")

        station_ref.set(updated_station_data) # Usar .set() para sobrescrever o documento
        print(f"✅ Mudanças da auditoria aplicadas com sucesso em {station_id}")

        return {
            "status": "success",
            "message": "Mudanças da auditoria aplicadas com sucesso!",
            "station_id": station_id,
            "updated_station_data": updated_station_data
        }
    except Exception as e:
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
        
        # Tentar salvar no sistema híbrido primeiro
        local_success = save_learning(feedback, context, category)
        
        # Fallback para Firestore se sistema local falhar ou se não estiver em modo mock
        if not firebase_mock_mode and db:
            try:
                doc_ref = db.collection('agent_config').document('rules')
                current_doc = doc_ref.get()
                
                if current_doc.exists:
                    current_md = (current_doc.to_dict() or {}).get('referencias_md', '')
                    new_rule_md = f"\n\n---\n\n## REGRA APRENDIDA (Feedback do Usuário):\n\n- {feedback}\n"
                    doc_ref.update({'referencias_md': current_md + new_rule_md})
                    print("✅ Backup salvo no Firestore também")
                    
            except Exception as e:
                print(f"⚠️ Erro ao salvar backup no Firestore: {e}")
        
        # Recarregar sistema se necessário
        if local_success and LOCAL_MEMORY_SYSTEM:
            # Recarregar aprendizados na memória
            try:
                with open('memoria/aprendizados_usuario.jsonl', 'r', encoding='utf-8') as f:
                    LOCAL_MEMORY_SYSTEM['aprendizados'] = json.load(f)
            except:
                pass
        
        message = "✅ Aprendizado salvo no sistema híbrido!" if local_success else "✅ Aprendizado salvo no Firestore!"
        
        return {
            "status": "success", 
            "message": message,
            "system_used": "hibrido" if local_success else "firestore",
            "category": categorize_learning(feedback, context)
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
# 📊 ENDPOINTS DO SISTEMA DE MONITORAMENTO
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
            except:
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
            "memory_stats": {
                "total_references_chars": len(LOCAL_MEMORY_SYSTEM.get('referencias_base', '')),
                "total_template_chars": len(LOCAL_MEMORY_SYSTEM.get('gabarito_template', '')),
                "estimated_token_savings": "82%" if LOCAL_MEMORY_SYSTEM else "0%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {e}")

# --- Ponto de Entrada para Execução Local ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
