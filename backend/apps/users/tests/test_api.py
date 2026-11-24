"""
Testes de API de usuários: cadastro, login por e-mail e perfil.
"""
from rest_framework.test import APITestCase

from apps.rentals.tests.conftest import UsuarioFactory
from apps.users.models import Usuario

REGISTRO = '/api/v1/users/registro/'
TOKEN = '/api/v1/auth/token/'
PERFIL = '/api/v1/users/perfil/'


def _dados_cadastro(**extra):
    dados = {
        'email': 'Maria@Exemplo.com',
        'first_name': 'Maria',
        'password': 'SenhaForte!2026',
        'password_confirm': 'SenhaForte!2026',
        'tipo_usuario': 'P2P',
        'cpf_cnpj': '123.456.789-09',
        'telefone': '48999990000',
    }
    dados.update(extra)
    return dados


class CadastroTests(APITestCase):
    def test_cadastro_sem_username_usa_o_email_e_permite_login(self):
        resposta = self.client.post(REGISTRO, _dados_cadastro(), format='json')
        self.assertEqual(resposta.status_code, 201, resposta.data)
        usuario = Usuario.objects.get(email='maria@exemplo.com')
        self.assertEqual(usuario.username, 'maria@exemplo.com')
        self.assertEqual(usuario.cpf_cnpj, '12345678909')

        login = self.client.post(
            TOKEN, {'username': 'maria@exemplo.com', 'password': 'SenhaForte!2026'}, format='json',
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.data)
        self.assertIn('refresh', login.data)

    def test_email_repetido_e_recusado(self):
        self.client.post(REGISTRO, _dados_cadastro(), format='json')
        resposta = self.client.post(
            REGISTRO, _dados_cadastro(email='maria@exemplo.com', cpf_cnpj='98765432100'), format='json',
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('email', resposta.data)

    def test_cpf_com_e_sem_mascara_e_o_mesmo(self):
        self.client.post(REGISTRO, _dados_cadastro(), format='json')
        resposta = self.client.post(
            REGISTRO, _dados_cadastro(email='outra@exemplo.com', cpf_cnpj='12345678909'), format='json',
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('cpf_cnpj', resposta.data)


class PerfilTests(APITestCase):
    def test_perfil_nao_permite_trocar_email_nem_tipo(self):
        usuario = UsuarioFactory(tipo_usuario='P2P')
        email_original = usuario.email
        self.client.force_authenticate(usuario)
        resposta = self.client.patch(
            PERFIL, {'email': 'novo@exemplo.com', 'tipo_usuario': 'B2B', 'telefone': '48999990000'},
            format='json',
        )
        self.assertEqual(resposta.status_code, 200)
        usuario.refresh_from_db()
        self.assertEqual(usuario.email, email_original)
        self.assertEqual(usuario.tipo_usuario, 'P2P')
        self.assertEqual(usuario.telefone, '48999990000')
