"""
Signals do módulo ESG do Aloogaí.

Dispara o cálculo de CO₂ quando uma locação é concluída.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='rentals.Locacao')
def processar_esg_locacao_concluida(sender, instance, **kwargs):
    """
    Quando uma locação muda para CONCLUIDO, calcula o CO₂ economizado
    e atualiza os scores ESG dos usuários envolvidos.
    """
    if instance.status == 'CONCLUIDO' and instance.co2_evitado == 0.0:
        try:
            from apps.esg.services import ESGService

            resultado = ESGService.processar_locacao_concluida(instance)
            logger.info(
                'Processamento ESG concluído para locação %s: %s',
                instance.id, resultado
            )
        except Exception as e:
            logger.error(
                'Erro no processamento ESG da locação %s: %s',
                instance.id, str(e)
            )
