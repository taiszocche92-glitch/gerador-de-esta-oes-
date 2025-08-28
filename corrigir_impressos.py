#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir impressos JSON com problemas estruturais
"""

import json
import re
from typing import Dict, Any, List

def corrigir_impressos_json(impressos_json: str) -> str:
    """
    Corrige impressos JSON com problemas estruturais comuns
    """
    try:
        # Parse do JSON
        impressos = json.loads(impressos_json)
        impressos_corrigidos = []

        for impresso in impressos:
            impresso_corrigido = corrigir_impresso_individual(impresso)
            impressos_corrigidos.append(impresso_corrigido)

        return json.dumps(impressos_corrigidos, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Erro ao corrigir impressos: {e}")
        return impressos_json

def corrigir_impresso_individual(impresso: Dict[str, Any]) -> Dict[str, Any]:
    """Corrige um impresso individual"""
    impresso_corrigido = impresso.copy()

    # Primeiro verificar se é tabela e converter
    tipo_atual = impresso.get('tipoConteudo', '')
    if tipo_atual == 'tabela':
        impresso_corrigido['tipoConteudo'] = 'lista_chave_valor_secoes'
        impresso_corrigido['conteudo'] = converter_tabela_para_secoes(impresso.get('conteudo', {}))
        return impresso_corrigido

    # Classificar automaticamente o tipo correto baseado no título e conteúdo
    tipo_detectado = detectar_tipo_impresso(impresso)
    impresso_corrigido['tipoConteudo'] = tipo_detectado

    # Corrigir conteúdo baseado no tipo detectado
    if tipo_detectado == 'lista_chave_valor_secoes':
        impresso_corrigido['conteudo'] = corrigir_conteudo_lista_chave_valor(impresso.get('conteudo', {}))
    elif tipo_detectado == 'imagem_com_texto':
        impresso_corrigido['conteudo'] = corrigir_conteudo_imagem_texto(impresso.get('conteudo', {}))
    elif tipo_detectado == 'sinais_vitais':
        impresso_corrigido['conteudo'] = corrigir_conteudo_sinais_vitais(impresso.get('conteudo', {}))

    return impresso_corrigido

    return impresso_corrigido

def detectar_tipo_impresso(impresso: Dict[str, Any]) -> str:
    """Detecta automaticamente o tipo correto do impresso"""
    titulo = impresso.get('tituloImpresso', '').lower()
    tipo_atual = impresso.get('tipoConteudo', '')

    # Regras de detecção baseadas no título
    if 'exame físico' in titulo or 'exame fisico' in titulo or 'ef' in titulo:
        return 'lista_chave_valor_secoes'
    elif 'laboratoriais' in titulo or 'laboratorio' in titulo or 'lab' in titulo:
        return 'lista_chave_valor_secoes'
    elif 'ecg' in titulo or 'eletrocardiograma' in titulo:
        return 'imagem_com_texto'
    elif tipo_atual == 'tabela':
        return 'lista_chave_valor_secoes'
    elif tipo_atual == 'imagemComLaudo':
        return 'imagem_com_texto'
    elif 'sinais vitais' in titulo or 'sinais_vitais' in tipo_atual:
        return 'lista_chave_valor_secoes'  # Manter compatibilidade com validador
    else:
        # Manter tipo original para outros
        return tipo_atual

def corrigir_conteudo_sinais_vitais(conteudo: Dict[str, Any]) -> Dict[str, Any]:
    """Corrige conteúdo específico para sinais vitais"""
    if 'secoes' not in conteudo:
        return conteudo

    secoes_corrigidas = []

    for secao in conteudo['secoes']:
        if isinstance(secao, str):
            # Se for string JSON, converter para objeto
            try:
                # Limpar aspas escapadas incorretas
                secao_limpa = secao.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                secao_obj = json.loads(secao_limpa)
                secoes_corrigidas.append(secao_obj)
            except json.JSONDecodeError as e:
                print(f"Erro ao parsear seção: {e}")
                print(f"Seção problemática: {secao[:100]}...")
                # Tentar correção manual se for erro simples
                secoes_corrigidas.append(corrigir_secao_manual(secao))
            except Exception as e:
                print(f"Erro inesperado: {e}")
                secoes_corrigidas.append(secao)
        else:
            secoes_corrigidas.append(secao)

    return {'secoes': secoes_corrigidas}

    return impresso_corrigido

def corrigir_secao_manual(secao_str: str) -> Dict[str, Any]:
    """Corrige seção manualmente quando JSON malformado"""
    try:
        # Tentar extrair título da seção
        titulo_match = re.search(r'"tituloSecao"\s*:\s*"([^"]+)"', secao_str)
        titulo = titulo_match.group(1) if titulo_match else "Seção"

        # Tentar extrair itens
        itens = []
        item_matches = re.findall(r'\{"chave"\s*:\s*"([^"]+)"\s*,\s*"valor"\s*:\s*"([^"]+)"\}', secao_str)

        for chave, valor in item_matches:
            itens.append({"chave": chave, "valor": valor})

        return {"tituloSecao": titulo, "itens": itens}
    except:
        return {"tituloSecao": "Seção", "itens": []}

def adicionar_sistema_neurologico_se_necessario(secoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adiciona sistema neurológico se for exame físico e estiver faltando"""
    # Verificar se já tem sistema neurológico
    tem_neurologico = any('neurológ' in secao.get('tituloSecao', '').lower() for secao in secoes)

    if not tem_neurologico:
        # Verificar se é exame físico (tem cardiovascular e respiratório)
        tem_cardiovascular = any('cardiovascul' in secao.get('tituloSecao', '').lower() for secao in secoes)
        tem_respiratorio = any('respiratór' in secao.get('tituloSecao', '').lower() for secao in secoes)

        if tem_cardiovascular and tem_respiratorio:
            # Adicionar seção neurológica
            secao_neurologica = {
                "tituloSecao": "SISTEMA NEUROLÓGICO",
                "itens": [
                    {
                        "chave": "Estado mental",
                        "valor": "Consciente, orientado no tempo e espaço. Sem déficits cognitivos evidentes."
                    },
                    {
                        "chave": "Reflexos",
                        "valor": "Reflexos osteotendinosos presentes e simétricos. Reflexos patológicos ausentes."
                    },
                    {
                        "chave": "Força motora",
                        "valor": "Força grau V em todos os grupos musculares. Sem paresias."
                    },
                    {
                        "chave": "Sensibilidade",
                        "valor": "Sensibilidade preservada em todos os dermátomos. Sem hipoestesia."
                    }
                ]
            }
            secoes.append(secao_neurologica)

    return secoes

def corrigir_conteudo_lista_chave_valor(conteudo: Dict[str, Any]) -> Dict[str, Any]:
    """Corrige conteúdo do tipo lista_chave_valor_secoes"""
    if 'secoes' not in conteudo:
        return conteudo

    secoes_corrigidas = []

    for secao in conteudo['secoes']:
        if isinstance(secao, str):
            # Se for string JSON, converter para objeto
            try:
                # Limpar aspas escapadas incorretas
                secao_limpa = secao.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                secao_obj = json.loads(secao_limpa)
                secoes_corrigidas.append(secao_obj)
            except json.JSONDecodeError as e:
                print(f"Erro ao parsear seção: {e}")
                print(f"Seção problemática: {secao[:100]}...")
                # Tentar correção manual se for erro simples
                secoes_corrigidas.append(corrigir_secao_manual(secao))
            except Exception as e:
                print(f"Erro inesperado: {e}")
                secoes_corrigidas.append(secao)
        else:
            secoes_corrigidas.append(secao)

    # Verificar se é exame físico e adicionar sistema neurológico se necessário
    secoes_corrigidas = adicionar_sistema_neurologico_se_necessario(secoes_corrigidas)

    return {'secoes': secoes_corrigidas}

def corrigir_conteudo_imagem_texto(conteudo: Dict[str, Any]) -> Dict[str, Any]:
    """Corrige conteúdo do tipo imagem_com_texto"""
    # Para ECG, manter a estrutura existente mas limpar campos desnecessários
    conteudo_corrigido = {}

    if 'textoDescritivo' in conteudo:
        conteudo_corrigido['textoDescritivo'] = conteudo['textoDescritivo']

    if 'caminhoImagem' in conteudo:
        # Se for uma sugestão de busca, converter para caminho vazio
        caminho = conteudo['caminhoImagem']
        if 'Buscar no Google' in caminho or 'sugestaoBuscaImagem' in conteudo:
            conteudo_corrigido['caminhoImagem'] = ''
        else:
            conteudo_corrigido['caminhoImagem'] = caminho

    if 'laudo' in conteudo:
        conteudo_corrigido['laudo'] = conteudo['laudo']

    return conteudo_corrigido

def converter_tabela_para_secoes(conteudo_tabela: Dict[str, Any]) -> Dict[str, Any]:
    """Converte estrutura de tabela para seções"""
    if 'linhas' not in conteudo_tabela:
        return {'secoes': []}

    secoes = []
    secao_atual = {'tituloSecao': 'Exames Laboratoriais', 'itens': []}

    for linha in conteudo_tabela['linhas']:
        if isinstance(linha, str):
            try:
                # Remover aspas extras e converter
                linha_limpa = linha.strip('[]"')
                partes = [p.strip().strip('"') for p in linha_limpa.split('", "')]

                if len(partes) >= 2:
                    exame = partes[0]
                    resultado = partes[1]
                    vr = partes[2] if len(partes) > 2 else ''

                    item = {
                        'chave': exame,
                        'valor': f"{resultado}" + (f" (VR: {vr})" if vr else "")
                    }
                    secao_atual['itens'].append(item)
            except:
                continue

    if secao_atual['itens']:
        secoes.append(secao_atual)

    return {'secoes': secoes}

# JSON dos impressos com problemas
impressos_problematicos = '''[
      {
        "idImpresso": "est1_sv",
        "tituloImpresso": "SINAIS VITAIS",
        "tipoConteudo": "lista_chave_valor_secoes",
        "conteudo": {
          "secoes": [
            "{\\"tituloSecao\\": \\"SINAIS VITAIS\\", \\"itens\\": [{\\"chave\\": \\"Pressão arterial\\", \\"valor\\": \\"158 × 96 mmHg (braço direito, sentado); 155 × 94 mmHg (braço esquerdo, sentado)\\"}, {\\"chave\\": \\"Frequência cardíaca\\", \\"valor\\": \\"78 bpm\\"}, {\\"chave\\": \\"Frequência respiratória\\", \\"valor\\": \\"16 irpm\\"}, {\\"chave\\": \\"Temperatura\\", \\"valor\\": \\"36.6 °C\\"}, {\\"chave\\": \\"Saturação O2\\", \\"valor\\": \\"98% em ar ambiente\\"}]}"
          ]
        }
      },
      {
        "idImpresso": "est1_ef",
        "tituloImpresso": "EXAME FÍSICO",
        "tipoConteudo": "lista_chave_valor_secoes",
        "conteudo": {
          "secoes": [
            "{\\"tituloSecao\\": \\"ESTADO GERAL E ANTROPOMETRIA\\", \\"itens\\": [{\\"chave\\": \\"Estado geral\\", \\"valor\\": \\"Bom estado geral, consciente, orientado, hidratado, corado.\\"}, {\\"chave\\": \\"Peso\\", \\"valor\\": \\"90 kg\\"}, {\\"chave\\": \\"Altura\\", \\"valor\\": \\"1,75 m\\"}, {\\"chave\\": \\"IMC\\", \\"valor\\": \\"29.38 kg/m²\\"}, {\\"chave\\": \\"Circunferência abdominal\\", \\"valor\\": \\"102 cm\\"}]}",
            "{\\"tituloSecao\\": \\"APARELHO CARDIOVASCULAR\\", \\"itens\\": [{\\"chave\\": \\"Ausculta cardíaca\\", \\"valor\\": \\"Bulhas rítmicas em 2 tempos, normofonéticas. Sem sopros.\\"}, {\\"chave\\": \\"Pulsos\\", \\"valor\\": \\"Pulsos periféricos amplos e simétricos nos quatro membros.\\"}]}",
            "{\\"tituloSecao\\": \\"APARELHO RESPIRATÓRIO\\", \\"itens\\": [{\\"chave\\": \\"Ausculta pulmonar\\", \\"valor\\": \\"Murmúrio vesicular universalmente audível, sem ruídos adventícios.\\"}]}",
            "{\\"tituloSecao\\": \\"ABDOMEN\\", \\"itens\\": [{\\"chave\\": \\"Inspeção e Palpação\\", \\"valor\\": \\"Globoso às custas de panículo adiposo, flácido, indolor à palpação. RHA presentes. Sem massas ou visceromegalias.\\"}, {\\"chave\\": \\"Ausculta\\", \\"valor\\": \\"Sem sopros abdominais.\\"}]}",
            "{\\"tituloSecao\\": \\"EXTREMIDADES\\", \\"itens\\": [{\\"chave\\": \\"Achados\\", \\"valor\\": \\"Sem edemas, panturrilhas livres.\\"}]}"
          ]
        }
      },
      {
        "idImpresso": "est1_lab",
        "tituloImpresso": "EXAMES LABORATORIAIS DE ROTINA",
        "tipoConteudo": "tabela",
        "conteudo": {
          "cabecalho": [
            "Exame",
            "Resultado",
            "Valor de Referência"
          ],
          "linhas": [
            "[\\"Glicemia de jejum\\", \\"135 mg/dL\\", \\"70-99 mg/dL\\"]",
            "[\\"Hemoglobina Glicada (HbA1c)\\", \\"7.2%\\", \\"<5.7%\\"]",
            "[\\"Colesterol Total\\", \\"220 mg/dL\\", \\"<190 mg/dL\\"]",
            "[\\"LDL-c\\", \\"140 mg/dL\\", \\"<130 mg/dL\\"]",
            "[\\"HDL-c\\", \\"38 mg/dL\\", \\">40 mg/dL\\"]",
            "[\\"Triglicerídeos\\", \\"180 mg/dL\\", \\"<150 mg/dL\\"]",
            "[\\"Creatinina sérica\\", \\"1.1 mg/dL\\", \\"0.7-1.3 mg/dL\\"]",
            "[\\"TFG (CKD-EPI)\\", \\"75 mL/min/1.73m²\\", \\">60 mL/min/1.73m²\\"]",
            "[\\"Sódio\\", \\"140 mEq/L\\", \\"135-145 mEq/L\\"]",
            "[\\"Potássio\\", \\"4.2 mEq/L\\", \\"3.5-5.0 mEq/L\\"]",
            "[\\"TSH\\", \\"2.5 µUI/mL\\", \\"0.4-4.0 µUI/mL\\"]",
            "[\\"Sumário de Urina\\", \\"Aspecto límpido, sem alterações\\", \\"Normal\\"]",
            "[\\"Microalbuminúria\\", \\"25 mg/24h\\", \\"<30 mg/24h\\"]"
          ]
        }
      },
      {
        "idImpresso": "est1_ecg",
        "tituloImpresso": "ELETROCARDIOGRAMA (ECG)",
        "tipoConteudo": "imagemComLaudo",
        "conteudo": {
          "textoDescritivo": "[ATENÇÃO: DIRIJA-SE PARA A CÂMERA E EXPLIQUE OS ACHADOS NA IMAGEM].",
          "caminhoImagem": "(Buscar no Google Imagens: ECG com sobrecarga ventricular esquerda critério de Sokolow-Lyon)",
          "sugestaoBuscaImagem": "ECG com sobrecarga ventricular esquerda critério de Sokolow-Lyon",
          "laudo": "Ritmo sinusal, FC 75 bpm. Eixo elétrico normal. Sinais de sobrecarga de ventrículo esquerdo (critérios de Cornell e Sokolow-Lyon positivos). Ausência de alterações de repolarização significativas."
        }
      }
]'''

def main():
    """Função principal para demonstrar a correção"""
    print("🔧 CORRETOR DE IMPRESSOS JSON")
    print("=" * 50)

    print("\n📋 IMPRESSOS ORIGINAIS (com problemas):")
    print(impressos_problematicos[:500] + "...")

    # Corrigir os impressos
    impressos_corrigidos = corrigir_impressos_json(impressos_problematicos)

    print("\n\n✅ IMPRESSOS CORRIGIDOS:")
    print(impressos_corrigidos)

    # Salvar em arquivo
    with open('impressos_corrigidos.json', 'w', encoding='utf-8') as f:
        f.write(impressos_corrigidos)

    print("\n💾 Arquivo 'impressos_corrigidos.json' salvo com sucesso!")

    # Validar JSON
    try:
        json.loads(impressos_corrigidos)
        print("✅ JSON válido!")
    except Exception as e:
        print(f"❌ Erro no JSON: {e}")

if __name__ == "__main__":
    main()
