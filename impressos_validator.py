# -*- coding: utf-8 -*-
"""
Sistema de Validação de Impressos Médicos
Validação avançada para impressos antes do salvamento no Firestore
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class ImpressosValidator:
    """Validador especializado para impressos médicos"""
    
    def __init__(self):
        self.regras_formatacao = {
            'laboratorio': {
                'formato_valores': r'^[\d,.\s]+\s*[a-zA-ZµΩ/\s%]*$',
                'intervalos_obrigatorios': True,
                'unidades_obrigatorias': True,
                'campos_obrigatorios': ['chave', 'valor']
            },
            'imagem': {
                'descricao_minima': 50,
                'laudo_obrigatorio': True,
                'palavras_chave_obrigatorias': ['achados', 'conclusão', 'impressão'],
                'formato_laudo': r'(ACHADOS?|DESCRIÇÃO|CONCLUSÃO|IMPRESSÃO DIAGNÓSTICA?):'
            },
            'exame_fisico': {
                'formato_manobras': r'(positiv[oa]|negativ[oa]|ausente|presente)',
                'sistemas_obrigatorios': ['cardiovascular', 'respiratório', 'neurológico'],
                'formato_sinais_vitais': r'PA:\s*\d+x\d+|FC:\s*\d+|FR:\s*\d+|T:\s*\d+[,.]?\d*'
            }
        }
    
    def validar_impressos(self, estacao_data: Dict[str, Any]) -> Tuple[bool, List[str], List[Dict]]:
        """
        Valida todos os impressos de uma estação
        
        Returns:
            - is_valid: bool
            - errors: List[str] 
            - impressos_corrigidos: List[Dict]
        """
        try:
            materiais = estacao_data.get('materiaisDisponiveis', {})
            impressos = materiais.get('impressos', [])
            
            if not impressos:
                return True, [], []
            
            errors = []
            impressos_corrigidos = []
            
            for i, impresso in enumerate(impressos):
                # Validar estrutura básica
                basic_errors = self._validar_estrutura_basica(impresso, i)
                errors.extend(basic_errors)
                
                if basic_errors:
                    continue
                
                # Determinar tipo de exame e validar
                tipo_exame = self._determinar_tipo_exame(impresso)
                impresso_corrigido = self._validar_por_tipo(impresso, tipo_exame, i, errors)
                impressos_corrigidos.append(impresso_corrigido)
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info(f"✅ Validação de impressos: {len(impressos)} impressos válidos")
            else:
                logger.warning(f"⚠️ Validação de impressos: {len(errors)} erros encontrados")
                
            return is_valid, errors, impressos_corrigidos
            
        except Exception as e:
            logger.error(f"Erro na validação de impressos: {e}")
            return False, [f"Erro interno na validação: {str(e)}"], []
    
    def _validar_estrutura_basica(self, impresso: Dict, index: int) -> List[str]:
        """Valida estrutura básica do impresso"""
        errors = []
        
        # Campos obrigatórios
        campos_obrigatorios = ['idImpresso', 'tituloImpresso', 'tipoConteudo', 'conteudo']
        for campo in campos_obrigatorios:
            if not impresso.get(campo):
                errors.append(f"Impresso {index + 1}: Campo '{campo}' é obrigatório")
        
        # Validar ID único
        id_impresso = impresso.get('idImpresso', '')
        if id_impresso and not re.match(r'^[a-zA-Z0-9_-]+$', id_impresso):
            errors.append(f"Impresso {index + 1}: ID deve conter apenas letras, números, _ e -")
        
        # Validar título
        titulo = impresso.get('tituloImpresso', '')
        if titulo and len(titulo.strip()) < 5:
            errors.append(f"Impresso {index + 1}: Título deve ter pelo menos 5 caracteres")
        
        # Corrigir tipos de conteúdo inválidos automaticamente
        tipo = impresso.get('tipoConteudo')
        tipos_validos = ['texto_simples', 'imagem_com_texto', 'lista_chave_valor_secoes', 'sinais_vitais']
        
        # Mapeamento de correções automáticas
        mapeamento_tipos = {
            'imagemComLaudo': 'imagem_com_texto',
            'textosimples': 'texto_simples',
            'imagemComTexto': 'imagem_com_texto',
            'tabela': 'lista_chave_valor_secoes'
        }
        
        if tipo in mapeamento_tipos:
            tipo_corrigido = mapeamento_tipos[tipo]
            impresso['tipoConteudo'] = tipo_corrigido
            logger.info(f"Impresso {index + 1}: Tipo corrigido automaticamente: {tipo} → {tipo_corrigido}")
        elif tipo not in tipos_validos:
            errors.append(f"Impresso {index + 1}: Tipo '{tipo}' inválido. Tipos válidos: {tipos_validos}")
        
        return errors
    
    def _corrigir_strings_json(self, impresso: Dict, index: int, errors: List[str]) -> Dict:
        """Corrige strings JSON no conteúdo dos impressos"""
        if not isinstance(impresso, dict):
            return impresso
        
        impresso_corrigido = impresso.copy()
        conteudo = impresso.get('conteudo', {})
        
        if not isinstance(conteudo, dict):
            return impresso_corrigido
        
        # Verificar se há strings JSON nas seções
        secoes = conteudo.get('secoes', [])
        if isinstance(secoes, list):
            secoes_corrigidas = []
            strings_json_encontradas = False
            
            for secao in secoes:
                if isinstance(secao, str):
                    try:
                        # Tentar converter string JSON de volta para objeto
                        secao_obj = json.loads(secao)
                        secoes_corrigidas.append(secao_obj)
                        strings_json_encontradas = True
                    except (json.JSONDecodeError, TypeError):
                        # Se não conseguir fazer parse, manter como string
                        secoes_corrigidas.append(secao)
                else:
                    secoes_corrigidas.append(secao)
            
            if strings_json_encontradas:
                logger.info(f"Impresso {index + 1}: Strings JSON convertidas de volta para objetos")
                conteudo_corrigido = conteudo.copy()
                conteudo_corrigido['secoes'] = secoes_corrigidas
                impresso_corrigido['conteudo'] = conteudo_corrigido
        
        return impresso_corrigido
    
    def _determinar_tipo_exame(self, impresso: Dict) -> str:
        """Determina o tipo de exame baseado no título e conteúdo"""
        titulo = impresso.get('tituloImpresso', '').lower()
        conteudo = str(impresso.get('conteudo', '')).lower()
        
        # Exames de laboratório
        if any(palavra in titulo for palavra in ['hemograma', 'bioquímica', 'urina', 'fezes', 
                                                'glicemia', 'creatinina', 'tgo', 'tgp', 'colesterol']):
            return 'laboratorio'
        
        # Exames de imagem
        if any(palavra in titulo for palavra in ['raio-x', 'rx', 'tomografia', 'tc', 'ressonância', 
                                                'rm', 'ultrassom', 'us', 'ecg', 'ecocardiograma']):
            return 'imagem'
        
        # Exame físico
        if any(palavra in titulo for palavra in ['exame físico', 'semiologia', 'ausculta', 
                                                'palpação', 'inspeção']) and 'sinais vitais' not in titulo.lower():
            return 'exame_fisico'
        
        # Verificar pelo conteúdo se não identificou pelo título
        if 'valor de referência' in conteudo or 'vr:' in conteudo:
            return 'laboratorio'
        
        if 'achados' in conteudo and 'conclusão' in conteudo:
            return 'imagem'
        
        return 'geral'
    
    def _validar_por_tipo(self, impresso: Dict, tipo_exame: str, index: int, errors: List[str]) -> Dict:
        """Valida impresso baseado no tipo de exame identificado"""
        # Verificar se impresso é um dicionário
        if not isinstance(impresso, dict):
            errors.append(f"Impresso {index + 1}: Deve ser um dicionário, recebido {type(impresso)}")
            return impresso
        
        impresso_corrigido = impresso.copy()
        
        # Corrigir strings JSON no conteúdo
        impresso_corrigido = self._corrigir_strings_json(impresso_corrigido, index, errors)
        
        if tipo_exame == 'laboratorio':
            impresso_corrigido = self._validar_exame_laboratorio(impresso_corrigido, index, errors)
        elif tipo_exame == 'imagem':
            impresso_corrigido = self._validar_exame_imagem(impresso_corrigido, index, errors)
        elif tipo_exame == 'exame_fisico':
            impresso_corrigido = self._validar_exame_fisico(impresso_corrigido, index, errors)
        elif impresso.get('tipoConteudo') == 'sinais_vitais' or 'sinais vitais' in impresso.get('tituloImpresso', '').lower():
            impresso_corrigido = self._validar_sinais_vitais(impresso_corrigido, index, errors)
        else:
            # Validação geral para outros tipos
            impresso_corrigido = self._validar_geral(impresso_corrigido, index, errors)
        
        return impresso_corrigido
    
    def _validar_exame_laboratorio(self, impresso: Dict, index: int, errors: List[str]) -> Dict:
        """Validação específica para exames de laboratório"""
        if not isinstance(impresso, dict):
            return impresso
        
        impresso_corrigido = impresso.copy()
        conteudo = impresso.get('conteudo', {})
        
        if impresso.get('tipoConteudo') == 'lista_chave_valor_secoes':
            secoes = conteudo.get('secoes', [])
            secoes_corrigidas = []
            
            for secao in secoes:
                if not isinstance(secao, dict):
                    continue
                
                secao_corrigida = secao.copy()
                itens_corrigidos = []
                
                for item in secao.get('itens', []):
                    if isinstance(item, dict):
                        item_corrigido = self._validar_item_laboratorio(item, index, errors)
                        itens_corrigidos.append(item_corrigido)
                
                secao_corrigida['itens'] = itens_corrigidos
                secoes_corrigidas.append(secao_corrigida)
            
            impresso_corrigido['conteudo'] = {'secoes': secoes_corrigidas}
        
        return impresso_corrigido
    
    def _validar_item_laboratorio(self, item: Dict, index: int, errors: List[str]) -> Dict:
        """Valida item individual de laboratório"""
        item_corrigido = item.copy()
        chave = item.get('chave', '')
        valor = item.get('valor', '')
        
        if not chave or not valor:
            return item_corrigido
        
        # Validar formato do valor
        regras = self.regras_formatacao['laboratorio']
        
        # Verificar se tem valor de referência
        if 'VR:' not in valor and 'Referência:' not in valor and 'mg/dL' in valor:
            # Tentar adicionar valor de referência baseado no exame
            vr = self._obter_valor_referencia(chave.lower())
            if vr:
                item_corrigido['valor'] = f"{valor} (VR: {vr})"
        
        # Validar formato numérico
        valor_numerico = re.search(r'[\d,.]+ ', valor)
        if valor_numerico and not re.match(regras['formato_valores'], valor_numerico.group()):
            errors.append(f"Impresso {index + 1}: Formato inválido para '{chave}': {valor}")
        
        return item_corrigido
    
    def _validar_exame_imagem(self, impresso: Dict, index: int, errors: List[str]) -> Dict:
        """Validação específica para exames de imagem"""
        impresso_corrigido = impresso.copy()
        conteudo = impresso.get('conteudo', {})
        
        if impresso.get('tipoConteudo') == 'imagem_com_texto':
            # Validar laudo obrigatório
            laudo = conteudo.get('laudo', '')
            if not laudo or len(laudo.strip()) < 50:
                errors.append(f"Impresso {index + 1}: Laudo deve ter pelo menos 50 caracteres")
            
            # Validar estrutura do laudo
            regras = self.regras_formatacao['imagem']
            if laudo and not re.search(regras['formato_laudo'], laudo, re.IGNORECASE):
                # Corrigir automaticamente adicionando estrutura
                laudo_corrigido = self._estruturar_laudo(laudo)
                impresso_corrigido['conteudo']['laudo'] = laudo_corrigido
            
            # Validar descrição mínima
            descricao = conteudo.get('textoDescritivo', '')
            if descricao and len(descricao.strip()) < regras['descricao_minima']:
                errors.append(f"Impresso {index + 1}: Descrição deve ter pelo menos {regras['descricao_minima']} caracteres")
        
        return impresso_corrigido
    
    def _validar_exame_fisico(self, impresso: Dict, index: int, errors: List[str]) -> Dict:
        """Validação específica para exames físicos"""
        if not isinstance(impresso, dict):
            return impresso
        
        impresso_corrigido = impresso.copy()
        conteudo = impresso.get('conteudo', {})
        
        if impresso.get('tipoConteudo') == 'lista_chave_valor_secoes':
            secoes = conteudo.get('secoes', [])
            
            # Verificar se tem sistemas obrigatórios
            regras = self.regras_formatacao['exame_fisico']
            sistemas_encontrados = []
            
            for secao in secoes:
                if isinstance(secao, dict):
                    titulo_secao = secao.get('tituloSecao', '').lower()
                    sistemas_encontrados.extend([s for s in regras['sistemas_obrigatorios'] 
                                               if s in titulo_secao])
            
            sistemas_faltando = set(regras['sistemas_obrigatorios']) - set(sistemas_encontrados)
            if sistemas_faltando:
                errors.append(f"Impresso {index + 1}: Sistemas obrigatórios ausentes: {list(sistemas_faltando)}")
        
        return impresso_corrigido
    
    def _validar_sinais_vitais(self, impresso: Dict, index: int, errors: List[str]) -> Dict:
        """Validação específica para sinais vitais"""
        if not isinstance(impresso, dict):
            return impresso
        
        impresso_corrigido = impresso.copy()
        conteudo = impresso.get('conteudo', {})
        
        if impresso.get('tipoConteudo') == 'sinais_vitais':
            secoes = conteudo.get('secoes', [])
            
            # Verificar se tem os sinais vitais básicos
            sinais_obrigatorios = ['pressão arterial', 'frequência cardíaca', 'frequência respiratória', 'temperatura']
            sinais_encontrados = []
            
            for secao in secoes:
                if isinstance(secao, dict):
                    for item in secao.get('itens', []):
                        if isinstance(item, dict):
                            chave = item.get('chave', '').lower()
                            sinais_encontrados.extend([s for s in sinais_obrigatorios if s in chave])
            
            sinais_faltando = set(sinais_obrigatorios) - set(sinais_encontrados)
            if sinais_faltando:
                errors.append(f"Impresso {index + 1}: Sinais vitais obrigatórios ausentes: {list(sinais_faltando)}")
        
        return impresso_corrigido
    
    def _validar_geral(self, impresso: Dict, index: int, errors: List[str]) -> Dict:
        """Validação geral para outros tipos de impresso"""
        if not isinstance(impresso, dict):
            return impresso
        
        impresso_corrigido = impresso.copy()
        
        # Validações básicas de conteúdo
        tipo = impresso.get('tipoConteudo')
        conteudo = impresso.get('conteudo', {})
        
        if tipo == 'texto_simples':
            texto = conteudo.get('texto', '')
            if texto and len(texto.strip()) < 10:
                errors.append(f"Impresso {index + 1}: Texto muito curto (mínimo 10 caracteres)")
        
        return impresso_corrigido
    
    def _obter_valor_referencia(self, nome_exame: str) -> Optional[str]:
        """Retorna valor de referência padrão para exames comuns"""
        valores_referencia = {
            'hemoglobina': '12-16 g/dL',
            'hematócrito': '36-46%',
            'leucócitos': '4.000-11.000/mm³',
            'plaquetas': '150.000-450.000/mm³',
            'glicemia': '70-99 mg/dL',
            'creatinina': '0,6-1,2 mg/dL',
            'ureia': '15-40 mg/dL',
            'colesterol total': '<200 mg/dL',
            'tgo': '10-40 U/L',
            'tgp': '7-41 U/L'
        }
        
        for exame, vr in valores_referencia.items():
            if exame in nome_exame:
                return vr
        return None
    
    def _estruturar_laudo(self, laudo_original: str) -> str:
        """Estrutura automaticamente um laudo de exame de imagem"""
        if not laudo_original:
            return laudo_original
        
        # Se já tem estrutura, retorna como está
        if re.search(r'(ACHADOS?|CONCLUSÃO|IMPRESSÃO):', laudo_original, re.IGNORECASE):
            return laudo_original
        
        # Adiciona estrutura básica
        return f"ACHADOS:\n{laudo_original}\n\nCONCLUSÃO:\n[A ser preenchida conforme achados]"

def validar_impressos_estacao(estacao_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Função principal para validação de impressos
    
    Args:
        estacao_data: Dados completos da estação
        
    Returns:
        - is_valid: bool
        - errors: List[str]
        - estacao_corrigida: Dict com impressos corrigidos
    """
    validator = ImpressosValidator()
    is_valid, errors, impressos_corrigidos = validator.validar_impressos(estacao_data)
    
    if impressos_corrigidos:
        estacao_corrigida = estacao_data.copy()
        if 'materiaisDisponiveis' not in estacao_corrigida:
            estacao_corrigida['materiaisDisponiveis'] = {}
        estacao_corrigida['materiaisDisponiveis']['impressos'] = impressos_corrigidos
    else:
        estacao_corrigida = estacao_data
    
    return is_valid, errors, estacao_corrigida

# Exemplo de uso
if __name__ == "__main__":
    # Teste básico
    estacao_exemplo = {
        "materiaisDisponiveis": {
            "impressos": [
                {
                    "idImpresso": "hemograma_001",
                    "tituloImpresso": "Hemograma Completo",
                    "tipoConteudo": "lista_chave_valor_secoes",
                    "conteudo": {
                        "secoes": [
                            {
                                "tituloSecao": "Série Vermelha",
                                "itens": [
                                    {"chave": "Hemoglobina", "valor": "12.5"},
                                    {"chave": "Hematócrito", "valor": "38%"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }
    
    is_valid, errors, corrigida = validar_impressos_estacao(estacao_exemplo)
    print(f"Válido: {is_valid}")
    print(f"Erros: {errors}")
