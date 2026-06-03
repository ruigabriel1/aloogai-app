"""
Serializers do app de Locações.

Fornece serializers para criação, listagem e detalhamento de locações,
incluindo cálculo automático de valores financeiros e validação de datas.
"""
from datetime import date

from rest_framework import serializers

from apps.rentals.models import Locacao, StatusLocacao, TimelineLocacao
from apps.rentals.services import LocacaoService


class TimelineLocacaoSerializer(serializers.ModelSerializer):
    """Serializer para eventos da timeline de uma locação."""

    class Meta:
        model = TimelineLocacao
        fields = [
            "id",
            "status_anterior",
            "status_novo",
            "observacao",
            "created_at",
        ]
        read_only_fields = fields


class LocacaoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novas locações.

    Responsabilidades:
        - Validar datas (não passado, fim >= início, máx 30 dias)
        - Verificar disponibilidade do item
        - Calcular valores financeiros automaticamente
        - Aceitar ``payment_method_id`` para integração Stripe

    O locatário é inferido do request (usuário autenticado).
    """

    payment_method_id = serializers.CharField(
        write_only=True,
        required=True,
        help_text="ID do método de pagamento Stripe (pm_xxx).",
    )

    class Meta:
        model = Locacao
        fields = [
            "item",
            "data_inicio",
            "data_fim",
            "payment_method_id",
        ]

    def validate(self, attrs: dict) -> dict:
        """
        Validações cruzadas de datas e disponibilidade.

        Calcula automaticamente os valores financeiros com base
        no preço da diária e caução do item.
        """
        data_inicio = attrs["data_inicio"]
        data_fim = attrs["data_fim"]
        item = attrs["item"]

        # Validar datas
        erros_datas = LocacaoService.validar_datas(data_inicio, data_fim)
        if erros_datas:
            raise serializers.ValidationError({"datas": erros_datas})

        # Validar que locatário não é o próprio locador
        request = self.context.get("request")
        if request and request.user == item.locador:
            raise serializers.ValidationError(
                {"item": "Você não pode alugar seu próprio item."}
            )

        # Verificar disponibilidade
        disponivel = LocacaoService.verificar_disponibilidade(
            item_id=str(item.id),
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        if not disponivel:
            raise serializers.ValidationError(
                {"item": "Este item não está disponível no período selecionado."}
            )

        # Calcular valores financeiros
        valores = LocacaoService.calcular_valores(
            preco_diaria=item.preco_diaria,
            data_inicio=data_inicio,
            data_fim=data_fim,
            valor_caucao=item.valor_caucao,
        )
        attrs.update(valores)

        return attrs

    def create(self, validated_data: dict) -> Locacao:
        """
        Cria a locação com o locatário do request e valores calculados.

        O ``payment_method_id`` é consumido aqui para iniciar o
        fluxo de pagamento (implementação completa no PaymentsService).
        """
        # Remover campos não-modelo
        validated_data.pop("payment_method_id", None)
        validated_data.pop("numero_diarias", None)

        # Definir locatário
        validated_data["locatario"] = self.context["request"].user

        return super().create(validated_data)


class LocacaoListSerializer(serializers.ModelSerializer):
    """
    Serializer compacto para listagem de locações.

    Inclui informações resumidas do item e status formatado.
    """

    item_titulo = serializers.CharField(
        source="item.titulo",
        read_only=True,
    )
    locador_nome = serializers.CharField(
        source="item.locador.get_full_name",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Locacao
        fields = [
            "id",
            "item",
            "item_titulo",
            "locador_nome",
            "status",
            "status_display",
            "data_inicio",
            "data_fim",
            "total_locatario",
            "created_at",
        ]
        read_only_fields = fields


class LocacaoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalhamento de uma locação.

    Inclui timeline completa, todos os valores financeiros
    e dados do item e participantes.
    """

    item_titulo = serializers.CharField(
        source="item.titulo",
        read_only=True,
    )
    locador_nome = serializers.CharField(
        source="item.locador.get_full_name",
        read_only=True,
    )
    locatario_nome = serializers.CharField(
        source="locatario.get_full_name",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    numero_diarias = serializers.IntegerField(read_only=True)
    timeline = TimelineLocacaoSerializer(many=True, read_only=True)

    class Meta:
        model = Locacao
        fields = [
            "id",
            "item",
            "item_titulo",
            "locatario",
            "locatario_nome",
            "locador_nome",
            "status",
            "status_display",
            "data_inicio",
            "data_fim",
            "numero_diarias",
            "valor_diarias",
            "valor_caucao",
            "valor_taxa_servico",
            "valor_taxa_sucesso",
            "total_locatario",
            "payment_intent_id",
            "caucao_auth_id",
            "co2_evitado",
            "timeline",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TransicaoSerializer(serializers.Serializer):
    """
    Serializer para ações de transição de status.

    Permite envio opcional de observação para registro na timeline.
    """

    observacao = serializers.CharField(
        required=False,
        default="",
        help_text="Observação opcional sobre a transição.",
    )
