from rest_framework import serializers

from apps.core.geo_compat import coordenadas
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

    def validate_item(self, item: Item) -> Item:
        """Só o dono do item pode adicionar fotos a ele."""
        if item.locador_id != self.context['request'].user.id:
            raise serializers.ValidationError('Você só pode adicionar fotos aos seus itens.')
        return item


class CoordenadasMixin(serializers.Serializer):
    """Expõe a localização como latitude/longitude, com ou sem PostGIS."""

    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    def get_latitude(self, obj: Item) -> float | None:
        return coordenadas(obj.localizacao)[0]

    def get_longitude(self, obj: Item) -> float | None:
        return coordenadas(obj.localizacao)[1]


def url_foto_capa(obj: Item, request) -> str | None:
    """URL absoluta da foto de capa (ou da primeira foto, se nenhuma for capa)."""
    fotos = list(obj.fotos.all())  # usa o prefetch da view
    foto = next((f for f in fotos if f.is_capa), None) or (fotos[0] if fotos else None)
    if not foto or not foto.imagem:
        return None
    return request.build_absolute_uri(foto.imagem.url) if request else foto.imagem.url


class ItemListSerializer(CoordenadasMixin, serializers.ModelSerializer):
    """
    Item resumido para o feed e o mapa.

    JSON comum (não GeoJSON), igual com e sem PostGIS, para o app ler um formato só.
    """

    locador = UsuarioResumoSerializer(read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    categoria_icone = serializers.CharField(source='categoria.icone', read_only=True)
    foto_capa_url = serializers.SerializerMethodField()
    distancia_km = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id',
            'titulo',
            'descricao',
            'camada',
            'status',
            'aprovado_para_uso',
            'categoria',
            'categoria_nome',
            'categoria_icone',
            'preco_diaria',
            'valor_caucao',
            'is_destacado',
            'avaliacao_media',
            'total_avaliacoes',
            'foto_capa_url',
            'distancia_km',
            'latitude',
            'longitude',
            'locador',
        ]

    def get_foto_capa_url(self, obj: Item) -> str | None:
        return url_foto_capa(obj, self.context.get('request'))

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


class ItemDetailSerializer(CoordenadasMixin, serializers.ModelSerializer):
    """
    Serializer detalhado para página do item.

    Inclui todas as informações do item, fotos, locador
    e avaliações recentes.
    """

    locador = UsuarioResumoSerializer(read_only=True)
    fotos = FotoItemSerializer(many=True, read_only=True)
    foto_capa_url = serializers.SerializerMethodField()
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
            'latitude',
            'longitude',
            'foto_capa_url',
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

    def get_foto_capa_url(self, obj: Item) -> str | None:
        return url_foto_capa(obj, self.context.get('request'))


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de itens.

    Aceita latitude/longitude separados e converte para PointField.
    O locador é automaticamente vinculado ao usuário autenticado.
    """

    latitude = serializers.FloatField(write_only=True, required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(write_only=True, required=True, min_value=-180, max_value=180)
    # O dono controla a publicação: nasce ATIVO (itens PRO ainda dependem de aprovação do admin).
    status = serializers.ChoiceField(
        choices=[('RASCUNHO', 'Rascunho'), ('ATIVO', 'Ativo'), ('PAUSADO', 'Pausado')],
        default='ATIVO',
    )

    class Meta:
        model = Item
        fields = [
            'id',
            'titulo',
            'descricao',
            'categoria',
            'status',
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
        # O item vem da própria locação: não dá para avaliar um item que não foi alugado.
        read_only_fields = ['id', 'item', 'avaliador', 'avaliador_nome', 'created_at']

    def validate_nota(self, value: int) -> int:
        """Valida que a nota está entre 1 e 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                'A nota deve ser entre 1 e 5.'
            )
        return value

    def validate_locacao(self, locacao):
        """Só o locatário avalia, e só depois que a locação foi concluída."""
        usuario = self.context['request'].user
        if locacao.locatario_id != usuario.id:
            raise serializers.ValidationError('Só o locatário pode avaliar esta locação.')
        if locacao.status != 'CONCLUIDO':
            raise serializers.ValidationError('Só é possível avaliar locações concluídas.')
        if Avaliacao.objects.filter(locacao=locacao).exists():
            raise serializers.ValidationError('Esta locação já foi avaliada.')
        return locacao

    def create(self, validated_data: dict) -> Avaliacao:
        """Cria avaliação vinculada ao usuário autenticado e atualiza a média do item."""
        validated_data['avaliador'] = self.context['request'].user
        validated_data['item'] = validated_data['locacao'].item
        avaliacao = super().create(validated_data)
        avaliacao.item.recalcular_avaliacoes()
        return avaliacao
