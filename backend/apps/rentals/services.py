"""
Serviço de negócio para Locações.

Encapsula lógica de cálculo de taxas, validação de datas e
verificação de disponibilidade de itens. Mantém os views e
serializers limpos, delegando regras de negócio para cá.
"""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from apps.rentals.models import Locacao, StatusLocacao


# ──────────────────────────────────────────────────────────────
# Constantes de negócio
# ──────────────────────────────────────────────────────────────

TAXA_SERVICO_LOCATARIO = Decimal("0.10")   # 10 % sobre diárias
TAXA_SUCESSO_LOCADOR = Decimal("0.15")     # 15 % sobre valor recebido


class LocacaoService:
    """
    Serviço centralizado de regras de negócio para Locações.

    Responsabilidades:
        - Cálculo de valores e taxas
        - Validação de datas
        - Verificação de disponibilidade do item
    """

    # ──────────────────────────────────────────────────────────
    # Cálculo de valores
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def calcular_numero_diarias(data_inicio: date, data_fim: date) -> int:
        """
        Calcula o número de diárias entre duas datas.

        Mínimo de 1 diária (mesmo para mesmo dia).

        Args:
            data_inicio: Data de início da locação.
            data_fim: Data de fim da locação.

        Returns:
            Quantidade de diárias (inteiro >= 1).
        """
        delta = (data_fim - data_inicio).days
        return max(delta, 1)

    @staticmethod
    def calcular_valores(
        preco_diaria: Decimal,
        data_inicio: date,
        data_fim: date,
        valor_caucao: Decimal,
    ) -> dict[str, Decimal]:
        """
        Calcula todos os valores financeiros de uma locação.

        Regras de split (gemini.md §4.5):
            - Taxa de Serviço: 10 % sobre diárias (pago pelo locatário)
            - Taxa de Sucesso: 15 % sobre diárias (retido do locador)
            - Total Locatário: diárias + taxa de serviço

        Args:
            preco_diaria: Preço da diária do item.
            data_inicio: Data de início da locação.
            data_fim: Data de fim da locação.
            valor_caucao: Valor da caução do item.

        Returns:
            Dicionário com todas as parcelas calculadas:
                - numero_diarias
                - valor_diarias
                - valor_taxa_servico
                - valor_taxa_sucesso
                - total_locatario
                - valor_caucao
        """
        centavos = Decimal("0.01")
        num_diarias = LocacaoService.calcular_numero_diarias(data_inicio, data_fim)

        valor_diarias = (preco_diaria * num_diarias).quantize(
            centavos, rounding=ROUND_HALF_UP
        )
        valor_taxa_servico = (valor_diarias * TAXA_SERVICO_LOCATARIO).quantize(
            centavos, rounding=ROUND_HALF_UP
        )
        valor_taxa_sucesso = (valor_diarias * TAXA_SUCESSO_LOCADOR).quantize(
            centavos, rounding=ROUND_HALF_UP
        )
        total_locatario = valor_diarias + valor_taxa_servico

        return {
            "numero_diarias": num_diarias,
            "valor_diarias": valor_diarias,
            "valor_taxa_servico": valor_taxa_servico,
            "valor_taxa_sucesso": valor_taxa_sucesso,
            "total_locatario": total_locatario,
            "valor_caucao": valor_caucao,
        }

    # ──────────────────────────────────────────────────────────
    # Validação de datas
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def validar_datas(data_inicio: date, data_fim: date) -> list[str]:
        """
        Valida as datas de uma locação.

        Regras:
            - data_inicio não pode ser no passado
            - data_fim deve ser >= data_inicio
            - Período máximo de 30 dias (regra de negócio MVP)

        Args:
            data_inicio: Data de início da locação.
            data_fim: Data de fim da locação.

        Returns:
            Lista de mensagens de erro. Vazia se válido.
        """
        erros: list[str] = []
        hoje = date.today()

        if data_inicio < hoje:
            erros.append("A data de início não pode ser no passado.")

        if data_fim < data_inicio:
            erros.append("A data de fim deve ser igual ou posterior à data de início.")

        delta = (data_fim - data_inicio).days
        if delta > 30:
            erros.append("O período máximo de locação é de 30 dias.")

        return erros

    # ──────────────────────────────────────────────────────────
    # Disponibilidade
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def verificar_disponibilidade(
        item_id: str,
        data_inicio: date,
        data_fim: date,
        excluir_locacao_id: str | None = None,
    ) -> bool:
        """
        Verifica se o item está disponível no período solicitado.

        Um item é considerado indisponível se existe outra locação
        ativa (status não-terminal) com sobreposição de datas.

        Args:
            item_id: UUID do item a verificar.
            data_inicio: Data de início desejada.
            data_fim: Data de fim desejada.
            excluir_locacao_id: ID de locação a excluir da verificação
                (útil para edição).

        Returns:
            True se o item está disponível, False caso contrário.
        """
        # Status que indicam locação ainda "viva" (não-terminal)
        status_bloqueantes = [
            StatusLocacao.SOLICITADO,
            StatusLocacao.CAUCAO_RETIDA,
            StatusLocacao.ATIVO,
            StatusLocacao.DEVOLVIDO,
            StatusLocacao.CONTESTADO,
        ]

        conflitos = Locacao.objects.filter(
            item_id=item_id,
            status__in=status_bloqueantes,
        ).filter(
            # Sobreposição de datas: início_existente <= fim_nova E
            # fim_existente >= início_nova
            Q(data_inicio__lte=data_fim) & Q(data_fim__gte=data_inicio),
        )

        if excluir_locacao_id:
            conflitos = conflitos.exclude(id=excluir_locacao_id)

        return not conflitos.exists()
