"""
Modelos do app de Locações.

Contém o modelo principal ``Locacao`` com FSM (Máquina de Estados Finita)
para controle do ciclo de vida de cada locação, e ``TimelineLocacao``
para registro histórico de cada transição de status.

Transições permitidas (unidirecionais):
    SOLICITADO → CAUCAO_RETIDA → ATIVO → DEVOLVIDO → CONCLUIDO
    Qualquer estado ativo → CONTESTADO
    SOLICITADO → CANCELADO (somente antes da retenção de caução)
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition


# ──────────────────────────────────────────────────────────────
# Constantes de status
# ──────────────────────────────────────────────────────────────

class StatusLocacao(models.TextChoices):
    """Possíveis status do ciclo de vida de uma locação."""

    SOLICITADO = "SOLICITADO", "Solicitado"
    CAUCAO_RETIDA = "CAUCAO_RETIDA", "Caução Retida"
    ATIVO = "ATIVO", "Ativo"
    DEVOLVIDO = "DEVOLVIDO", "Devolvido"
    CONCLUIDO = "CONCLUIDO", "Concluído"
    CONTESTADO = "CONTESTADO", "Contestado"
    CANCELADO = "CANCELADO", "Cancelado"


# Estados a partir dos quais se pode abrir contestação
_ESTADOS_CONTESTAVEIS = (
    StatusLocacao.CAUCAO_RETIDA,
    StatusLocacao.ATIVO,
    StatusLocacao.DEVOLVIDO,
)


# ──────────────────────────────────────────────────────────────
# Modelo Locação
# ──────────────────────────────────────────────────────────────

class Locacao(models.Model):
    """
    Representa uma locação (aluguel) entre locatário e locador.

    Utiliza ``django-fsm`` para garantir transições de status
    estritamente unidirecionais conforme regras de negócio.

    Regras financeiras:
        - ``valor_taxa_servico``: 10 % sobre diárias (pago pelo locatário)
        - ``valor_taxa_sucesso``: 15 % sobre valor recebido (retido do locador)
        - ``total_locatario``: diárias + taxa de serviço
        - Caução NUNCA é capturada automaticamente
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )

    # ── Relacionamentos ──────────────────────────────────────
    item = models.ForeignKey(
        "catalog.Item",
        on_delete=models.PROTECT,
        related_name="locacoes",
        verbose_name="Item",
    )
    locatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="locacoes_como_locatario",
        verbose_name="Locatário",
    )

    # ── Datas ─────────────────────────────────────────────────
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Fim")

    # ── FSM ───────────────────────────────────────────────────
    status = FSMField(
        default=StatusLocacao.SOLICITADO,
        choices=StatusLocacao.choices,
        protected=True,
        verbose_name="Status",
        db_index=True,
    )

    # ── Valores financeiros ──────────────────────────────────
    valor_diarias = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Valor Total das Diárias",
        help_text="Soma das diárias do período.",
    )
    valor_caucao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Valor da Caução",
        help_text="Valor de pré-autorização de caução (nunca capturado automaticamente).",
    )
    valor_taxa_servico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Taxa de Serviço (Locatário)",
        help_text="10 % sobre o valor das diárias, pago pelo locatário.",
    )
    valor_taxa_sucesso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Taxa de Sucesso (Locador)",
        help_text="15 % sobre o valor recebido pelo locador, retido pelo Aloogaí.",
    )
    total_locatario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Total Pago pelo Locatário",
        help_text="valor_diarias + valor_taxa_servico.",
    )

    # ── Stripe ────────────────────────────────────────────────
    payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Payment Intent ID (Diárias)",
        help_text="ID do PaymentIntent Stripe para pagamento das diárias.",
    )
    caucao_auth_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Payment Intent ID (Caução)",
        help_text="ID do PaymentIntent Stripe da pré-autorização de caução.",
    )

    # ── ESG ───────────────────────────────────────────────────
    co2_evitado = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="CO₂ Evitado (kg)",
        help_text="Estimativa de CO₂ evitado por reutilização do item.",
    )

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        verbose_name = "Locação"
        verbose_name_plural = "Locações"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="idx_locacao_status"),
            models.Index(fields=["locatario", "status"], name="idx_locacao_locat_st"),
            models.Index(fields=["data_inicio", "data_fim"], name="idx_locacao_datas"),
        ]

    def __str__(self) -> str:
        return f"Locação {self.id} — {self.item} ({self.get_status_display()})"

    # ──────────────────────────────────────────────────────────
    # Propriedades
    # ──────────────────────────────────────────────────────────

    @property
    def numero_diarias(self) -> int:
        """Retorna a quantidade de diárias (dias) da locação."""
        delta = self.data_fim - self.data_inicio
        return max(delta.days, 1)

    @property
    def locador(self):
        """Atalho para acessar o locador (dono do item)."""
        return self.item.locador

    # ──────────────────────────────────────────────────────────
    # Transições FSM
    # ──────────────────────────────────────────────────────────

    @transition(
        field=status,
        source=StatusLocacao.SOLICITADO,
        target=StatusLocacao.CAUCAO_RETIDA,
    )
    def reter_caucao(self, caucao_auth_id: str = ""):
        """
        Transição: SOLICITADO → CAUCAO_RETIDA.

        Chamada após a pré-autorização de caução ser confirmada no Stripe.
        """
        if caucao_auth_id:
            self.caucao_auth_id = caucao_auth_id

    @transition(
        field=status,
        source=StatusLocacao.CAUCAO_RETIDA,
        target=StatusLocacao.ATIVO,
    )
    def confirmar_entrega(self):
        """
        Transição: CAUCAO_RETIDA → ATIVO.

        Chamada quando o locador confirma que entregou o item ao locatário.
        """
        pass  # Lógica adicional pode ser inserida aqui

    @transition(
        field=status,
        source=StatusLocacao.ATIVO,
        target=StatusLocacao.DEVOLVIDO,
    )
    def confirmar_devolucao(self):
        """
        Transição: ATIVO → DEVOLVIDO.

        Chamada quando o locatário devolve o item ao locador.
        """
        pass

    @transition(
        field=status,
        source=StatusLocacao.DEVOLVIDO,
        target=StatusLocacao.CONCLUIDO,
    )
    def concluir(self):
        """
        Transição: DEVOLVIDO → CONCLUIDO.

        Chamada após pagamento capturado, caução liberada e
        tudo finalizado sem pendências.
        """
        pass

    @transition(
        field=status,
        source=_ESTADOS_CONTESTAVEIS,
        target=StatusLocacao.CONTESTADO,
    )
    def contestar(self, observacao: str = ""):
        """
        Transição: (CAUCAO_RETIDA | ATIVO | DEVOLVIDO) → CONTESTADO.

        Abre um processo de mediação humana. A caução só pode ser
        capturada após mediação neste estado.
        """
        pass  # A observação é registrada via TimelineLocacao

    @transition(
        field=status,
        source=StatusLocacao.SOLICITADO,
        target=StatusLocacao.CANCELADO,
    )
    def cancelar(self):
        """
        Transição: SOLICITADO → CANCELADO.

        Só é permitido ANTES da retenção de caução. Após a caução
        ser retida, o cancelamento não é possível.
        """
        pass


# ──────────────────────────────────────────────────────────────
# Modelo Timeline
# ──────────────────────────────────────────────────────────────

class TimelineLocacao(models.Model):
    """
    Registro histórico de cada transição de status de uma Locação.

    Fornece auditoria completa do ciclo de vida, incluindo
    status anterior, novo status, timestamp e observações.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    locacao = models.ForeignKey(
        Locacao,
        on_delete=models.CASCADE,
        related_name="timeline",
        verbose_name="Locação",
    )
    status_anterior = models.CharField(
        max_length=20,
        choices=StatusLocacao.choices,
        blank=True,
        default="",
        verbose_name="Status Anterior",
    )
    status_novo = models.CharField(
        max_length=20,
        choices=StatusLocacao.choices,
        verbose_name="Novo Status",
    )
    observacao = models.TextField(
        blank=True,
        default="",
        verbose_name="Observação",
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data/Hora",
    )

    class Meta:
        verbose_name = "Evento da Timeline"
        verbose_name_plural = "Eventos da Timeline"
        ordering = ["created_at"]

    def __str__(self) -> str:
        anterior = self.status_anterior or "—"
        return (
            f"[{self.created_at:%d/%m/%Y %H:%M}] "
            f"{anterior} → {self.status_novo}"
        )
