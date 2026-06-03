"""
Management command para criar selos ESG iniciais.

Uso: python manage.py seed_selos
"""

from django.core.management.base import BaseCommand

from apps.esg.models import SeloESG


class Command(BaseCommand):
    help = 'Cria os selos ecológicos iniciais do Aloogaí'

    def handle(self, *args, **options):
        selos = [
            {
                'nome': 'Vizinho Verde',
                'descricao': (
                    'Parabéns! Você completou 10 locações e está ajudando '
                    'a reduzir o consumo desnecessário na sua vizinhança.'
                ),
                'icone': 'leaf',
                'requisito_locacoes': 10,
                'requisito_score': None,
            },
            {
                'nome': 'Herói Circular',
                'descricao': (
                    'Incrível! 50 locações concluídas. Você é um verdadeiro '
                    'herói da economia circular!'
                ),
                'icone': 'recycle',
                'requisito_locacoes': 50,
                'requisito_score': None,
            },
            {
                'nome': 'Embaixador ESG',
                'descricao': (
                    'Lendário! 100 locações concluídas. Você é um embaixador '
                    'da sustentabilidade no Aloogaí.'
                ),
                'icone': 'globe',
                'requisito_locacoes': 100,
                'requisito_score': None,
            },
            {
                'nome': 'Estrela Sustentável',
                'descricao': (
                    'Seu impacto ambiental é extraordinário! Você economizou '
                    'mais de 100 kg de CO₂ com suas locações.'
                ),
                'icone': 'star',
                'requisito_locacoes': None,
                'requisito_score': 100.0,
            },
            {
                'nome': 'Guardião do Planeta',
                'descricao': (
                    'Impressionante! Mais de 500 kg de CO₂ economizados. '
                    'Você é um guardião do planeta!'
                ),
                'icone': 'earth',
                'requisito_locacoes': None,
                'requisito_score': 500.0,
            },
        ]

        criados = 0
        for selo_data in selos:
            selo, created = SeloESG.objects.get_or_create(
                nome=selo_data['nome'],
                defaults=selo_data,
            )
            if created:
                criados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Selo criado: {selo.nome}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ Selo já existe: {selo.nome}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🏅 {criados} selos criados de {len(selos)} totais.'
            )
        )
