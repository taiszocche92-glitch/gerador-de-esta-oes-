#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se a ordem das seções está sendo preservada
após as correções implementadas.
"""

import json
import sys
import os
from corretor_profundidade_impressos import reduzir_profundidade_impresso
from impressos_validator import validar_impressos_estacao

def testar_ordem_secoes():
    """Testa se a ordem das seções é preservada durante o processamento"""

    # Carregar dados da estação de teste
    arquivo_estacao = "estacoes_geradas/38ccb01c-2ab6-44f8-9a00-5925876cfb2e.json"

    if not os.path.exists(arquivo_estacao):
        print(f"❌ Arquivo de teste não encontrado: {arquivo_estacao}")
        return False

    try:
        with open(arquivo_estacao, 'r', encoding='utf-8') as f:
            dados_estacao = json.load(f)

        print("📋 Carregando estação de teste...")
        print(f"   Título: {dados_estacao.get('tituloEstacao', 'N/A')}")
        print(f"   Especialidade: {dados_estacao.get('especialidade', 'N/A')}")

        # Extrair impressos
        materiais = dados_estacao.get('materiaisDisponiveis', {})
        impressos = materiais.get('impressos', [])

        if not impressos:
            print("❌ Nenhum impresso encontrado na estação")
            return False

        print(f"   📄 Encontrados {len(impressos)} impressos")

        # Testar cada impresso
        for i, impresso in enumerate(impressos):
            print(f"\n🔍 Testando impresso {i+1}: {impresso.get('tituloImpresso', 'N/A')}")

            # Verificar se tem seções
            conteudo = impresso.get('conteudo', {})
            tipo_conteudo = impresso.get('tipoConteudo', '')

            # Pular tipos que não têm seções estruturadas
            if tipo_conteudo in ['texto_simples', 'texto_livre', 'imagem_com_texto']:
                print(f"   ⏭️  Tipo '{tipo_conteudo}' não tem seções estruturadas, pulando...")
                continue

            # Verificar se conteúdo é um dicionário
            if not isinstance(conteudo, dict):
                print(f"   ⏭️  Conteúdo não é estruturado (tipo: {type(conteudo)}), pulando...")
                continue

            secoes = conteudo.get('secoes', [])

            if not secoes:
                print("   ⏭️  Nenhum seção encontrada, pulando...")
                continue

            print(f"   📊 {len(secoes)} seções encontradas")

            # Registrar ordem original
            ordem_original = []
            for j, secao in enumerate(secoes):
                if isinstance(secao, dict):
                    titulo = secao.get('tituloSecao', f'Seção {j+1}')
                    ordem_original.append(titulo)
                    print(f"      {j+1}. {titulo}")
                else:
                    ordem_original.append(f'Item {j+1}')
                    print(f"      {j+1}. Item não estruturado")

            # Aplicar redução de profundidade
            print("   🔧 Aplicando redução de profundidade...")
            impresso_reduzido = reduzir_profundidade_impresso(impresso.copy())

            # Verificar ordem após redução
            conteudo_reduzido = impresso_reduzido.get('conteudo', {})
            secoes_reduzidas = conteudo_reduzido.get('secoes', [])

            ordem_apos_reducao = []
            for j, secao in enumerate(secoes_reduzidas):
                if isinstance(secao, dict):
                    titulo = secao.get('tituloSecao', f'Seção {j+1}')
                    ordem_apos_reducao.append(titulo)
                else:
                    ordem_apos_reducao.append(f'Item {j+1}')

            # Comparar ordens
            if ordem_original == ordem_apos_reducao:
                print("   ✅ Ordem preservada após redução de profundidade")
            else:
                print("   ❌ Ordem ALTERADA após redução de profundidade!")
                print(f"      Original: {ordem_original}")
                print(f"      Após redução: {ordem_apos_reducao}")
                return False

            # Aplicar validação
            print("   🔍 Aplicando validação...")
            estacao_teste = {
                'materiaisDisponiveis': {
                    'impressos': [impresso_reduzido]
                }
            }

            is_valid, errors, estacao_corrigida = validar_impressos_estacao(estacao_teste)
            impressos_corrigidos = estacao_corrigida.get('materiaisDisponiveis', {}).get('impressos', [])

            if impressos_corrigidos:
                impresso_validado = impressos_corrigidos[0]
                conteudo_validado = impresso_validado.get('conteudo', {})
                secoes_validadas = conteudo_validado.get('secoes', [])

                ordem_apos_validacao = []
                for j, secao in enumerate(secoes_validadas):
                    if isinstance(secao, dict):
                        titulo = secao.get('tituloSecao', f'Seção {j+1}')
                        ordem_apos_validacao.append(titulo)
                    else:
                        ordem_apos_validacao.append(f'Item {j+1}')

                # Comparar ordens após validação
                if ordem_original == ordem_apos_validacao:
                    print("   ✅ Ordem preservada após validação")
                else:
                    print("   ❌ Ordem ALTERADA após validação!")
                    print(f"      Original: {ordem_original}")
                    print(f"      Após validação: {ordem_apos_validacao}")
                    return False

                if errors:
                    print(f"   ⚠️  {len(errors)} erros de validação encontrados:")
                    for error in errors:
                        print(f"      - {error}")

        print("\n🎉 Todos os testes passaram! A ordem das seções está sendo preservada.")
        return True

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste de preservação de ordem das seções...")
    sucesso = testar_ordem_secoes()

    if sucesso:
        print("\n✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)
