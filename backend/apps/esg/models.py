"""
Modelos do app de ESG e Sustentabilidade do Aloogaí.

Implementa o sistema de cálculo de CO₂ economizado por locação,
histórico ESG do usuário, e gamificação com selos ecológicos.
"""

import uuid

from django.db import models


class FatorESGCategoria(models.Model):
    """
    Fator de referência de CO₂ por categoria de item.

    Armazena os parâmetros usados para calcular o CO₂ economizado
    quando um item de determinada categoria é alugado ao invés de
    ser comprado novo.

    Fórmula: co2 = co2_fabricacao_kg * fator_reuso + reducao_frete_kg
    """

    class Meta:
        verbose_name = "Fator ESG por Categoria"
        verbose_name_plural = "Fatores ESG por Categoria"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    categoria = models.OneToOneField(
        "catalog.Categoria",
        on_delete=models.CASCADE,
        related_name="fator_esg",
        verbose_name="Categoria",
        help_text="Categoria de item associada a este fator ESG.",
    )
    co2_fabricacao_kg = models.FloatField(
        verbose_name="CO₂ de Fabricação (kg)",
        help_text=(
            "Estimativa de CO₂ (em kg) emitido na fabricação de um item "
            "novo desta categoria."
        ),
    )
    fator_reuso = models.FloatField(
        default=0.7,
        verbose_name="Fator de Reuso",
        help_text=(
            "Multiplicador de reuso (0 a 1). Representa a fração do CO₂ "
            "de fabricação que é economizada ao reutilizar o item. "
            "Padrão: 0.7 (70%%)."
        ),
    )
    reducao_frete_kg = models.FloatField(
        default=0.0,
        verbose_name="Redução de Frete (kg CO₂)",
        help_text=(
            "CO₂ (em kg) economizado pela redução logística ao alugar "
            "localmente vs comprar online com entrega."
        ),
    )

    def calcular_co2(self):
        """
        Calcula o CO₂ economizado por uma locação desta categoria.

        Retorna:
            float: CO₂ economizado em kg.
        """
        return (self.co2_fabricacao_kg * self.fator_reuso) + self.reducao_frete_kg

    def __str__(self):
        return f"Fator ESG — {self.categoria}"


class HistoricoESG(models.Model):
    """
    Registro histórico de cálculos de CO₂ economizado.

    Cada locação concluída gera um registro com o CO₂ economizado
    e a evolução do score ESG do usuário (antes e depois).
    """

    class Meta:
        verbose_name = "Histórico ESG"
        verbose_name_plural = "Históricos ESG"
        ordering = ["-created_at"]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    usuario = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="historico_esg",
        verbose_name="Usuário",
    )
    locacao = models.OneToOneField(
        "rentals.Locacao",
        on_delete=models.CASCADE,
        related_name="historico_esg",
        verbose_name="Locação",
        help_text="Locação que gerou este cálculo de CO₂.",
    )
    co2_economizado = models.FloatField(
        verbose_name="CO₂ Economizado (kg)",
        help_text="Quantidade de CO₂ economizado nesta locação específica.",
    )
    score_anterior = models.FloatField(
        verbose_name="Score Anterior",
        help_text="Score ESG do usuário antes desta locação.",
    )
    score_novo = models.FloatField(
        verbose_name="Score Novo",
        help_text="Score ESG do usuário após esta locação.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    def __str__(self):
        return (
            f"ESG — {self.usuario} | "
            f"+{self.co2_economizado:.2f}kg CO₂ | "
            f"Score: {self.score_anterior:.1f} → {self.score_novo:.1f}"
        )


class SeloESG(models.Model):
    """
    Selo (badge/conquista) ecológico do sistema de gamificação ESG.

    Os selos incentivam locações recorrentes e sustentabilidade,
    sendo desbloqueados quando o usuário atinge requisitos de
    quantidade de locações ou score ESG.
    """

    class Meta:
        verbose_name = "Selo ESG"
        verbose_name_plural = "Selos ESG"
        ordering = ["requisito_locacoes", "requisito_score"]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome",
        help_text="Nome do selo ecológico.",
    )
    descricao = models.TextField(
        verbose_name="Descrição",
        help_text="Descrição do selo e como desbloqueá-lo.",
    )
    icone = models.CharField(
        max_length=100,
        verbose_name="Ícone",
        help_text="Identificador do ícone do selo (emoji ou nome do asset).",
    )
    requisito_locacoes = models.IntegerField(
        default=0,
        verbose_name="Requisito de Locações",
        help_text="Número mínimo de locações concluídas para desbloquear.",
    )
    requisito_score = models.FloatField(
        default=0.0,
        verbose_name="Requisito de Score ESG",
        help_text="Score ESG mínimo para desbloquear o selo.",
    )

    def __str__(self):
        return f"{self.icone} {self.nome}"


class UsuarioSelo(models.Model):
    """
    Tabela associativa (M2M through) entre Usuário e Selo ESG.

    Registra quando um usuário desbloqueia um selo ecológico,
    incluindo o timestamp do desbloqueio.
    """

    class Meta:
        verbose_name = "Selo do Usuário"
        verbose_name_plural = "Selos dos Usuários"
        unique_together = ("usuario", "selo")
        ordering = ["-desbloqueado_em"]

    usuario = models.ForeignKey(
        "users.Usuario",
        on_delete=models.CASCADE,
        related_name="selos_desbloqueados",
        verbose_name="Usuário",
    )
    selo = models.ForeignKey(
        SeloESG,
        on_delete=models.CASCADE,
        related_name="usuarios",
        verbose_name="Selo",
    )
    desbloqueado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Desbloqueado em",
    )

    def __str__(self):
        return f"{self.usuario} — {self.selo.nome}"
