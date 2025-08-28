#!/usr/bin/env python3
"""
Diagnóstico dos Problemas de Validação de Impressos
Data: 27 de agosto de 2025
Autor: GitHub Copilot
"""

import json
import logging
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnostico_validacao_impressos():
    """
    Diagnóstico completo dos problemas de validação de impressos
    baseado nos logs do sistema
    """
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DOS PROBLEMAS DE VALIDAÇÃO DE IMPRESSOS")
    print("=" * 80)
    
    # Problemas identificados nos logs
    problemas = [
        {
            "id": "P001",
            "titulo": "Profundidade Excessiva em Impressos",
            "descricao": "Estruturas JSON com mais de 2 níveis de aninhamento",
            "evidencia": "impressos[0].conteudo VIOLATION: profundidade 5 > 2",
            "impacto": "ALTO",
            "solucao": "Correção automática com conversão de estruturas"
        },
        {
            "id": "P002", 
            "titulo": "Tipo de Conteúdo Incorreto",
            "descricao": "tipoConteudo 'tabela' ao invés de 'lista_chave_valor_secoes'",
            "evidencia": "impressos[2] com tipoConteudo: 'tabela'",
            "impacto": "MÉDIO",
            "solucao": "Detecção automática e correção de tipos"
        },
        {
            "id": "P003",
            "titulo": "String JSON em Arrays",
            "descricao": "JSON serializado como string dentro de arrays",
            "evidencia": "conteudo com strings JSON ao invés de objetos",
            "impacto": "ALTO", 
            "solucao": "Parser automático de strings JSON"
        },
        {
            "id": "P004",
            "titulo": "Perguntas Ator Simulado Complexas",
            "descricao": "perguntasAtorSimulado com objetos ao invés de strings simples",
            "evidencia": "perguntasAtorSimulado VIOLATION: profundidade 2 > 1",
            "impacto": "MÉDIO",
            "solucao": "Simplificação automática para lista de strings"
        },
        {
            "id": "P005",
            "titulo": "Tipo imagemComLaudo Incorreto",
            "descricao": "Tipo imagemComLaudo deve ser imagem_com_texto",
            "evidencia": "tipoConteudo: 'imagemComLaudo' em impressos TC e ECG",
            "impacto": "MÉDIO",
            "solucao": "Correção automática de tipos"
        }
    ]
    
    # Imprimir diagnóstico
    for i, problema in enumerate(problemas, 1):
        print(f"\n{i}. {problema['titulo']} ({problema['id']})")
        print(f"   📄 Descrição: {problema['descricao']}")
        print(f"   🔍 Evidência: {problema['evidencia']}")
        print(f"   ⚠️  Impacto: {problema['impacto']}")
        print(f"   🔧 Solução: {problema['solucao']}")
    
    print("\n" + "=" * 80)
    print("📊 RESUMO DO DIAGNÓSTICO")
    print("=" * 80)
    print(f"• Total de problemas identificados: {len(problemas)}")
    print(f"• Problemas de impacto ALTO: {len([p for p in problemas if p['impacto'] == 'ALTO'])}")
    print(f"• Problemas de impacto MÉDIO: {len([p for p in problemas if p['impacto'] == 'MÉDIO'])}")
    
    return problemas

def verificar_sistema_validacao():
    """
    Verifica se o sistema de validação está funcionando
    """
    print("\n" + "=" * 80)
    print("🔧 VERIFICANDO SISTEMA DE VALIDAÇÃO")
    print("=" * 80)
    
    arquivos_necessarios = {
        "impressos_validator.py": "Sistema de validação de impressos",
        "corrigir_impressos.py": "Script de correção automática", 
        "testar_impressos_corrigidos.py": "Script de teste de validação",
        "gabaritoestacoes.json": "Template de gabarito INEP",
        "impressos_corrigidos.json": "Arquivo de impressos corrigidos (será criado)"
    }
    
    status_arquivos = {}
    
    for arquivo, descricao in arquivos_necessarios.items():
        existe = os.path.exists(arquivo)
        status_arquivos[arquivo] = existe
        status = "✅" if existe else "❌"
        print(f"{status} {arquivo} - {descricao}")
        
        if arquivo == "impressos_corrigidos.json" and not existe:
            print(f"   ℹ️  Arquivo será criado durante a correção")
    
    # Verificar importação do validador
    try:
        from impressos_validator import validar_impressos_estacao
        print("✅ Módulo impressos_validator importado com sucesso")
        status_arquivos["validador_import"] = True
    except ImportError as e:
        print(f"❌ Erro ao importar validador: {e}")
        status_arquivos["validador_import"] = False
        
    return status_arquivos

def verificar_estrutura_projeto():
    """
    Verifica a estrutura do projeto
    """
    print("\n" + "=" * 80)
    print("📁 VERIFICANDO ESTRUTURA DO PROJETO")
    print("=" * 80)
    
    diretorios_importantes = [
        "memoria",
        "__pycache__",
        "api_docs",
        "estacoes_geradas"
    ]
    
    for diretorio in diretorios_importantes:
        existe = os.path.exists(diretorio)
        status = "✅" if existe else "❌"
        print(f"{status} {diretorio}/")
        
        if diretorio == "memoria" and existe:
            # Verificar arquivos da memória
            arquivos_memoria = [
                "aprendizados_usuario.jsonl",
                "config_memoria.json", 
                "referencias_base.md",
                "serviceAccountKey.json"
            ]
            
            for arquivo in arquivos_memoria:
                caminho = os.path.join("memoria", arquivo)
                existe_arquivo = os.path.exists(caminho)
                status_arquivo = "  ✅" if existe_arquivo else "  ❌"
                print(f"{status_arquivo} {caminho}")

def plano_correcao():
    """
    Plano de correção dos problemas identificados
    """
    print("\n" + "=" * 80)
    print("🔧 PLANO DE CORREÇÃO")
    print("=" * 80)
    
    etapas = [
        {
            "etapa": 1,
            "titulo": "Verificar Sistema de Validação",
            "descricao": "Confirmar se impressos_validator.py está funcionando",
            "comando": "python -c \"from impressos_validator import validar_impressos_estacao; print('✅ Validador funcionando')\"",
            "tempo_estimado": "2 min"
        },
        {
            "etapa": 2,
            "titulo": "Executar Script de Correção",
            "descricao": "Rodar corrigir_impressos.py para corrigir estruturas",
            "comando": "python corrigir_impressos.py",
            "tempo_estimado": "5 min"
        },
        {
            "etapa": 3,
            "titulo": "Testar Validação Corrigida",
            "descricao": "Validar impressos corrigidos",
            "comando": "python testar_impressos_corrigidos.py",
            "tempo_estimado": "3 min"
        },
        {
            "etapa": 4,
            "titulo": "Atualizar Validação no Main.py",
            "descricao": "Integrar validação antes do salvamento no Firestore",
            "comando": "Modificação no endpoint generate-final-station",
            "tempo_estimado": "10 min"
        },
        {
            "etapa": 5,
            "titulo": "Teste de Integração",
            "descricao": "Testar geração completa de estação via AdminView.vue",
            "comando": "Teste manual via interface",
            "tempo_estimado": "5 min"
        }
    ]
    
    for etapa in etapas:
        print(f"\n{etapa['etapa']}. {etapa['titulo']}")
        print(f"   📄 {etapa['descricao']}")
        print(f"   💻 Comando: {etapa['comando']}")
        print(f"   ⏱️  Tempo estimado: {etapa['tempo_estimado']}")
    
    print(f"\n⏱️ Tempo total estimado: 25 minutos")
    
    return etapas

def main():
    """
    Função principal do diagnóstico
    """
    print("🚀 Iniciando diagnóstico do sistema de validação de impressos...")
    print(f"📅 Data: 27 de agosto de 2025")
    print(f"📂 Diretório: {os.getcwd()}")
    
    # Executar diagnóstico
    problemas = diagnostico_validacao_impressos()
    
    # Verificar sistema de validação
    status_arquivos = verificar_sistema_validacao()
    
    # Verificar estrutura do projeto
    verificar_estrutura_projeto()
    
    # Mostrar plano de correção
    etapas = plano_correcao()
    
    print("\n" + "=" * 80)
    print("🚀 PRÓXIMOS PASSOS RECOMENDADOS")
    print("=" * 80)
    print("1. ✅ Execute este diagnóstico: python diagnostico_validacao.py")
    print("2. 🔧 Siga o plano de correção em ordem")
    print("3. 📊 Monitore logs durante a execução")
    print("4. 🧪 Teste a geração de estações após correções")
    print("=" * 80)
    
    # Verificar se pode prosseguir
    if not status_arquivos.get("validador_import", False):
        print("\n⚠️  ATENÇÃO: Sistema de validação com problemas!")
        print("   Primeiro corrija os problemas de importação antes de prosseguir.")
        return False
    
    if not status_arquivos.get("impressos_validator.py", False):
        print("\n⚠️  ATENÇÃO: Arquivo impressos_validator.py não encontrado!")
        print("   Este arquivo é essencial para o sistema funcionar.")
        return False
        
    print("\n✅ Sistema pronto para correção!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Diagnóstico concluído com sucesso!")
    else:
        print("\n❌ Diagnóstico identificou problemas críticos!")
