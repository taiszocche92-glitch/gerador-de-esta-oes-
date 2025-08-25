#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema Híbrido de Memória - Fase 2A
Testa as funcionalidades de aprendizado automático implementadas
"""

import json
import sys
import os

# Adicionar o diretório do backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar as funções do main
from main import (
    categorize_learning, 
    save_learning, 
    get_recent_learnings, 
    format_learnings_for_context,
    initialize_local_memory_system
)

def test_sistema_hibrido():
    """Testa o sistema híbrido de memória"""
    print("🧪 TESTANDO SISTEMA HÍBRIDO DE MEMÓRIA - FASE 2A")
    print("="*60)
    
    # 1. Testar inicialização
    print("\n1️⃣ Testando inicialização do sistema local...")
    success = initialize_local_memory_system()
    print(f"✅ Sistema inicializado: {success}")
    
    # 2. Testar categorização automática
    print("\n2️⃣ Testando categorização automática de aprendizados...")
    
    test_rules = [
        ("Nunca usar parênteses nas descrições do PEP", "restricao"),
        ("Sempre incluir notificação SINAM em casos de dengue", "obrigatorio"),
        ("Preferir usar 'contextoOuPerguntaChave' ao invés de HDA", "preferencia"),
        ("Criar novo padrão para estações de emergência", "novo_padrao"),
        ("Corrigir erro na formatação dos impressos", "correcao"),
        ("Usar formato JSON para estrutura de exames", "formatacao"),
        ("Esta é uma regra geral sem categoria específica", "geral")
    ]
    
    for rule, expected_category in test_rules:
        category = categorize_learning(rule)
        status = "✅" if category == expected_category else "❌"
        print(f"  {status} '{rule[:50]}...' → {category}")
    
    # 3. Testar salvamento de aprendizados
    print("\n3️⃣ Testando salvamento de aprendizados...")
    
    test_learnings = [
        {
            "rule": "Sempre usar sistema híbrido para economia de tokens",
            "context": "Otimização de performance",
            "category": "obrigatorio"
        },
        {
            "rule": "Nunca incluir informações entre parênteses no PEP",
            "context": "Padrão de formatação INEP",
            "category": "restricao"
        },
        {
            "rule": "Preferir arquivos locais ao invés de Firestore para templates",
            "context": "Sistema híbrido",
            "category": "preferencia"
        }
    ]
    
    for learning in test_learnings:
        success = save_learning(
            learning["rule"], 
            learning["context"], 
            learning["category"]
        )
        status = "✅" if success else "❌"
        print(f"  {status} Salvamento: {learning['rule'][:50]}...")
    
    # 4. Testar recuperação de aprendizados
    print("\n4️⃣ Testando recuperação de aprendizados...")
    recent_learnings = get_recent_learnings(5)
    print(f"✅ Encontrados {len(recent_learnings)} aprendizados recentes")
    
    # 5. Testar formatação para contexto
    print("\n5️⃣ Testando formatação para contexto...")
    if recent_learnings:
        formatted = format_learnings_for_context(recent_learnings)
        print(f"✅ Contexto formatado: {len(formatted)} caracteres")
        print("\n📄 EXEMPLO DE CONTEXTO FORMATADO:")
        print("-" * 40)
        print(formatted[:300] + "..." if len(formatted) > 300 else formatted)
        print("-" * 40)
    
    # 6. Testar estatísticas
    print("\n6️⃣ Estatísticas do sistema:")
    print(f"📊 Total de aprendizados: {len(recent_learnings)}")
    
    if recent_learnings:
        categories = {}
        for learning in recent_learnings:
            cat = learning.get('category', 'indefinida')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("📈 Por categoria:")
        for cat, count in categories.items():
            print(f"   • {cat}: {count}")
    
    print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    print("="*60)

if __name__ == "__main__":
    test_sistema_hibrido()
