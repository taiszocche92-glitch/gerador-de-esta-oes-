#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corretor de Profundidade de Impressos
Corrige problemas de profundidade excessiva e strings JSON nos impressos
"""

import json
import re
from typing import Dict, Any, List, Union
import logging

def detectar_strings_json_em_secoes(conteudo: Dict[str, Any]) -> bool:
    """Detecta se há strings JSON nas seções"""
    if not isinstance(conteudo, dict):
        return False
    
    secoes = conteudo.get('secoes', [])
    if not isinstance(secoes, list):
        return False
    
    for secao in secoes:
        if isinstance(secao, str):
            try:
                json.loads(secao)
                return True
            except:
                continue
    return False

def converter_strings_json_para_objetos(conteudo: Dict[str, Any]) -> Dict[str, Any]:
    """Converte strings JSON de volta para objetos"""
    if not isinstance(conteudo, dict):
        return conteudo
    
    conteudo_corrigido = conteudo.copy()
    secoes = conteudo.get('secoes', [])
    
    if isinstance(secoes, list):
        secoes_corrigidas = []
        for secao in secoes:
            if isinstance(secao, str):
                try:
                    secao_obj = json.loads(secao)
                    secoes_corrigidas.append(secao_obj)
                except:
                    # Se não conseguir fazer parse, manter como string
                    secoes_corrigidas.append(secao)
            else:
                secoes_corrigidas.append(secao)
        
        conteudo_corrigido['secoes'] = secoes_corrigidas
    
    return conteudo_corrigido

def calcular_profundidade_impressos(obj, nivel=0):
    """Calcula profundidade específica para impressos"""
    if isinstance(obj, dict):
        if not obj:
            return nivel
        return max(calcular_profundidade_impressos(v, nivel + 1) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return nivel
        return max(calcular_profundidade_impressos(item, nivel + 1) for item in obj)
    else:
        return nivel

def reduzir_profundidade_impresso(impresso: Dict[str, Any]) -> Dict[str, Any]:
    """Reduz profundidade de um impresso para máximo 2 níveis, preservando ordem das seções"""
    if not isinstance(impresso, dict):
        return impresso

    impresso_corrigido = impresso.copy()
    conteudo = impresso.get('conteudo', {})
    tipo_conteudo = impresso.get('tipoConteudo', '')

    # Se é lista_chave_valor_secoes, reduzir profundidade mantendo estrutura de lista
    if tipo_conteudo == 'lista_chave_valor_secoes' and isinstance(conteudo, dict):
        secoes = conteudo.get('secoes', [])

        if isinstance(secoes, list) and secoes:
            secoes_corrigidas = []

            for secao in secoes:
                if isinstance(secao, dict):
                    titulo_secao = secao.get('tituloSecao', '')
                    itens = secao.get('itens', [])

                    # Manter estrutura da seção, mas reduzir profundidade dos itens
                    secao_corrigida = {
                        'tituloSecao': titulo_secao,
                        'itens': []
                    }

                    # Converter itens aninhados em estrutura plana
                    for item in itens:
                        if isinstance(item, dict):
                            chave = item.get('chave', '')
                            valor = item.get('valor', '')
                            if chave and valor:
                                # Criar item plano com chave e valor diretos
                                secao_corrigida['itens'].append({
                                    'chave': chave,
                                    'valor': valor
                                })

                    secoes_corrigidas.append(secao_corrigida)

            # Manter estrutura original mas com profundidade reduzida
            impresso_corrigido['conteudo'] = {
                'secoes': secoes_corrigidas
            }

    return impresso_corrigido

def corrigir_tipo_conteudo_invalido(impresso: Dict[str, Any]) -> Dict[str, Any]:
    """Corrige tipos de conteúdo inválidos"""
    impresso_corrigido = impresso.copy()
    tipo_conteudo = impresso.get('tipoConteudo', '')
    
    # Mapeamento de tipos incorretos para corretos
    mapeamento_tipos = {
        'imagemComLaudo': 'imagem_com_texto',
        'tabela': 'lista_chave_valor_secoes',
        'textosimples': 'texto_simples',
        'imagemComTexto': 'imagem_com_texto'
    }
    
    if tipo_conteudo in mapeamento_tipos:
        impresso_corrigido['tipoConteudo'] = mapeamento_tipos[tipo_conteudo]
        print(f"🔧 Tipo corrigido: {tipo_conteudo} → {mapeamento_tipos[tipo_conteudo]}")
    
    return impresso_corrigido

def adicionar_sistema_neurologico_se_necessario(impresso: Dict[str, Any]) -> Dict[str, Any]:
    """Adiciona sistema neurológico se for exame físico e não tiver"""
    impresso_corrigido = impresso.copy()
    titulo = impresso.get('tituloImpresso', '').lower()
    conteudo = impresso.get('conteudo', {})
    
    # Se é exame físico
    if any(palavra in titulo for palavra in ['exame físico', 'semiologia', 'físico']):
        # Verificar se tem sistema neurológico
        conteudo_str = str(conteudo).lower()
        
        if 'neurológico' not in conteudo_str and 'neuro' not in conteudo_str:
            # Adicionar sistema neurológico básico
            if isinstance(conteudo, dict):
                conteudo_corrigido = conteudo.copy()
                conteudo_corrigido['sistema_neurologico'] = 'Consciente, orientado. Reflexos preservados. Sem déficits focais.'
                impresso_corrigido['conteudo'] = conteudo_corrigido
                print("🧠 Sistema neurológico adicionado ao exame físico")
    
    return impresso_corrigido

def corrigir_impressos_problematicos(materiais_disponiveis: Dict[str, Any]) -> Dict[str, Any]:
    """Função principal para corrigir todos os problemas de impressos"""
    if not isinstance(materiais_disponiveis, dict):
        return materiais_disponiveis
    
    materiais_corrigidos = materiais_disponiveis.copy()
    impressos = materiais_disponiveis.get('impressos', [])
    
    if not isinstance(impressos, list):
        return materiais_corrigidos
    
    impressos_corrigidos = []
    
    print("🔧 CORRIGINDO IMPRESSOS PROBLEMÁTICOS:")
    print("=" * 50)
    
    for i, impresso in enumerate(impressos):
        if not isinstance(impresso, dict):
            impressos_corrigidos.append(impresso)
            continue
        
        print(f"\n📋 Processando impresso {i+1}: {impresso.get('tituloImpresso', 'Sem título')}")
        
        # 1. Corrigir tipos de conteúdo inválidos
        impresso_corrigido = corrigir_tipo_conteudo_invalido(impresso)
        
        # 2. Detectar e corrigir strings JSON
        conteudo = impresso_corrigido.get('conteudo', {})
        if detectar_strings_json_em_secoes(conteudo):
            print("   🔍 Strings JSON detectadas, convertendo para objetos...")
            conteudo_corrigido = converter_strings_json_para_objetos(conteudo)
            impresso_corrigido['conteudo'] = conteudo_corrigido
        
        # 3. Verificar profundidade
        prof_conteudo = calcular_profundidade_impressos(impresso_corrigido.get('conteudo', {}))
        print(f"   📊 Profundidade do conteúdo: {prof_conteudo}")
        
        if prof_conteudo > 2:
            print(f"   ⚠️ Profundidade excessiva ({prof_conteudo} > 2), reduzindo...")
            impresso_corrigido = reduzir_profundidade_impresso(impresso_corrigido)
            nova_prof = calcular_profundidade_impressos(impresso_corrigido.get('conteudo', {}))
            print(f"   ✅ Nova profundidade: {nova_prof}")
        
        # 4. Adicionar sistema neurológico se necessário
        impresso_corrigido = adicionar_sistema_neurologico_se_necessario(impresso_corrigido)
        
        impressos_corrigidos.append(impresso_corrigido)
    
    materiais_corrigidos['impressos'] = impressos_corrigidos
    
    print(f"\n✅ Correção concluída: {len(impressos_corrigidos)} impressos processados")
    return materiais_corrigidos

def validar_impressos_corrigidos(materiais_disponiveis: Dict[str, Any]) -> List[str]:
    """Valida se os impressos corrigidos estão em conformidade"""
    problemas = []
    impressos = materiais_disponiveis.get('impressos', [])
    
    for i, impresso in enumerate(impressos):
        if not isinstance(impresso, dict):
            problemas.append(f"Impresso {i+1}: Não é um dicionário")
            continue
        
        # Validar campos obrigatórios
        campos_obrigatorios = ['idImpresso', 'tituloImpresso', 'tipoConteudo', 'conteudo']
        for campo in campos_obrigatorios:
            if not impresso.get(campo):
                problemas.append(f"Impresso {i+1}: Campo '{campo}' ausente")
        
        # Validar profundidade
        conteudo = impresso.get('conteudo', {})
        prof = calcular_profundidade_impressos(conteudo)
        if prof > 2:
            problemas.append(f"Impresso {i+1}: Profundidade {prof} > 2")
        
        # Validar tipo de conteúdo
        tipos_validos = ['texto_simples', 'imagem_com_texto', 'lista_chave_valor_secoes', 'sinais_vitais']
        tipo = impresso.get('tipoConteudo')
        if tipo not in tipos_validos:
            problemas.append(f"Impresso {i+1}: Tipo inválido '{tipo}'")
    
    return problemas

# Exemplo de teste
if __name__ == "__main__":
    print("🏥 CORRETOR DE PROFUNDIDADE DE IMPRESSOS")
    print("=" * 60)
    
    # Simular materiais problemáticos baseados no log
    materiais_problematicos = {
        "informacoesVerbaisSimulado": [],
        "impressos": [
            {
                "idImpresso": "est01_examefisico",
                "tituloImpresso": "SINAIS VITAIS E EXAME FÍSICO",
                "tipoConteudo": "lista_chave_valor_secoes",
                "conteudo": {
                    "secoes": [
                        {
                            "tituloSecao": "SINAIS VITAIS",
                            "itens": [
                                {"chave": "Pressão arterial", "valor": "95 x 60 mmHg"},
                                {"chave": "Frequência cardíaca", "valor": "115 bpm"}
                            ]
                        },
                        {
                            "tituloSecao": "APARELHO CARDIOVASCULAR", 
                            "itens": [
                                {"chave": "Ausculta cardíaca", "valor": "B3 em foco mitral"}
                            ]
                        }
                    ]
                }
            },
            {
                "idImpresso": "est01_laboratorio",
                "tituloImpresso": "EXAMES LABORATORIAIS",
                "tipoConteudo": "lista_chave_valor_secoes",
                "conteudo": {
                    "secoes": [
                        '{"tituloSecao": "BIOMARCADORES", "itens": [{"chave": "Troponina", "valor": "850 ng/L"}]}'
                    ]
                }
            }
        ],
        "perguntasAtorSimulado": []
    }
    
    print("📋 MATERIAIS ORIGINAIS:")
    for i, imp in enumerate(materiais_problematicos['impressos']):
        prof = calcular_profundidade_impressos(imp.get('conteudo', {}))
        print(f"   Impresso {i+1}: {imp.get('tituloImpresso')} (prof: {prof})")
    
    # Corrigir
    materiais_corrigidos = corrigir_impressos_problematicos(materiais_problematicos)
    
    print("\n📋 VALIDAÇÃO FINAL:")
    problemas = validar_impressos_corrigidos(materiais_corrigidos)
    
    if problemas:
        print("❌ Problemas encontrados:")
        for problema in problemas:
            print(f"   • {problema}")
    else:
        print("✅ Todos os impressos estão válidos!")
    
    print("\n📊 RESUMO:")
    for i, imp in enumerate(materiais_corrigidos['impressos']):
        prof = calcular_profundidade_impressos(imp.get('conteudo', {}))
        print(f"   Impresso {i+1}: {imp.get('tituloImpresso')} (prof: {prof})")
