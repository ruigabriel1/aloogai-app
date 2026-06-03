"""
Modelos do app de Pagamentos.

Contém ``ContaConectada`` para dados da conta Stripe Connect do
locador e ``TransacaoStripe`` para registro de cada operação
financeira realizada via Stripe.
"""
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal


# ──────────────────────────────────────────────────────────────
# Conta Conectada (Stripe Connect)
# ──────────────────────────────────────────────────────────────

class StatusOnboarding(models.TextChoices):
    """Status do processo de onboarding Stripe Connect."""

    PENDENTE = "PENDENTE", "Pendente"
    EM_ANALISE = "EM_ANALISE", "Em Análise"
    COMPLETO = "COMPLETO", "Completo"
    ATIVO = "ATIVO", "Ativo"
    RESTRITO = "RESTRITO", "Restrito"
    DESATIVADO = "DESATIVADO", "Desativado"


class TipoConta(models.TextChoices):
    """Tipos de conta Stripe Connect suportados."""

    STANDARD = "STANDARD", "Standard"
    EXPRESS = "EXPRESS", "Express"


class ContaConectada(models.Model):
    """
    Informações da conta Stripe Connect vinculada a um usuário (locador).

    Cada locador que deseja receber pagamentos precisa ter uma conta
    conectada via Stripe Connect. O onboarding é gerenciado pelo
    próprio Stripe.

    Campos:
        usuario: Relacionamento 1:1 com o modelo de Usuário.
        stripe_account_id: ID da conta no Stripe (acct_xxx).
        tipo_conta: STANDARD ou EXPRESS.
        status_onboarding: Estado atual do onboarding.
        created_at: Data de criação do registro.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conta_conectada",
        verbose_name="Usuário",
    )
    stripe_account_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Stripe Account ID",
        help_text="ID da conta conectada no Stripe (acct_xxx).",
    )
    tipo_conta = models.CharField(
        max_length=10,
        choices=TipoConta.choices,
        default=TipoConta.EXPRESS,
        verbose_name="Tipo de Conta",
    )
    status_onboarding = models.CharField(
        max_length=15,
        choices=StatusOnboarding.choices,
        default=StatusOnboarding.PENDENTE,
        verbose_name="Status do Onboarding",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        verbose_name = "Conta Conectada"
        verbose_name_plural = "Contas Conectadas"

    def __str__(self) -> str:
        return f"{self.usuario} — {self.stripe_account_id} ({self.get_status_onboarding_display()})"

    @property
    def esta_ativa(self) -> bool:
        """Retorna True se a conta está ativa e pode receber pagamentos."""
        return self.status_onboarding == StatusOnboarding.ATIVO


# ──────────────────────────────────────────────────────────────
# Transação Stripe
# ──────────────────────────────────────────────────────────────

class TipoTransacao(models.TextChoices):
    """Tipos de transação financeira via Stripe."""

    PRE_AUTH = "PRE_AUTH", "Pré-Autorização (Diárias)"
    CAPTURA = "CAPTURA", "Captura (Diárias)"
    ESTORNO = "ESTORNO", "Estorno"
    CAUCAO_PRE_AUTH = "CAUCAO_PRE_AUTH", "Pré-Autorização (Caução)"
    CAUCAO_CAPTURA = "CAUCAO_CAPTURA", "Captura de Caução"
    CAUCAO_LIBERADA = "CAUCAO_LIBERADA", "Caução Liberada"


class StatusTransacao(models.TextChoices):
    """Status da transação no Stripe."""

    PENDENTE = "PENDENTE", "Pendente"
    SUCESSO = "SUCESSO", "Sucesso"
    FALHA = "FALHA", "Falha"


class TransacaoStripe(models.Model):
    """
    Registro de cada transação financeira realizada via Stripe.

    Mantém rastreabilidade completa de todas as operações
    financeiras associadas a uma locação, incluindo:
        - Pré-autorizações de diárias e caução
        - Capturas de pagamento
        - Estornos
        - Liberações de caução

    A caução NUNCA é capturada automaticamente. Só pode ser
    capturada em caso de CONTESTADO com mediação humana.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    locacao = models.ForeignKey(
        "rentals.Locacao",
        on_delete=models.PROTECT,
        related_name="transacoes",
        verbose_name="Locação",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoTransacao.choices,
        verbose_name="Tipo de Transação",
        db_index=True,
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Stripe Payment Intent ID",
        help_text="ID do PaymentIntent associado (pi_xxx).",
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Valor (R$)",
    )
    status = models.CharField(
        max_length=10,
        choices=StatusTransacao.choices,
        default=StatusTransacao.PENDENTE,
        verbose_name="Status",
        db_index=True,
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadados",
        help_text="Dados adicionais retornados pelo Stripe.",
    )
    erro_mensagem = models.TextField(
        blank=True,
        default="",
        verbose_name="Mensagem de Erro",
        help_text="Detalhes do erro em caso de falha.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    class Meta:
        verbose_name = "Transação Stripe"
        verbose_name_plural = "Transações Stripe"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["locacao", "tipo"], name="idx_trans_locacao_tipo"),
            models.Index(
                fields=["stripe_payment_intent_id"],
                name="idx_trans_stripe_pi",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.get_tipo_display()} — R$ {self.valor} "
            f"({self.get_status_display()})"
        )
