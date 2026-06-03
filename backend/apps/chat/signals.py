"""
Signals do app de Chat do Aloogaí.

Cria automaticamente uma SalaChat quando uma nova Locação é criada,
vinculando locador (dono do item) e locatário.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='rentals.Locacao')
def criar_sala_chat_para_locacao(sender, instance, created, **kwargs):
    """
    Cria uma SalaChat automaticamente quando uma Locação é criada.

    Regra comportamental #3 (gemini.md):
    O chat entre locador e locatário só é habilitado APÓS uma
    solicitação de locação (Locacao.status >= SOLICITADO).

    A sala é criada com `ativa=True`, mas o acesso efetivo ao chat
    é controlado pela propriedade `SalaChat.chat_permitido`, que
    verifica o status da locação.
    """
    if not created:
        return

    from apps.chat.models import SalaChat

    # Verificar se já existe uma sala para esta locação
    if SalaChat.objects.filter(locacao=instance).exists():
        return

    SalaChat.objects.create(
        locacao=instance,
        locador=instance.item.locador,
        locatario=instance.locatario,
    )

    logger.info(
        'SalaChat criada automaticamente para locação %s '
        '(locador=%s, locatário=%s)',
        instance.id,
        instance.item.locador_id,
        instance.locatario_id,
    )
