import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.models import DocumentoKYC, Endereco, Usuario


class UsuarioRegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de novo usuário.

    Valida formato de CPF/CNPJ, força senha segura e
    cria o usuário com os campos obrigatórios do Aloogaí.
    """

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Senha do usuário (mínimo 8 caracteres).',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmação da senha.',
    )

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'tipo_usuario',
            'cpf_cnpj',
            'telefone',
            'foto_perfil',
        ]
        read_only_fields = ['id']

    def validate_cpf_cnpj(self, value: str) -> str:
        """
        Valida o formato do CPF ou CNPJ.

        Aceita formatos:
        - CPF: 123.456.789-00 ou 12345678900
        - CNPJ: 12.345.678/0001-00 ou 12345678000100
        """
        # Remove formatação para validar
        numeros = re.sub(r'[.\-/]', '', value)

        if len(numeros) == 11:
            # Formato CPF
            if not re.match(r'^\d{11}$', numeros):
                raise serializers.ValidationError(
                    'CPF deve conter exatamente 11 dígitos numéricos.'
                )
        elif len(numeros) == 14:
            # Formato CNPJ
            if not re.match(r'^\d{14}$', numeros):
                raise serializers.ValidationError(
                    'CNPJ deve conter exatamente 14 dígitos numéricos.'
                )
        else:
            raise serializers.ValidationError(
                'CPF deve ter 11 dígitos e CNPJ deve ter 14 dígitos.'
            )

        return value

    def validate(self, attrs: dict) -> dict:
        """Valida que as senhas coincidem."""
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': 'As senhas não coincidem.'}
            )
        return attrs

    def create(self, validated_data: dict) -> Usuario:
        """Cria o usuário com senha hasheada."""
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para visualização e atualização do perfil do usuário.

    Inclui campo computado `is_locador_ativo` e campos somente-leitura
    para dados gerenciados pelo sistema (KYC, ESG, Stripe).
    """

    is_locador_ativo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'tipo_usuario',
            'cpf_cnpj',
            'telefone',
            'foto_perfil',
            'kyc_status',
            'score_esg',
            'stripe_onboarding_complete',
            'is_locador_ativo',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'cpf_cnpj',
            'kyc_status',
            'score_esg',
            'stripe_onboarding_complete',
            'is_locador_ativo',
            'created_at',
            'updated_at',
        ]


class UsuarioResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumido do usuário para exibição pública.

    Usado em listagens de itens no mapa, avaliações, etc.
    Expõe apenas dados públicos sem informações sensíveis.
    """

    class Meta:
        model = Usuario
        fields = [
            'id',
            'first_name',
            'foto_perfil',
            'score_esg',
            'tipo_usuario',
        ]
        read_only_fields = fields


class EnderecoSerializer(serializers.ModelSerializer):
    """
    Serializer para endereços do usuário.

    Trata a geolocalização como par latitude/longitude separados
    para facilitar consumo pelo frontend mobile.
    """

    latitude = serializers.FloatField(write_only=True, required=True)
    longitude = serializers.FloatField(write_only=True, required=True)

    class Meta:
        model = Endereco
        fields = [
            'id',
            'apelido',
            'logradouro',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'estado',
            'cep',
            'latitude',
            'longitude',
            'localizacao',
            'is_principal',
            'created_at',
        ]
        read_only_fields = ['id', 'localizacao', 'created_at']

    def create(self, validated_data: dict) -> Endereco:
        """Cria endereço convertendo lat/lng para PointField."""
        from apps.core.geo_compat import Point

        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['localizacao'] = Point(longitude, latitude, srid=4326)
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance: Endereco, validated_data: dict) -> Endereco:
        """Atualiza endereço convertendo lat/lng para PointField se fornecidos."""
        from apps.core.geo_compat import Point

        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['localizacao'] = Point(longitude, latitude, srid=4326)
        return super().update(instance, validated_data)


class DocumentoKYCSerializer(serializers.ModelSerializer):
    """
    Serializer para documentos de verificação KYC.

    Campos de análise (status, motivo_rejeicao, analisado_por) são
    somente-leitura — gerenciados exclusivamente pelo admin.
    """

    class Meta:
        model = DocumentoKYC
        fields = [
            'id',
            'tipo_documento',
            'arquivo',
            'status',
            'motivo_rejeicao',
            'analisado_por',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'motivo_rejeicao',
            'analisado_por',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data: dict) -> DocumentoKYC:
        """Cria documento KYC vinculado ao usuário autenticado."""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)
