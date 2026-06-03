"""
Signals do app de Locações.

Registra automaticamente cada transição de status no modelo
``TimelineLocacao`` para auditoria completa do ciclo de vida.
"""
import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.rentals.models import Locacao, TimelineLocacao

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Locacao)
def registrar_mudanca_status(sender, instance: Locacao, **kwargs):
    """
    Cria um registro na timeline sempre que o status de uma Locação muda.

    Funciona no ``pre_save`` para capturar o status anterior antes
    de ser sobrescrito. O ``TimelineLocacao`` é salvo diretamente
    (sem depender do save principal) para garantir o registro.

    Nota:
        Na criação (instance.pk novo), registra a entrada inicial
        com status_anterior vazio.
    """
    if not instance.pk:
        # Locação sendo criada — registrar no post_save seria ideal,
        # mas como usamos pre_save, o registro de criação é feito
        # via signal separado abaixo.
        return

    try:
        locacao_anterior = Locacao.objects.get(pk=instance.pk)
    except Locacao.DoesNotExist:
        return

    if locacao_anterior.status != instance.status:
        TimelineLocacao.objects.create(
            locacao=instance,
            status_anterior=locacao_anterior.status,
            status_novo=instance.status,
            observacao=f"Transição automática: {locacao_anterior.status} → {instance.status}",
        )
        logger.info(
            "Locação %s: %s → %s",
            instance.pk,
            locacao_anterior.status,
            instance.status,
        )


@receiver(pre_save, sender=Locacao)
def registrar_criacao_locacao(sender, instance: Locacao, **kwargs):
    """
    Registra a entrada inicial na timeline quando a Locação é criada.

    Usa ``_is_new`` flag para detectar criação, já que o ``pre_save``
    é chamado antes do ``pk`` ser atribuído em auto-generated IDs.
    Para UUIDs (default gerado no Python), o pk já existe no pre_save.
    """
    # UUID é gerado no Python, então pk já existe mesmo em criação.
    # Verificamos se já existe no banco.
    if instance.pk and not Locacao.objects.filter(pk=instance.pk).exists():
        # Marcar para criar timeline no post_save
        instance._registrar_timeline_criacao = True


from django.db.models.signals import post_save  # noqa: E402


@receiver(post_save, sender=Locacao)
def registrar_timeline_criacao_post_save(sender, instance: Locacao, created: bool, **kwargs):
    """
    Cria o primeiro registro de timeline após a criação da Locação.
    """
    if created or getattr(instance, "_registrar_timeline_criacao", False):
        TimelineLocacao.objects.create(
            locacao=instance,
            status_anterior="",
            status_novo=instance.status,
            observacao="Locação criada.",
        )
        # Limpar flag
        if hasattr(instance, "_registrar_timeline_criacao"):
            del instance._registrar_timeline_criacao
        logger.info("Locação %s criada com status %s", instance.pk, instance.status)
