from rest_framework import serializers

from apps.core.geo_compat import HAS_GIS

if HAS_GIS:
    from rest_framework_gis.serializers import GeoFeatureModelSerializer
else:
    # Fallback: usar ModelSerializer quando GIS não disponível
    GeoFeatureModelSerializer = serializers.ModelSerializer

from apps.catalog.models import Avaliacao, Categoria, FotoItem, Item
from apps.users.serializers import UsuarioResumoSerializer


class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializer para categorias de itens.

    Usado tanto na listagem para o filtro do app quanto
    na seleção durante criação de um item.
    """

    class Meta:
        model = Categoria
        fields = [
            'id',
            'nome',
            'slug',
            'descricao',
            'icone',
            'ordem',
        ]
        read_only_fields = ['id', 'slug']


class FotoItemSerializer(serializers.ModelSerializer):
    """
    Serializer para fotos de itens.

    Suporta upload de múltiplas fotos com ordenação
    e marcação de foto de capa.
    """

    class Meta:
        model = FotoItem
        fields = [
            'id',
            'item',
            'imagem',
            'is_capa',
            'ordem',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ItemListSerializer(GeoFeatureModelSerializer):
    """
    Serializer GeoJSON para listagem de itens no mapa.

    Retorna itens no formato GeoJSON Feature conforme
    especificado em gemini.md §3.2 (Saída: Item no Mapa).

    Inclui dados resumidos do locador e foto de capa.
    """

    locador = UsuarioResumoSerializer(read_only=True)
    foto_capa_url = serializers.SerializerMethodField()
    distancia_km = serializers.SerializerMethodField()

    class Meta:
        model = Item
        geo_field = 'localizacao'
        fields = [
            'id',
            'titulo',
            'camada',
            'preco_diaria',
            'valor_caucao',
            'is_destacado',
            'avaliacao_media',
            'foto_capa_url',
            'distancia_km',
            'locador',
        ]

    def get_foto_capa_url(self, obj: Item) -> str | None:
        """Retorna URL da foto de capa do item."""
        foto_capa = obj.fotos.filter(is_capa=True).first()
        if foto_capa and foto_capa.imagem:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(foto_capa.imagem.url)
            return foto_capa.imagem.url
        return None

    def get_distancia_km(self, obj: Item) -> float | None:
        """
        Retorna a distância do item em km.

        Disponível apenas quando a queryset foi anotada com
        o campo 'distancia' via ST_DWithin/Distance.
        """
        if hasattr(obj, 'distancia'):
            # Em PostGIS real, obj.distancia é um objeto Distance com .km
            if hasattr(obj.distancia, 'km'):
                return round(obj.distancia.km, 2)
            # Em SQLite (geo_compat), obj.distancia já é um número (float)
            elif isinstance(obj.distancia, (float, int)):
                return round(float(obj.distancia), 2)
        return None


class ItemDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detalhado para página do item.

    Inclui todas as informações do item, fotos, locador
    e avaliações recentes.
    """

    locador = UsuarioResumoSerializer(read_only=True)
    fotos = FotoItemSerializer(many=True, read_only=True)
    categoria_nome = serializers.CharField(
        source='categoria.nome',
        read_only=True,
    )
    visivel_no_mapa = serializers.BooleanField(read_only=True)

    class Meta:
        model = Item
        fields = [
            'id',
            'titulo',
            'descricao',
            'camada',
            'status',
            'preco_diaria',
            'valor_caucao',
            'localizacao',
            'endereco_texto',
            'requer_licenca',
            'aprovado_para_uso',
            'is_destacado',
            'avaliacao_media',
            'total_avaliacoes',
            'total_locacoes',
            'categoria',
            'categoria_nome',
            'locador',
            'fotos',
            'visivel_no_mapa',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'aprovado_para_uso',
            'avaliacao_media',
            'total_avaliacoes',
            'total_locacoes',
            'visivel_no_mapa',
            'created_at',
            'updated_at',
        ]


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de itens.

    Aceita latitude/longitude separados e converte para PointField.
    O locador é automaticamente vinculado ao usuário autenticado.
    """

    latitude = serializers.FloatField(write_only=True, required=True)
    longitude = serializers.FloatField(write_only=True, required=True)

    class Meta:
        model = Item
        fields = [
            'id',
            'titulo',
            'descricao',
            'categoria',
            'camada',
            'preco_diaria',
            'valor_caucao',
            'latitude',
            'longitude',
            'endereco_texto',
            'requer_licenca',
            'documento_licenca',
        ]
        read_only_fields = ['id']

    def validate_preco_diaria(self, value):
        """Valida que o preço da diária é positivo."""
        if value <= 0:
            raise serializers.ValidationError(
                'O preço da diária deve ser maior que zero.'
            )
        return value

    def validate_valor_caucao(self, value):
        """Valida que o valor da caução é positivo."""
        if value <= 0:
            raise serializers.ValidationError(
                'O valor da caução deve ser maior que zero.'
            )
        return value

    def create(self, validated_data: dict) -> Item:
        """Cria item com geolocalização e vincula ao locador autenticado."""
        from apps.core.geo_compat import Point

        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['localizacao'] = Point(longitude, latitude, srid=4326)
        validated_data['locador'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance: Item, validated_data: dict) -> Item:
        """Atualiza item, convertendo lat/lng se fornecidos."""
        from apps.core.geo_compat import Point

        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['localizacao'] = Point(longitude, latitude, srid=4326)
        return super().update(instance, validated_data)


class AvaliacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para avaliações de locações concluídas.

    A nota deve ser entre 1 e 5. Cada locação só pode
    ter uma avaliação (garantido pelo unique_together).
    """

    avaliador_nome = serializers.CharField(
        source='avaliador.get_full_name',
        read_only=True,
    )

    class Meta:
        model = Avaliacao
        fields = [
            'id',
            'item',
            'avaliador',
            'avaliador_nome',
            'locacao',
            'nota',
            'comentario',
            'created_at',
        ]
        read_only_fields = ['id', 'avaliador', 'avaliador_nome', 'created_at']

    def validate_nota(self, value: int) -> int:
        """Valida que a nota está entre 1 e 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                'A nota deve ser entre 1 e 5.'
            )
        return value

    def create(self, validated_data: dict) -> Avaliacao:
        """Cria avaliação vinculada ao usuário autenticado."""
        validated_data['avaliador'] = self.context['request'].user
        return super().create(validated_data)
