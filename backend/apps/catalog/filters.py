import django_filters
from django.db import models

from apps.catalog.models import Item


class ItemFilter(django_filters.FilterSet):
    """
    Filtros para busca de itens no catálogo.

    Suporta filtragem por:
    - camada: ESSENTIAL, PRO, B2B
    - categoria: UUID da categoria
    - preco_max: preço máximo da diária
    - preco_min: preço mínimo da diária
    - status: RASCUNHO, ATIVO, PAUSADO, INATIVO
    - is_destacado: itens impulsionados
    - avaliacao_min: nota mínima
    - busca: texto livre no título e descrição
    """

    preco_min = django_filters.NumberFilter(
        field_name='preco_diaria',
        lookup_expr='gte',
        label='Preço mínimo da diária',
    )
    preco_max = django_filters.NumberFilter(
        field_name='preco_diaria',
        lookup_expr='lte',
        label='Preço máximo da diária',
    )
    avaliacao_min = django_filters.NumberFilter(
        field_name='avaliacao_media',
        lookup_expr='gte',
        label='Avaliação mínima',
    )
    busca = django_filters.CharFilter(
        method='filtrar_por_texto',
        label='Busca por texto',
    )
    categoria = django_filters.UUIDFilter(
        field_name='categoria__id',
        label='ID da categoria',
    )

    class Meta:
        model = Item
        fields = [
            'camada',
            'categoria',
            'status',
            'is_destacado',
        ]

    def filtrar_por_texto(self, queryset, name, value):
        """
        Filtra itens por texto livre no título e descrição.

        Usa icontains para busca case-insensitive.
        """
        return queryset.filter(
            models.Q(titulo__icontains=value)
            | models.Q(descricao__icontains=value)
        )
