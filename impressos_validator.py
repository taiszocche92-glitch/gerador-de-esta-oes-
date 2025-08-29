"""
Módulo de Validação de Impressos Médicos
Sistema de validação especializada para impressos médicos em estações REVALIDA
"""

import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("impressos_validator")

class ImpressosValidator:
    """
    Validador especializado para impressos médicos em estações clínicas REVALIDA
    """

    def __init__(self):
        """Inicializa o validador com regras específicas para impressos médicos"""
        self.validation_rules = {
            "tipos_validos": [
                "receita_medica",
                "atestado_medico",
                "laudo_medico",
                "relatorio_medico",
                "solicitacao_exames",
                "encaminhamento_medico",
                "declaracao_medica",
                "prescricao_medicamentosa",
                "lista_chave_valor_secoes",
                "formulario_clinico"
            ],
            "campos_obrigatorios": {
                "tituloImpresso": str,
                "tipo": str,
                "conteudo": dict
            },
            "validacoes_conteudo": {
                "lista_chave_valor_secoes": self._validar_lista_chave_valor_secoes,
                "receita_medica": self._validar_receita_medica,
                "atestado_medico": self._validar_atestado_medico,
                "laudo_medico": self._validar_laudo_medico
            }
        }

        logger.info("ImpressosValidator inicializado com sucesso")

    def validar_impressos_estacao(self, estacao_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Valida todos os impressos de uma estação clínica

        Args:
            estacao_data: Dados completos da estação

        Returns:
            Tuple: (is_valid, errors_list, corrected_station_data)
        """
        try:
            logger.info("Iniciando validação de impressos da estação")

            is_valid = True
            errors = []
            estacao_corrigida = estacao_data.copy()

            # Verificar se há materiais disponíveis
            if "materiaisDisponiveis" not in estacao_data:
                errors.append("Campo 'materiaisDisponiveis' ausente na estação")
                is_valid = False
                return is_valid, errors, estacao_corrigida

            materiais = estacao_data["materiaisDisponiveis"]

            # Verificar se há impressos
            if "impressos" not in materiais:
                errors.append("Campo 'impressos' ausente em materiaisDisponiveis")
                is_valid = False
                return is_valid, errors, estacao_corrigida

            impressos = materiais["impressos"]

            if not isinstance(impressos, list):
                errors.append("Campo 'impressos' deve ser uma lista")
                is_valid = False
                return is_valid, errors, estacao_corrigida

            if len(impressos) == 0:
                logger.info("Nenhum impresso encontrado para validação")
                return True, [], estacao_data

            # Validar cada impresso
            impressos_corrigidos = []
            for i, impresso in enumerate(impressos):
                logger.info(f"Validando impresso {i+1}/{len(impressos)}")

                impresso_valid, impresso_errors, impresso_corrigido = self._validar_impresso_individual(impresso, i)

                if not impresso_valid:
                    is_valid = False
                    errors.extend(impresso_errors)

                impressos_corrigidos.append(impresso_corrigido)

            # Atualizar estação com impressos corrigidos
            if impressos_corrigidos != impressos:
                estacao_corrigida["materiaisDisponiveis"]["impressos"] = impressos_corrigidos
                logger.info("Impressos corrigidos aplicados à estação")

            logger.info(f"Validação concluída: {len(errors)} erros encontrados")
            return is_valid, errors, estacao_corrigida

        except Exception as e:
            error_msg = f"Erro crítico na validação de impressos: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg], estacao_data

    def _validar_impresso_individual(self, impresso: Dict[str, Any], index: int) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Valida um impresso individual

        Args:
            impresso: Dados do impresso
            index: Índice do impresso na lista

        Returns:
            Tuple: (is_valid, errors_list, corrected_impresso)
        """
        errors = []
        impresso_corrigido = impresso.copy()
        is_valid = True

        # Verificar campos obrigatórios
        for campo, tipo_esperado in self.validation_rules["campos_obrigatorios"].items():
            if campo not in impresso:
                errors.append(f"Impresso {index+1}: Campo obrigatório '{campo}' ausente")
                is_valid = False
            elif not isinstance(impresso[campo], tipo_esperado):
                errors.append(f"Impresso {index+1}: Campo '{campo}' deve ser do tipo {tipo_esperado.__name__}")
                is_valid = False

        if not is_valid:
            return is_valid, errors, impresso_corrigido

        # Validar tipo do impresso
        tipo = impresso.get("tipo", "")
        if tipo not in self.validation_rules["tipos_validos"]:
            errors.append(f"Impresso {index+1}: Tipo '{tipo}' não é válido. Tipos válidos: {self.validation_rules['tipos_validos']}")
            is_valid = False
        else:
            # Aplicar validação específica do tipo
            if tipo in self.validation_rules["validacoes_conteudo"]:
                tipo_valid, tipo_errors, tipo_corrigido = self.validation_rules["validacoes_conteudo"][tipo](impresso, index)
                if not tipo_valid:
                    errors.extend(tipo_errors)
                    is_valid = False
                impresso_corrigido = tipo_corrigido

        return is_valid, errors, impresso_corrigido

    def _validar_lista_chave_valor_secoes(self, impresso: Dict[str, Any], index: int) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Valida impresso do tipo lista_chave_valor_secoes"""
        errors = []
        impresso_corrigido = impresso.copy()
        is_valid = True

        conteudo = impresso.get("conteudo", {})

        if "secoes" not in conteudo:
            errors.append(f"Impresso {index+1}: Campo 'secoes' ausente no conteúdo")
            is_valid = False
        else:
            secoes = conteudo["secoes"]
            if not isinstance(secoes, list):
                errors.append(f"Impresso {index+1}: Campo 'secoes' deve ser uma lista")
                is_valid = False
            elif len(secoes) == 0:
                errors.append(f"Impresso {index+1}: Lista 'secoes' não pode estar vazia")
                is_valid = False
            else:
                # Validar cada seção
                secoes_corrigidas = []
                for i, secao in enumerate(secoes):
                    if isinstance(secao, dict):
                        secoes_corrigidas.append(secao)
                    elif isinstance(secao, str):
                        # Tentar converter string JSON para dict
                        try:
                            secao_dict = json.loads(secao)
                            secoes_corrigidas.append(secao_dict)
                        except json.JSONDecodeError:
                            errors.append(f"Impresso {index+1}: Seção {i+1} não é um JSON válido")
                            is_valid = False
                            secoes_corrigidas.append(secao)
                    else:
                        errors.append(f"Impresso {index+1}: Seção {i+1} deve ser dict ou string JSON")
                        is_valid = False
                        secoes_corrigidas.append(secao)

                if secoes_corrigidas != secoes:
                    impresso_corrigido["conteudo"]["secoes"] = secoes_corrigidas

        return is_valid, errors, impresso_corrigido

    def _validar_receita_medica(self, impresso: Dict[str, Any], index: int) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Valida impresso do tipo receita_medica"""
        errors = []
        impresso_corrigido = impresso.copy()
        is_valid = True

        conteudo = impresso.get("conteudo", {})

        # Campos obrigatórios para receita médica
        campos_obrigatorios = ["paciente", "medicamentos", "data", "crm_medico"]
        for campo in campos_obrigatorios:
            if campo not in conteudo:
                errors.append(f"Impresso {index+1}: Campo obrigatório '{campo}' ausente na receita médica")
                is_valid = False

        # Validar medicamentos
        if "medicamentos" in conteudo:
            medicamentos = conteudo["medicamentos"]
            if not isinstance(medicamentos, list):
                errors.append(f"Impresso {index+1}: Campo 'medicamentos' deve ser uma lista")
                is_valid = False
            elif len(medicamentos) == 0:
                errors.append(f"Impresso {index+1}: Lista 'medicamentos' não pode estar vazia")
                is_valid = False

        return is_valid, errors, impresso_corrigido

    def _validar_atestado_medico(self, impresso: Dict[str, Any], index: int) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Valida impresso do tipo atestado_medico"""
        errors = []
        impresso_corrigido = impresso.copy()
        is_valid = True

        conteudo = impresso.get("conteudo", {})

        # Campos obrigatórios para atestado médico
        campos_obrigatorios = ["paciente", "cid", "dias_afastamento", "data", "crm_medico"]
        for campo in campos_obrigatorios:
            if campo not in conteudo:
                errors.append(f"Impresso {index+1}: Campo obrigatório '{campo}' ausente no atestado médico")
                is_valid = False

        return is_valid, errors, impresso_corrigido

    def _validar_laudo_medico(self, impresso: Dict[str, Any], index: int) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Valida impresso do tipo laudo_medico"""
        errors = []
        impresso_corrigido = impresso.copy()
        is_valid = True

        conteudo = impresso.get("conteudo", {})

        # Campos obrigatórios para laudo médico
        campos_obrigatorios = ["paciente", "exame", "conclusao", "data", "crm_medico"]
        for campo in campos_obrigatorios:
            if campo not in conteudo:
                errors.append(f"Impresso {index+1}: Campo obrigatório '{campo}' ausente no laudo médico")
                is_valid = False

        return is_valid, errors, impresso_corrigido


# Instância global do validador
_validator_instance = None

def get_validator() -> ImpressosValidator:
    """Retorna instância singleton do validador"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ImpressosValidator()
    return _validator_instance

def validar_impressos_estacao(estacao_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Função principal para validar impressos de uma estação
    Interface compatível com o código existente em main.py

    Args:
        estacao_data: Dados da estação a ser validada

    Returns:
        Tuple: (is_valid, errors_list, corrected_station_data)
    """
    try:
        validator = get_validator()
        return validator.validar_impressos_estacao(estacao_data)
    except Exception as e:
        logger.error(f"Erro na função validar_impressos_estacao: {e}")
        return False, [f"Erro interno do validador: {str(e)}"], estacao_data

# Função de compatibilidade para testes
def validar_impresso_test(impresso_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Função para testar validação de um impresso individual
    """
    validator = get_validator()
    return validator._validar_impresso_individual(impresso_data, 0)

if __name__ == "__main__":
    # Exemplo de uso para testes
    print("Testando ImpressosValidator...")

    # Exemplo de impresso válido
    exemplo_impresso = {
        "tituloImpresso": "Receita Médica Modelo",
        "tipo": "receita_medica",
        "conteudo": {
            "paciente": "João Silva",
            "medicamentos": ["Paracetamol 500mg", "Ibuprofeno 400mg"],
            "data": "2024-01-15",
            "crm_medico": "CRM/SP 123456"
        }
    }

    validator = get_validator()
    is_valid, errors, corrigido = validator._validar_impresso_individual(exemplo_impresso, 0)

    print(f"Impresso válido: {is_valid}")
    if errors:
        print("Erros encontrados:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Nenhum erro encontrado!")

    print("Teste concluído!")
