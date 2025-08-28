#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico Específico de Profundidade de Impressos
Analisa problemas estruturais detectados nos logs do main.py
"""

import json
from typing import Dict, Any, List
import logging

def calcular_profundidade(obj, nivel=0, max_depth=10):
    """Calcula profundidade de estrutura aninhada"""
    if nivel > max_depth:
        return max_depth
    
    if isinstance(obj, dict):
        if not obj:
            return nivel
        return max(calcular_profundidade(v, nivel + 1, max_depth) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return nivel
        return max(calcular_profundidade(item, nivel + 1, max_depth) for item in obj)
    else:
        return nivel

def diagnosticar_estrutura_impressos():
    """Simula o problema detectado nos logs"""
    print("🔍 DIAGNÓSTICO DE PROFUNDIDADE DE IMPRESSOS")
    print("=" * 60)
    
    # Estrutura problemática similar ao log
    impresso_problematico = {
        "idImpresso": "est01_examefisico",
        "tituloImpresso": "SINAIS VITAIS E EXAME FÍSICO",
        "tipoConteudo": "lista_chave_valor_secoes",
        "conteudo": {
            "secoes": [
                {
                    "tituloSecao": "SINAIS VITAIS",
                    "itens": [
                        {"chave": "Pressão arterial", "valor": "95 x 60 mmHg"},
                        {"chave": "Frequência cardíaca", "valor": "115 bpm"},
                        {"chave": "Frequência respiratória", "valor": "24 irpm"}
                    ]
                },
                {
                    "tituloSecao": "EXAME FÍSICO GERAL",
                    "itens": [
                        {"chave": "Estado geral", "valor": "Regular estado geral, pálido (+/4+)"}
                    ]
                }
            ]
        }
    }
    
    # Calcular profundidade
    prof_total = calcular_profundidade(impresso_problematico)
    prof_conteudo = calcular_profundidade(impresso_problematico["conteudo"])
    prof_secoes = calcular_profundidade(impresso_problematico["conteudo"]["secoes"])
    
    print(f"📊 ANÁLISE DE PROFUNDIDADE:")
    print(f"   • Profundidade total do impresso: {prof_total}")
    print(f"   • Profundidade do conteúdo: {prof_conteudo}")
    print(f"   • Profundidade das seções: {prof_secoes}")
    print()
    
    print(f"🚨 PROBLEMA DETECTADO:")
    print(f"   • Limite permitido: 2 níveis")
    print(f"   • Profundidade atual: {prof_conteudo} níveis")
    print(f"   • Violação: {prof_conteudo - 2} níveis a mais")
    print()
    
    # Estrutura depois da sanitização (strings JSON)
    print("📋 ESTRUTURA APÓS SANITIZAÇÃO PROBLEMÁTICA:")
    impresso_sanitizado_errado = {
        "idImpresso": "est01_examefisico",
        "tituloImpresso": "SINAIS VITAIS E EXAME FÍSICO", 
        "tipoConteudo": "lista_chave_valor_secoes",
        "conteudo": {
            "secoes": [
                '{"tituloSecao": "SINAIS VITAIS", "itens": [{"chave": "Pressão arterial", "valor": "95 x 60 mmHg"}]}',
                '{"tituloSecao": "EXAME FÍSICO GERAL", "itens": [{"chave": "Estado geral", "valor": "Regular estado geral"}]}'
            ]
        }
    }
    
    prof_sanitizado = calcular_profundidade(impresso_sanitizado_errado["conteudo"])
    print(f"   • Profundidade após sanitização: {prof_sanitizado}")
    print(f"   • Estrutura: conteudo > secoes > [strings JSON]")
    print()
    
    print("❌ PROBLEMA COM STRINGS JSON:")
    print("   • Seções se tornaram strings ao invés de objetos")
    print("   • Validator tenta fazer .copy() em string")
    print("   • Erro: 'str' object has no attribute 'copy'")
    print()
    
    return impresso_problematico, impresso_sanitizado_errado

def criar_estrutura_correta():
    """Cria estrutura correta com profundidade <= 2"""
    print("✅ ESTRUTURA CORRIGIDA:")
    print("=" * 60)
    
    # Versão corrigida - profundidade máxima 2
    impresso_corrigido = {
        "idImpresso": "est01_examefisico",
        "tituloImpresso": "SINAIS VITAIS E EXAME FÍSICO",
        "tipoConteudo": "lista_chave_valor_secoes",
        "conteudo": {
            "sinais_vitais": "PA: 95x60 mmHg | FC: 115 bpm | FR: 24 irpm | T: 37,9°C | SatO2: 93%",
            "exame_geral": "Regular estado geral, pálido (+/4+), sudorético, dispneico",
            "cardiovascular": "Turgência jugular patológica. B3 em foco mitral",
            "respiratorio": "Estertores crepitantes em bases pulmonares",
            "extremidades": "Edema mole, simétrico (++/4+) até tornozelos"
        }
    }
    
    prof_corrigido = calcular_profundidade(impresso_corrigido["conteudo"])
    print(f"📊 PROFUNDIDADE CORRIGIDA: {prof_corrigido} níveis")
    print(f"✅ Dentro do limite: {prof_corrigido} <= 2")
    print()
    
    print("🔧 ALTERAÇÕES APLICADAS:")
    print("   • Removida estrutura secoes > itens > chave/valor")
    print("   • Convertido para chaves diretas com strings descritivas")
    print("   • Mantido conteúdo médico completo")
    print("   • Profundidade reduzida de 5 para 2 níveis")
    
    return impresso_corrigido

def simular_erro_validacao():
    """Simula o erro de validação encontrado nos logs"""
    print("\n🚨 SIMULAÇÃO DO ERRO DE VALIDAÇÃO:")
    print("=" * 60)
    
    # String JSON que causa o erro
    secao_string = '{"tituloSecao": "SINAIS VITAIS", "itens": [{"chave": "PA", "valor": "95x60"}]}'
    
    print(f"❌ Tentativa de .copy() em string:")
    print(f"   Tipo: {type(secao_string)}")
    print(f"   Valor: {secao_string[:50]}...")
    print()
    
    try:
        # Corrigir: converter string JSON para dict antes de copiar
        secao_dict = json.loads(secao_string)
        copia = secao_dict.copy()
        print(f"✅ Sucesso: Copiado como dict - {copia}")
    except AttributeError as e:
        print(f"🔴 ERRO CAPTURADO: {e}")
        print("   • Strings não têm método .copy()")
        print("   • Validator espera objetos dict")
        print("   • Sanitização converteu objetos em strings")
    
    print()
    print("✅ SOLUÇÃO:")
    print("   • Detectar strings JSON no conteúdo")
    print("   • Converter de volta para objetos dict")
    print("   • Ou reestruturar com profundidade <= 2")

if __name__ == "__main__":
    print("🏥 DIAGNÓSTICO DE PROBLEMAS ESTRUTURAIS NOS IMPRESSOS")
    print("Baseado nos logs do main.py")
    print("=" * 70)
    print()
    
    # Diagnóstico do problema
    problematico, sanitizado_errado = diagnosticar_estrutura_impressos()
    
    # Estrutura corrigida
    corrigido = criar_estrutura_correta()
    
    # Simulação do erro
    simular_erro_validacao()
    
    print("\n" + "=" * 70)
    print("📋 RESUMO DO DIAGNÓSTICO:")
    print("1. ❌ Impressos gerados com profundidade > 2 níveis")
    print("2. ❌ Sanitização converte objetos em strings JSON")  
    print("3. ❌ Validator falha ao tentar .copy() em strings")
    print("4. ✅ Solução: Reestruturar com profundidade <= 2")
    print("5. ✅ Alternativa: Corrigir sanitização/validação")
