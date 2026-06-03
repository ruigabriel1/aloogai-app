"""
Serializers do app de Chat do Aloogaí.

Serializa salas de chat e mensagens para a API REST,
incluindo validações de acesso e criação.
"""

from rest_framework import serializers

from apps.chat.models import Mensagem, SalaChat


class SalaChatSerializer(serializers.ModelSerializer):
    """
    Serializer para leitura de salas de chat.

    Inclui o flag de chat_permitido para o frontend saber
    se pode habilitar o input de mensagens.
    """

    chat_permitido = serializers.BooleanField(read_only=True)
    total_mensagens = serializers.SerializerMethodField()
    ultima_mensagem = serializers.SerializerMethodField()

    class Meta:
        model = SalaChat
        fields = (
            "id",
            "locacao",
            "locador",
            "locatario",
            "ativa",
            "chat_permitido",
            "total_mensagens",
            "ultima_mensagem",
            "created_at",
        )
        read_only_fields = fields

    def get_total_mensagens(self, obj):
        """Retorna o total de mensagens na sala."""
        return obj.mensagens.count()

    def get_ultima_mensagem(self, obj):
        """Retorna um resumo da última mensagem da sala."""
        ultima = obj.mensagens.order_by("-created_at").first()
        if ultima:
            return {
                "id": str(ultima.id),
                "remetente": str(ultima.remetente_id),
                "tipo": ultima.tipo,
                "created_at": ultima.created_at.isoformat(),
            }
        return None


class MensagemSerializer(serializers.ModelSerializer):
    """
    Serializer para leitura de mensagens.

    Inclui o conteúdo descriptografado (a descriptografia acontece
    automaticamente no campo CampoEncriptado do modelo).
    """

    class Meta:
        model = Mensagem
        fields = (
            "id",
            "sala",
            "remetente",
            "conteudo",
            "tipo",
            "lida_em",
            "created_at",
        )
        read_only_fields = fields


class MensagemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novas mensagens.

    Valida que o remetente pertence à sala e que o chat está
    permitido com base no status da locação.
    """

    class Meta:
        model = Mensagem
        fields = (
            "id",
            "sala",
            "conteudo",
            "tipo",
        )
        read_only_fields = ("id",)

    def validate_sala(self, sala):
        """
        Valida que o chat está permitido na sala.

        Raises:
            ValidationError: Se o chat não está habilitado para a locação.
        """
        if not sala.chat_permitido:
            raise serializers.ValidationError(
                "O chat não está habilitado para esta locação. "
                "O chat só é acessível após uma solicitação de locação."
            )
        return sala

    def validate(self, attrs):
        """
        Valida que o remetente pertence à sala de chat.

        Raises:
            ValidationError: Se o usuário não é participante da sala.
        """
        request = self.context.get("request")
        sala = attrs.get("sala")

        if request and sala:
            if not sala.usuario_pertence(request.user):
                raise serializers.ValidationError(
                    {"sala": "Você não é participante desta sala de chat."}
                )

        return attrs

    def create(self, validated_data):
        """Cria a mensagem atribuindo o remetente do request."""
        request = self.context.get("request")
        validated_data["remetente"] = request.user
        return super().create(validated_data)
