"""
Factories para testes do app de Locações.

Usa factory_boy para gerar instâncias realistas dos modelos
necessários para os testes.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import factory
from django.contrib.auth import get_user_model

from apps.catalog.models import Categoria, Item
from apps.rentals.models import Locacao, StatusLocacao

Usuario = get_user_model()


class UsuarioFactory(factory.django.DjangoModelFactory):
    """Factory para o modelo Usuario."""

    class Meta:
        model = Usuario

    username = factory.Sequence(lambda n: f'usuario_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@aloogai.com')
    first_name = factory.Faker('first_name', locale='pt_BR')
    last_name = factory.Faker('last_name', locale='pt_BR')
    cpf_cnpj = factory.Sequence(lambda n: f'{str(n).zfill(11)}')
    telefone = factory.Faker('phone_number', locale='pt_BR')
    tipo_usuario = 'P2P'
    kyc_status = 'APROVADO'
    stripe_account_id = factory.LazyAttribute(lambda obj: f'acct_test_{obj.username}')
    stripe_onboarding_complete = True
    password = factory.PostGenerationMethodCall('set_password', 'senha123')


class CategoriaFactory(factory.django.DjangoModelFactory):
    """Factory para o modelo Categoria."""

    class Meta:
        model = Categoria

    id = factory.LazyFunction(uuid.uuid4)
    nome = factory.Sequence(lambda n: f'Categoria {n}')
    slug = factory.Sequence(lambda n: f'categoria-{n}')
    ativa = True


class ItemFactory(factory.django.DjangoModelFactory):
    """Factory para o modelo Item."""

    class Meta:
        model = Item

    id = factory.LazyFunction(uuid.uuid4)
    locador = factory.SubFactory(UsuarioFactory)
    categoria = factory.SubFactory(CategoriaFactory)
    titulo = factory.Faker('sentence', nb_words=3, locale='pt_BR')
    descricao = factory.Faker('paragraph', locale='pt_BR')
    camada = 'ESSENTIAL'
    status = 'ATIVO'
    preco_diaria = Decimal('25.00')
    valor_caucao = Decimal('150.00')
    aprovado_para_uso = True
    localizacao = ''  # TextField em modo SQLite (PointField em produção)


class LocacaoFactory(factory.django.DjangoModelFactory):
    """Factory para o modelo Locacao."""

    class Meta:
        model = Locacao

    id = factory.LazyFunction(uuid.uuid4)
    item = factory.SubFactory(ItemFactory)
    locatario = factory.SubFactory(UsuarioFactory)
    data_inicio = factory.LazyFunction(lambda: date.today() + timedelta(days=1))
    data_fim = factory.LazyFunction(lambda: date.today() + timedelta(days=3))
    valor_diarias = Decimal('50.00')
    valor_caucao = Decimal('150.00')
    valor_taxa_servico = Decimal('5.00')
    valor_taxa_sucesso = Decimal('7.50')
    total_locatario = Decimal('55.00')
