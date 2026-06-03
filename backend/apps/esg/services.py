"""
Serviço de cálculo ESG do Aloogaí.

Calcula a pegada de carbono economizada por cada locação concluída
e gerencia o sistema de selos ecológicos.

Fórmula: CO₂ Economizado = (co2_fabricacao_kg × fator_reuso) + reducao_frete_kg
"""

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class ESGService:
    """Serviço centralizado para cálculos ESG e gamificação."""

    @staticmethod
    def calcular_co2_economizado(locacao):
        """
        Calcula o CO₂ economizado em uma locação concluída.

        Usa os fatores de referência da categoria do item para
        estimar a redução de emissões.

        Returns:
            float: Quantidade de CO₂ economizado em kg.
        """
        from apps.esg.models import FatorESGCategoria

        try:
            fator = FatorESGCategoria.objects.get(
                categoria=locacao.item.categoria
            )
        except FatorESGCategoria.DoesNotExist:
            # Usar valores padrão se a categoria não tem fator configurado
            logger.warning(
                'Fator ESG não encontrado para categoria %s. '
                'Usando valores padrão.',
                locacao.item.categoria.nome
            )
            co2_fabricacao_kg = 5.0
            fator_reuso = 0.7
            reducao_frete_kg = 1.0
        else:
            co2_fabricacao_kg = fator.co2_fabricacao_kg
            fator_reuso = fator.fator_reuso
            reducao_frete_kg = fator.reducao_frete_kg

        # Fórmula: CO₂ = (fabricação × reuso) + redução de frete
        co2_economizado = (co2_fabricacao_kg * fator_reuso) + reducao_frete_kg

        # Multiplicar pelo número de dias (mais dias = mais economia)
        dias = (locacao.data_fim - locacao.data_inicio).days
        if dias < 1:
            dias = 1
        co2_economizado *= dias

        logger.info(
            'CO₂ economizado calculado: %.2f kg para locação %s (%d dias)',
            co2_economizado, locacao.id, dias
        )

        return round(co2_economizado, 2)

    @staticmethod
    @transaction.atomic
    def atualizar_score_usuario(usuario, co2_economizado):
        """
        Atualiza o score ESG do usuário com o CO₂ economizado.

        Args:
            usuario: Instância do Usuario
            co2_economizado: Quantidade de CO₂ em kg

        Returns:
            tuple: (score_anterior, score_novo)
        """
        score_anterior = usuario.score_esg
        score_novo = score_anterior + co2_economizado

        usuario.score_esg = score_novo
        usuario.save(update_fields=['score_esg'])

        logger.info(
            'Score ESG atualizado para %s: %.2f → %.2f (+%.2f)',
            usuario.get_full_name(), score_anterior, score_novo, co2_economizado
        )

        return score_anterior, score_novo

    @staticmethod
    @transaction.atomic
    def registrar_historico(usuario, locacao, co2_economizado, score_anterior, score_novo):
        """Registra o cálculo ESG no histórico."""
        from apps.esg.models import HistoricoESG

        historico = HistoricoESG.objects.create(
            usuario=usuario,
            locacao=locacao,
            co2_economizado=co2_economizado,
            score_anterior=score_anterior,
            score_novo=score_novo,
        )

        logger.info('Histórico ESG registrado: %s', historico.id)
        return historico

    @staticmethod
    def verificar_selos(usuario):
        """
        Verifica se o usuário desbloqueou novos selos ecológicos.

        Returns:
            list: Lista de selos recém-desbloqueados.
        """
        from apps.esg.models import SeloESG, UsuarioSelo

        # Contar locações concluídas do usuário (como locatário)
        from apps.rentals.models import Locacao
        total_locacoes = Locacao.objects.filter(
            locatario=usuario,
            status='CONCLUIDO',
        ).count()

        # Buscar selos que o usuário ainda não tem
        selos_atuais = UsuarioSelo.objects.filter(
            usuario=usuario
        ).values_list('selo_id', flat=True)

        selos_disponiveis = SeloESG.objects.exclude(
            id__in=selos_atuais
        )

        selos_desbloqueados = []

        for selo in selos_disponiveis:
            desbloqueou = True

            if selo.requisito_locacoes and total_locacoes < selo.requisito_locacoes:
                desbloqueou = False

            if selo.requisito_score and usuario.score_esg < selo.requisito_score:
                desbloqueou = False

            if desbloqueou:
                UsuarioSelo.objects.create(
                    usuario=usuario,
                    selo=selo,
                    desbloqueado_em=timezone.now(),
                )
                selos_desbloqueados.append(selo)

                logger.info(
                    'Selo desbloqueado: "%s" para %s',
                    selo.nome, usuario.get_full_name()
                )

        return selos_desbloqueados

    @classmethod
    def processar_locacao_concluida(cls, locacao):
        """
        Pipeline completo de processamento ESG para uma locação concluída.

        1. Calcula CO₂ economizado
        2. Atualiza score do locatário
        3. Atualiza score do locador
        4. Registra histórico
        5. Verifica selos desbloqueados
        6. Envia notificações

        Returns:
            dict: Resumo do processamento ESG.
        """
        co2 = cls.calcular_co2_economizado(locacao)

        # Atualizar locação
        locacao.co2_evitado = co2
        locacao.save(update_fields=['co2_evitado'])

        # Atualizar locatário
        score_ant_loc, score_novo_loc = cls.atualizar_score_usuario(
            locacao.locatario, co2
        )
        cls.registrar_historico(
            locacao.locatario, locacao, co2, score_ant_loc, score_novo_loc
        )
        selos_locatario = cls.verificar_selos(locacao.locatario)

        # Atualizar locador (recebe metade do CO₂ por disponibilizar o item)
        co2_locador = round(co2 * 0.5, 2)
        score_ant_ldr, score_novo_ldr = cls.atualizar_score_usuario(
            locacao.item.locador, co2_locador
        )
        selos_locador = cls.verificar_selos(locacao.item.locador)

        # Enviar notificações
        try:
            from apps.notifications.services import NotificacaoService

            NotificacaoService.criar_notificacao(
                usuario=locacao.locatario,
                titulo='🌱 Impacto ambiental positivo!',
                mensagem=(
                    f'Você economizou {co2:.1f} kg de CO₂ com esta locação. '
                    f'Seu score ESG agora é {score_novo_loc:.1f}!'
                ),
                tipo='ESG',
                dados_extras={'co2': co2, 'score': score_novo_loc},
            )

            for selo in selos_locatario:
                NotificacaoService.criar_notificacao(
                    usuario=locacao.locatario,
                    titulo=f'🏅 Novo selo: {selo.nome}!',
                    mensagem=selo.descricao,
                    tipo='ESG',
                    dados_extras={'selo_id': str(selo.id), 'selo_nome': selo.nome},
                )
        except Exception as e:
            logger.error('Erro ao enviar notificações ESG: %s', str(e))

        return {
            'co2_economizado': co2,
            'locatario': {
                'score_anterior': score_ant_loc,
                'score_novo': score_novo_loc,
                'selos_desbloqueados': [s.nome for s in selos_locatario],
            },
            'locador': {
                'co2_creditado': co2_locador,
                'score_anterior': score_ant_ldr,
                'score_novo': score_novo_ldr,
                'selos_desbloqueados': [s.nome for s in selos_locador],
            },
        }
