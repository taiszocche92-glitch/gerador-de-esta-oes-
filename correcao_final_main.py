#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Correção Final para Integração no Main.py
Data: 27 de agosto de 2025
Autor: GitHub Copilot
"""

import json
import logging
import os
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analisar_main_py():
    """
    Analisa o arquivo main.py para identificar pontos de melhoria na validação
    """
    print("=" * 80)
    print("🔍 ANÁLISE DO MAIN.PY ATUAL")
    print("=" * 80)
    
    if not os.path.exists("main.py"):
        print("❌ Arquivo main.py não encontrado!")
        return False
    
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verificar se já tem validação de impressos
    tem_validacao = "validar_impressos_estacao" in content
    tem_correcao = "corrigir_impressos" in content
    tem_monitoring = "MONITORING_SYSTEM" in content
    
    print(f"✅ Validação de impressos: {'Implementado' if tem_validacao else 'Não implementado'}")
    print(f"✅ Correção automática: {'Implementado' if tem_correcao else 'Não implementado'}")
    print(f"✅ Sistema de monitoramento: {'Implementado' if tem_monitoring else 'Não implementado'}")
    
    # Procurar por problemas específicos identificados nos logs
    problemas_encontrados = []
    
    if "imagemComLaudo" in content:
        problemas_encontrados.append("Tipo 'imagemComLaudo' ainda presente (deve ser 'imagem_com_texto')")
    
    if "tabela" in content and "lista_chave_valor_secoes" not in content:
        problemas_encontrados.append("Tipo 'tabela' pode estar sendo usado incorretamente")
    
    # Verificar se endpoint generate-final-station tem validação completa
    if "generate-final-station" in content:
        print("✅ Endpoint generate-final-station encontrado")
        
        # Verificar se tem validação antes do salvamento
        linhas = content.split('\n')
        dentro_endpoint = False
        tem_validacao_pre_save = False
        
        for linha in linhas:
            if "@app.post(\"/api/agent/generate-final-station\"" in linha:
                dentro_endpoint = True
            elif dentro_endpoint and ("@app." in linha or "def " in linha.strip()):
                dentro_endpoint = False
            elif dentro_endpoint and "validar_impressos_estacao" in linha:
                tem_validacao_pre_save = True
        
        print(f"✅ Validação pré-salvamento: {'Implementado' if tem_validacao_pre_save else 'Não implementado'}")
    
    if problemas_encontrados:
        print(f"\n⚠️  Problemas identificados:")
        for problema in problemas_encontrados:
            print(f"   • {problema}")
    else:
        print(f"\n✅ Nenhum problema crítico identificado")
    
    return True

def verificar_configuracao_validacao():
    """
    Verifica se a configuração da validação está correta
    """
    print("\n" + "=" * 80)
    print("🔧 VERIFICANDO CONFIGURAÇÃO DA VALIDAÇÃO")
    print("=" * 80)
    
    # Verificar se módulo de validação pode ser importado
    try:
        from impressos_validator import validar_impressos_estacao, ImpressosValidator
        print("✅ Módulo impressos_validator importado com sucesso")
        
        # Testar uma validação simples - a função espera uma estação completa
        teste_estacao = {
            "materiaisDisponiveis": {
                "impressos": [
                    {
                        "idImpresso": "teste",
                        "tituloImpresso": "TESTE",
                        "tipoConteudo": "lista_chave_valor_secoes",
                        "conteudo": {
                            "secoes": [
                                {
                                    "tituloSecao": "Teste",
                                    "itens": [
                                        {"chave": "teste", "valor": "valor"}
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        valido, erros, estacao_corrigida = validar_impressos_estacao(teste_estacao)
        print(f"✅ Teste de validação: {'PASSOU' if valido else 'FALHOU'}")
        
        if not valido:
            print(f"   Erros encontrados: {len(erros)}")
            for erro in erros[:3]:  # Mostrar apenas os primeiros 3
                print(f"   • {erro}")
                
    except ImportError as e:
        print(f"❌ Erro ao importar validador: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste de validação: {e}")
        return False
    
    return True

def gerar_snippet_correcao():
    """
    Gera snippet de código para correção no main.py
    """
    print("\n" + "=" * 80)
    print("🔧 SNIPPET DE CORREÇÃO PARA MAIN.PY")
    print("=" * 80)
    
    snippet = '''
# === VALIDAÇÃO AVANÇADA DE IMPRESSOS (INSERIR NO ENDPOINT generate-final-station) ===

# Logo após a geração do JSON e antes do salvamento no Firestore, adicionar:

if IMPRESSOS_VALIDATOR_AVAILABLE:
    logger.info("🏥 Iniciando validação completa de impressos médicos...")
    
    try:
        # Validar toda a estação (não apenas impressos)
        is_valid, validation_errors, estacao_corrigida = validar_impressos_estacao(json_output)
        
        if not is_valid:
            logger.warning(f"⚠️ Validação de impressos: {len(validation_errors)} erros encontrados")
            
            # Log dos erros para análise
            for error in validation_errors[:5]:  # Mostrar apenas os primeiros 5
                logger.warning(f"   - {error}")
            
            # Aplicar correções automáticas usando estação corrigida retornada
            if estacao_corrigida and estacao_corrigida != json_output:
                logger.info("✅ Aplicando correções automáticas aos impressos...")
                json_output = estacao_corrigida
                
                # Registrar métricas
                if MONITORING_SYSTEM.get('active'):
                    MONITORING_SYSTEM['metrics']['impressos_auto_corrected'] = MONITORING_SYSTEM['metrics'].get('impressos_auto_corrected', 0) + 1
            else:
                logger.warning("⚠️ Correção automática não disponível")
                # Adicionar metadata sobre os erros
                json_output["_validation_issues"] = {
                    "impressos_errors": validation_errors,
                    "auto_correction_attempted": True,
                    "auto_correction_successful": False
                }
        else:
            logger.info("✅ Todos os impressos passaram na validação!")
            
            # Registrar sucesso na validação
            if MONITORING_SYSTEM.get('active'):
                MONITORING_SYSTEM['metrics']['impressos_validated_success'] = MONITORING_SYSTEM['metrics'].get('impressos_validated_success', 0) + 1
            
    except Exception as validation_error:
        logger.error(f"❌ Erro na validação de impressos: {validation_error}")
        # Continuar com o salvamento mesmo se a validação falhar
        if MONITORING_SYSTEM.get('active'):
            MONITORING_SYSTEM['metrics']['validation_system_errors'] = MONITORING_SYSTEM['metrics'].get('validation_system_errors', 0) + 1
        
        # Adicionar metadata sobre o erro
        json_output["_validation_issues"] = {
            "validation_system_error": str(validation_error),
            "timestamp": datetime.now().isoformat()
        }
else:
    logger.warning("⚠️ Sistema de validação de impressos não disponível - pulando validação")

# === FIM DO SNIPPET ===
'''
    
    print(snippet)
    
    # Salvar snippet em arquivo
    with open("snippet_correcao_main.py", "w", encoding="utf-8") as f:
        f.write(snippet)
    
    print("💾 Snippet salvo em 'snippet_correcao_main.py'")

def recomendar_melhorias():
    """
    Recomenda melhorias para o sistema baseado nos logs analisados
    """
    print("\n" + "=" * 80)
    print("💡 RECOMENDAÇÕES DE MELHORIAS")
    print("=" * 80)
    
    recomendacoes = [
        {
            "id": "R001",
            "titulo": "Validação Pré-Salvamento Obrigatória",
            "descricao": "Sempre validar impressos antes de salvar no Firestore",
            "prioridade": "ALTA",
            "implementacao": "Adicionar validação no endpoint generate-final-station"
        },
        {
            "id": "R002", 
            "titulo": "Correção Automática Integrada",
            "descricao": "Aplicar correções automáticas quando problemas forem detectados",
            "prioridade": "ALTA",
            "implementacao": "Integrar corrigir_impressos.py no fluxo principal"
        },
        {
            "id": "R003",
            "titulo": "Logging Detalhado de Validação",
            "descricao": "Adicionar logs específicos para monitorar validações",
            "prioridade": "MÉDIA",
            "implementacao": "Expandir logging no sistema de validação"
        },
        {
            "id": "R004",
            "titulo": "Métricas de Qualidade",
            "descricao": "Coletar métricas sobre taxa de sucesso da validação",
            "prioridade": "MÉDIA", 
            "implementacao": "Adicionar contadores no MONITORING_SYSTEM"
        },
        {
            "id": "R005",
            "titulo": "Fallback para Tipos Incorretos",
            "descricao": "Converter automaticamente tipos incorretos (tabela→lista_chave_valor_secoes)",
            "prioridade": "BAIXA",
            "implementacao": "Adicionar lógica de conversão automática"
        }
    ]
    
    for rec in recomendacoes:
        print(f"\n{rec['id']} - {rec['titulo']} [{rec['prioridade']}]")
        print(f"   📄 {rec['descricao']}")
        print(f"   🔧 {rec['implementacao']}")
    
    return recomendacoes

def gerar_script_teste_pos_integracao():
    """
    Gera script para testar o sistema após a integração
    """
    print("\n" + "=" * 80)
    print("🧪 SCRIPT DE TESTE PÓS-INTEGRAÇÃO")
    print("=" * 80)
    
    script_teste = '''#!/usr/bin/env python3
"""
Teste Pós-Integração do Sistema de Validação
Execute após aplicar as correções no main.py
"""

import requests
import json
import time

def testar_endpoint_geracao():
    """
    Testa o endpoint de geração de estações com validação integrada
    """
    print("🧪 Testando endpoint de geração com validação integrada...")
    
    # Dados de teste
    dados_teste = {
        "tema": "AVC ISQUEMICO",
        "especialidade": "Clínica Médica",
        "resumo_clinico": "Teste de validação integrada",
        "proposta_escolhida": "Encontro clínico completo com foco em neurologia"
    }
    
    try:
        # Fazer requisição para o endpoint
        response = requests.post(
            "http://localhost:8080/api/agent/generate-final-station",
            json=dados_teste,
            timeout=180  # 3 minutos
        )
        
        if response.status_code == 200:
            resultado = response.json()
            print("✅ Endpoint respondeu com sucesso")
            
            # Verificar se tem validação aplicada
            if "_validation_issues" in resultado.get("station_data", {}):
                print("⚠️ Problemas de validação detectados (esperado)")
            else:
                print("✅ Nenhum problema de validação detectado")
            
            # Verificar se impressos estão corretos
            impressos = resultado.get("station_data", {}).get("materiaisDisponiveis", {}).get("impressos", [])
            print(f"📋 Total de impressos gerados: {len(impressos)}")
            
            # Verificar tipos de conteúdo
            tipos_encontrados = set()
            for impresso in impressos:
                tipos_encontrados.add(impresso.get("tipoConteudo", ""))
            
            print(f"🔍 Tipos de conteúdo encontrados: {list(tipos_encontrados)}")
            
            # Verificar se há tipos incorretos
            tipos_incorretos = {"tabela", "imagemComLaudo"}
            tipos_problematicos = tipos_encontrados.intersection(tipos_incorretos)
            
            if tipos_problematicos:
                print(f"❌ Tipos incorretos encontrados: {tipos_problematicos}")
            else:
                print("✅ Todos os tipos de conteúdo estão corretos")
            
        else:
            print(f"❌ Endpoint falhou: {response.status_code}")
            print(f"   Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando teste pós-integração...")
    testar_endpoint_geracao()
    print("🏁 Teste concluído!")
'''
    
    with open("teste_pos_integracao.py", "w", encoding="utf-8") as f:
        f.write(script_teste)
    
    print("💾 Script de teste salvo em 'teste_pos_integracao.py'")

def main():
    """
    Função principal do script de correção
    """
    print("🚀 Iniciando análise e correção do sistema de validação...")
    print(f"📅 Data: 27 de agosto de 2025")
    print(f"📂 Diretório: {os.getcwd()}")
    
    # 1. Analisar main.py atual
    if not analisar_main_py():
        print("❌ Não foi possível analisar o main.py!")
        return 1
    
    # 2. Verificar configuração da validação
    if not verificar_configuracao_validacao():
        print("❌ Problemas na configuração da validação!")
        return 1
    
    # 3. Gerar snippet de correção
    gerar_snippet_correcao()
    
    # 4. Recomendar melhorias
    recomendacoes = recomendar_melhorias()
    
    # 5. Gerar script de teste pós-integração
    gerar_script_teste_pos_integracao()
    
    print("\n" + "=" * 80)
    print("🎯 PLANO DE AÇÃO FINAL")
    print("=" * 80)
    print("1. ✅ Revisar snippet_correcao_main.py")
    print("2. 🔧 Aplicar as correções no main.py")
    print("3. 🧪 Executar teste_pos_integracao.py")
    print("4. 📊 Monitorar logs durante testes")
    print("5. 🎉 Sistema estará pronto para produção!")
    
    print(f"\n💡 Implementar {len([r for r in recomendacoes if r['prioridade'] == 'ALTA'])} recomendações de ALTA prioridade primeiro")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
