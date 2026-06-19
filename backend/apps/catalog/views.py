from apps.core.geo_compat import HAS_GIS, Point, D

if HAS_GIS:
    from django.contrib.gis.db.models.functions import Distance
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.catalog.filters import ItemFilter
from apps.catalog.models import Avaliacao, Categoria, FotoItem, Item
from apps.catalog.serializers import (
    AvaliacaoSerializer,
    CategoriaSerializer,
    FotoItemSerializer,
    ItemCreateUpdateSerializer,
    ItemDetailSerializer,
    ItemListSerializer,
)


class CategoriaListView(generics.ListAPIView):
    """
    Lista todas as categorias ativas.

    GET /api/v1/catalog/categorias/

    Endpoint público (sem autenticação) para popular
    filtros e seleção de categoria no app mobile.
    """

    queryset = Categoria.objects.filter(ativa=True)
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Categorias são poucas, sem paginação


class ItemViewSet(viewsets.ModelViewSet):
    """
    CRUD de itens e busca geoespacial por proximidade.

    GET    /api/v1/catalog/itens/              — Lista itens (GeoJSON)
    POST   /api/v1/catalog/itens/              — Cria item
    GET    /api/v1/catalog/itens/{id}/          — Detalhe do item
    PATCH  /api/v1/catalog/itens/{id}/          — Atualiza item
    DELETE /api/v1/catalog/itens/{id}/          — Remove item
    GET    /api/v1/catalog/itens/proximos/      — Busca por proximidade

    A listagem retorna GeoJSON. O detalhe retorna JSON completo.
    Busca por proximidade usa PostGIS ST_DWithin + índice GiST.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ItemFilter
    ordering_fields = ['preco_diaria', 'avaliacao_media', 'created_at']
    ordering = ['-is_destacado', '-created_at']

    def get_serializer_class(self):
        """Retorna serializer apropriado conforme a ação."""
        if self.action == 'list' or self.action == 'proximos':
            return ItemListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ItemCreateUpdateSerializer
        return ItemDetailSerializer

    def get_queryset(self):
        """
        Retorna queryset de itens visíveis.

        Para listagem pública: apenas itens ATIVOS e aprovados.
        Para o proprietário: inclui seus próprios itens em qualquer status.
        """
        queryset = Item.objects.select_related(
            'locador', 'categoria',
        ).prefetch_related('fotos')

        if self.action in ('list', 'proximos'):
            # Listagem pública: só itens visíveis no mapa
            queryset = queryset.filter(
                status='ATIVO',
                aprovado_para_uso=True,
            )
        elif self.request.user.is_authenticated and self.action == 'retrieve':
            # Detalhe: qualquer item ativo OU próprio do usuário
            from django.db.models import Q
            queryset = queryset.filter(
                Q(status='ATIVO', aprovado_para_uso=True)
                | Q(locador=self.request.user)
            )

        return queryset

    @action(detail=False, methods=['get'], url_path='proximos')
    def proximos(self, request):
        """
        Busca itens por proximidade geográfica.

        GET /api/v1/catalog/itens/proximos/?lat=-23.55&lng=-46.63&raio_km=5

        Parâmetros de query:
        - lat (obrigatório): Latitude do ponto de referência
        - lng (obrigatório): Longitude do ponto de referência
        - raio_km (opcional, default=5): Raio de busca em quilômetros
        - ordenar_por (opcional): distancia, preco, avaliacao

        Utiliza ST_DWithin com índice GiST para performance.
        Resultados ordenados por destaque + distância por padrão.
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        raio_km = request.query_params.get('raio_km', 5)
        ordenar_por = request.query_params.get('ordenar_por', 'distancia')

        if not lat or not lng:
            return Response(
                {'erro': 'Parâmetros "lat" e "lng" são obrigatórios.'},
                status=400,
            )

        try:
            lat = float(lat)
            lng = float(lng)
            raio_km = float(raio_km)
        except (ValueError, TypeError):
            return Response(
                {'erro': 'Parâmetros "lat", "lng" e "raio_km" devem ser numéricos.'},
                status=400,
            )

        # Ponto de referência (SRID 4326 / WGS84)
        ponto_ref = Point(lng, lat, srid=4326)

        try:
            # Busca por raio usando ST_DWithin + índice GiST (Falha no SQLite local)
            from django.core.exceptions import FieldError
            queryset = self.get_queryset().filter(
                localizacao__dwithin=(ponto_ref, D(km=raio_km)),
            ).annotate(
                distancia=Distance('localizacao', ponto_ref),
            )
        except FieldError:
            # Fallback para SQLite local (Dev): Retorna todos os itens
            # e anota uma distância simulada de 1km para não quebrar a UI
            from django.db.models import Value, FloatField
            queryset = self.get_queryset().annotate(
                distancia=Value(1.0, output_field=FloatField())
            )

        # Aplicar filtros do django-filter
        queryset = self.filter_queryset(queryset)

        # Ordenação
        ordenacao_map = {
            'distancia': ['distancia'],
            'preco': ['preco_diaria', 'distancia'],
            'avaliacao': ['-avaliacao_media', 'distancia'],
        }
        campos_ordem = ordenacao_map.get(ordenar_por, ['distancia'])
        queryset = queryset.order_by('-is_destacado', *campos_ordem)

        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FotoItemViewSet(viewsets.ModelViewSet):
    """
    CRUD de fotos de itens.

    GET    /api/v1/catalog/fotos/          — Lista fotos
    POST   /api/v1/catalog/fotos/          — Upload de foto
    GET    /api/v1/catalog/fotos/{id}/      — Detalhe da foto
    PATCH  /api/v1/catalog/fotos/{id}/      — Atualiza metadados
    DELETE /api/v1/catalog/fotos/{id}/      — Remove foto

    Usuário só pode gerenciar fotos de seus próprios itens.
    """

    serializer_class = FotoItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Retorna fotos de itens do usuário autenticado."""
        return FotoItem.objects.filter(
            item__locador=self.request.user,
        ).select_related('item')


class AvaliacaoViewSet(viewsets.ModelViewSet):
    """
    CRUD de avaliações de locações concluídas.

    GET    /api/v1/catalog/avaliacoes/            — Lista avaliações
    POST   /api/v1/catalog/avaliacoes/            — Cria avaliação
    GET    /api/v1/catalog/avaliacoes/{id}/        — Detalhe
    DELETE /api/v1/catalog/avaliacoes/{id}/        — Remove avaliação

    Filtragem por item via query param ?item={uuid}.
    """

    serializer_class = AvaliacaoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        """
        Retorna avaliações, opcionalmente filtradas por item.

        GET /api/v1/catalog/avaliacoes/?item={uuid}
        """
        queryset = Avaliacao.objects.select_related(
            'item', 'avaliador',
        ).order_by('-created_at')

        item_id = self.request.query_params.get('item')
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        return queryset
