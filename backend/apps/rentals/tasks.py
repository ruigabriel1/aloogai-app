"""
Tasks assíncronas do app de Locações.

Tarefas executadas via Celery para operações que não
devem bloquear o request/response cycle.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='rentals.expirar_solicitacoes_pendentes')
def expirar_solicitacoes_pendentes():
    """
    Expira locações com status SOLICITADO há mais de 24 horas.

    Regra de negócio: Solicitações não confirmadas (sem retenção
    de caução) dentro de 24h são automaticamente canceladas.

    Esta task deve ser registrada no Celery Beat para rodar
    a cada hora (ou conforme configuração desejada).

    Returns:
        dict com contagem de locações expiradas.
    """
    from apps.rentals.models import Locacao, StatusLocacao

    limite = timezone.now() - timedelta(hours=24)

    locacoes_pendentes = Locacao.objects.filter(
        status=StatusLocacao.SOLICITADO,
        created_at__lt=limite,
    )

    total = locacoes_pendentes.count()

    if total == 0:
        logger.info('Nenhuma solicitação pendente para expirar.')
        return {'expiradas': 0}

    expiradas = 0
    erros = 0

    for locacao in locacoes_pendentes:
        try:
            locacao.cancelar()
            locacao.save()
            expiradas += 1
            logger.info(
                'Locação %s expirada automaticamente (criada em %s).',
                locacao.id,
                locacao.created_at,
            )
        except Exception as e:
            erros += 1
            logger.error(
                'Erro ao expirar locação %s: %s',
                locacao.id,
                str(e),
            )

    logger.info(
        'Expiração concluída: %d expiradas, %d erros de %d pendentes.',
        expiradas, erros, total,
    )

    return {
        'expiradas': expiradas,
        'erros': erros,
        'total_pendentes': total,
    }
