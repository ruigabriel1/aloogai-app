import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Endereco
from apps.catalog.models import Categoria, Item

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de teste realistas'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando seed de dados falsos...')

        # 1. Categorias
        categorias_data = [
            {'nome': 'Ferramentas', 'slug': 'ferramentas', 'icone': 'hammer'},
            {'nome': 'Camping e Aventura', 'slug': 'camping', 'icone': 'tent'},
            {'nome': 'Limpeza Pesada', 'slug': 'limpeza', 'icone': 'spray-can'},
            {'nome': 'Audiovisual', 'slug': 'audiovisual', 'icone': 'camera'},
        ]
        
        categorias = {}
        for c in categorias_data:
            obj, _ = Categoria.objects.get_or_create(
                slug=c['slug'],
                defaults={'nome': c['nome'], 'icone': c['icone']}
            )
            categorias[c['slug']] = obj
        self.stdout.write(self.style.SUCCESS(f'{len(categorias)} Categorias criadas/carregadas.'))

        # 2. Usuários
        usuarios_data = [
            {'username': 'joao.locador', 'email': 'joao@teste.com', 'nome': 'João da Silva', 'tipo': 'P2P', 'cpf_cnpj': '111.111.111-11'},
            {'username': 'maria.b2b', 'email': 'maria@teste.com', 'nome': 'Maria Locadora ME', 'tipo': 'B2B', 'cpf_cnpj': '11.111.111/0001-11'},
            {'username': 'carlos.cliente', 'email': 'carlos@teste.com', 'nome': 'Carlos Cliente', 'tipo': 'P2P', 'cpf_cnpj': '222.222.222-22'},
        ]

        usuarios = []
        for u in usuarios_data:
            user, created = Usuario.objects.get_or_create(
                username=u['username'],
                defaults={
                    'email': u['email'],
                    'first_name': u['nome'].split()[0],
                    'last_name': ' '.join(u['nome'].split()[1:]),
                    'tipo_usuario': u['tipo'],
                    'cpf_cnpj': u['cpf_cnpj'],
                    'kyc_status': 'APROVADO',
                    'stripe_onboarding_complete': True,
                    'score_esg': random.randint(10, 150)
                }
            )
            if created:
                user.set_password('senha123')
                user.save()
            usuarios.append(user)
        self.stdout.write(self.style.SUCCESS(f'{len(usuarios)} Usuários criados com senha: senha123'))

        # 3. Endereços e Itens
        # Pontos geográficos reais em SP (Avenida Paulista, Pinheiros, Vila Madalena)
        locais_sp = [
            {'lat': -23.5615, 'lng': -46.6560, 'bairro': 'Cerqueira César'},
            {'lat': -23.5670, 'lng': -46.6938, 'bairro': 'Pinheiros'},
            {'lat': -23.5489, 'lng': -46.6388, 'bairro': 'Centro'},
            {'lat': -23.5896, 'lng': -46.6340, 'bairro': 'Vila Mariana'},
            {'lat': -23.5505, 'lng': -46.6333, 'bairro': 'Sé'},
        ]

        # Criar endereços
        enderecos = []
        for i, user in enumerate(usuarios):
            local = locais_sp[i % len(locais_sp)]
            end, _ = Endereco.objects.get_or_create(
                usuario=user,
                is_principal=True,
                defaults={
                    'apelido': 'Principal',
                    'logradouro': f'Rua {local["bairro"]}, {random.randint(10, 999)}',
                    'numero': str(random.randint(10, 999)),
                    'bairro': local['bairro'],
                    'cidade': 'São Paulo',
                    'estado': 'SP',
                    'cep': '01000-000',
                    'localizacao': f"SRID=4326;POINT({local['lng']} {local['lat']})"
                }
            )
            enderecos.append(end)

        self.stdout.write(self.style.SUCCESS(f'{len(enderecos)} Endereços em SP criados.'))

        # Criar Itens
        itens_catalogo = [
            {'titulo': 'Furadeira Bosch Impacto', 'cat': 'ferramentas', 'preco': 25.00, 'caucao': 150.00},
            {'titulo': 'Tenda Canadense 4 Pessoas', 'cat': 'camping', 'preco': 45.00, 'caucao': 200.00},
            {'titulo': 'WAP Lavadora de Alta Pressão', 'cat': 'limpeza', 'preco': 60.00, 'caucao': 350.00},
            {'titulo': 'Caixa de Som JBL Boombox', 'cat': 'audiovisual', 'preco': 80.00, 'caucao': 800.00},
            {'titulo': 'Serra Tico-Tico Makita', 'cat': 'ferramentas', 'preco': 30.00, 'caucao': 180.00},
            {'titulo': 'Projetor Epson Full HD', 'cat': 'audiovisual', 'preco': 100.00, 'caucao': 1200.00},
            {'titulo': 'Cooler Térmico 30L', 'cat': 'camping', 'preco': 15.00, 'caucao': 80.00},
            {'titulo': 'Extratora Wap Carpet WAP', 'cat': 'limpeza', 'preco': 70.00, 'caucao': 400.00},
        ]

        count_itens = 0
        for item_data in itens_catalogo:
            # Seleciona um locador aleatório que seja P2P ou B2B (exclui o Carlos que é só cliente para testes)
            locador = random.choice([usuarios[0], usuarios[1]])
            endereco = Endereco.objects.filter(usuario=locador, is_principal=True).first()
            
            Item.objects.get_or_create(
                titulo=item_data['titulo'],
                defaults={
                    'locador': locador,
                    'categoria': categorias[item_data['cat']],
                    'descricao': f'Alugo {item_data["titulo"]} em ótimo estado. Ideal para as suas necessidades.',
                    'status': 'ATIVO',
                    'preco_diaria': item_data['preco'],
                    'valor_caucao': item_data['caucao'],
                    'localizacao': endereco.localizacao,
                    'endereco_texto': f"{endereco.bairro}, {endereco.cidade}",
                    'avaliacao_media': round(random.uniform(4.0, 5.0), 1),
                    'total_avaliacoes': random.randint(1, 20)
                }
            )
            count_itens += 1

        self.stdout.write(self.style.SUCCESS(f'{count_itens} Itens de teste criados com sucesso.'))
        self.stdout.write(self.style.SUCCESS('\nSEED FINALIZADO!'))
        self.stdout.write(self.style.WARNING('Use os seguintes dados no app para logar:'))
        self.stdout.write(self.style.WARNING('- E-mail: joao@teste.com | Senha: senha123 (Tem itens cadastrados)'))
        self.stdout.write(self.style.WARNING('- E-mail: carlos@teste.com | Senha: senha123 (Apenas cliente)'))
