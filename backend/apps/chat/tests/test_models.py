"""
Testes unitários para os modelos do app de Chat.

Cobre: SalaChat (permissões, propriedades) e
Mensagem (criptografia, marcar como lida).
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.chat.models import Mensagem, SalaChat, STATUS_ORDEM
from apps.rentals.tests.conftest import LocacaoFactory, UsuarioFactory


# Chave Fernet válida para testes
TEST_ENCRYPTION_KEY = "dGVzdGVfY2hhdmVfZmVybmV0XzMyX2J5dGVzMTIzNA=="


class SalaChatFactory:
    """Factory simples para criar/obter SalaChat a partir de Locacao."""

    @staticmethod
    def criar(locacao=None, **kwargs):
        """
        Obtém ou cria uma SalaChat vinculada a uma locação.

        Como o signal ``criar_sala_chat_para_locacao`` cria a sala
        automaticamente, este método usa get_or_create para evitar
        erros de UNIQUE constraint.
        """
        if locacao is None:
            locacao = LocacaoFactory()

        sala, _ = SalaChat.objects.get_or_create(
            locacao=locacao,
            defaults={
                'locador': locacao.item.locador,
                'locatario': locacao.locatario,
                **kwargs,
            },
        )
        # Aplicar kwargs extras (ex: ativa=False) mesmo se já existia
        if kwargs:
            for key, value in kwargs.items():
                setattr(sala, key, value)
            sala.save()
        return sala


class TestSalaChatPermissoes(TestCase):
    """Testes para a propriedade chat_permitido da SalaChat."""

    def test_chat_permitido_status_solicitado(self):
        """Chat deve ser permitido quando status é SOLICITADO."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        self.assertTrue(sala.chat_permitido)

    def test_chat_permitido_status_caucao_retida(self):
        """Chat deve ser permitido quando status é CAUCAO_RETIDA."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test')
        locacao.save()
        sala = SalaChatFactory.criar(locacao)
        self.assertTrue(sala.chat_permitido)

    def test_chat_permitido_status_ativo(self):
        """Chat deve ser permitido quando status é ATIVO."""
        locacao = LocacaoFactory()
        locacao.reter_caucao(caucao_auth_id='pi_test')
        locacao.save()
        locacao.confirmar_entrega()
        locacao.save()
        sala = SalaChatFactory.criar(locacao)
        self.assertTrue(sala.chat_permitido)

    def test_chat_nao_permitido_status_cancelado(self):
        """Chat NÃO deve ser permitido quando status é CANCELADO."""
        locacao = LocacaoFactory()
        locacao.cancelar()
        locacao.save()
        sala = SalaChatFactory.criar(locacao)
        self.assertFalse(sala.chat_permitido)

    def test_chat_nao_permitido_sala_inativa(self):
        """Chat NÃO deve ser permitido quando sala está inativa."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao, ativa=False)
        self.assertFalse(sala.chat_permitido)


class TestSalaChatParticipantes(TestCase):
    """Testes para verificação de participantes da SalaChat."""

    def test_locador_pertence_a_sala(self):
        """Locador deve pertencer à sala."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        self.assertTrue(sala.usuario_pertence(locacao.item.locador))

    def test_locatario_pertence_a_sala(self):
        """Locatário deve pertencer à sala."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        self.assertTrue(sala.usuario_pertence(locacao.locatario))

    def test_usuario_externo_nao_pertence(self):
        """Usuário externo NÃO deve pertencer à sala."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        externo = UsuarioFactory()
        self.assertFalse(sala.usuario_pertence(externo))

    def test_str(self):
        """__str__ deve conter identificador da locação."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        self.assertIn('Chat', str(sala))


@override_settings(
    CHAT_ENCRYPTION_KEY="SnHuRUEzdTFIQTlCRDB6YkFrcFNGSmM2VDk2VjdVRUo="
)
class TestMensagemCriptografia(TestCase):
    """Testes para criptografia de mensagens (AES-256 / Fernet)."""

    def _gerar_chave_fernet(self):
        """Gera uma chave Fernet válida para testes."""
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()

    @override_settings(CHAT_ENCRYPTION_KEY=None)
    def test_criptografia_sem_chave_gera_erro(self):
        """Sem CHAT_ENCRYPTION_KEY, o campo deve lançar ValueError."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        with self.assertRaises(ValueError):
            Mensagem.objects.create(
                sala=sala,
                remetente=locacao.locatario,
                conteudo="Mensagem secreta",
                tipo="TEXTO",
            )


class TestMensagemLeitura(TestCase):
    """Testes para marcação de leitura de mensagens."""

    @override_settings(
        CHAT_ENCRYPTION_KEY="nSnUuzyAxg57aBDlaBp0tw5Qm5XdJCH1kjeLlfZxzCs="
    )
    def test_mensagem_inicia_como_nao_lida(self):
        """Mensagem nova deve ter lida_em como None."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        msg = Mensagem.objects.create(
            sala=sala,
            remetente=locacao.locatario,
            conteudo="Olá!",
            tipo="TEXTO",
        )
        self.assertIsNone(msg.lida_em)

    @override_settings(
        CHAT_ENCRYPTION_KEY="nSnUuzyAxg57aBDlaBp0tw5Qm5XdJCH1kjeLlfZxzCs="
    )
    def test_marcar_como_lida(self):
        """marcar_como_lida deve definir lida_em com timestamp."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        msg = Mensagem.objects.create(
            sala=sala,
            remetente=locacao.locatario,
            conteudo="Olá!",
            tipo="TEXTO",
        )
        msg.marcar_como_lida()
        msg.refresh_from_db()
        self.assertIsNotNone(msg.lida_em)

    @override_settings(
        CHAT_ENCRYPTION_KEY="nSnUuzyAxg57aBDlaBp0tw5Qm5XdJCH1kjeLlfZxzCs="
    )
    def test_marcar_como_lida_nao_sobrescreve(self):
        """Marcar como lida duas vezes não deve alterar o timestamp original."""
        locacao = LocacaoFactory()
        sala = SalaChatFactory.criar(locacao)
        msg = Mensagem.objects.create(
            sala=sala,
            remetente=locacao.locatario,
            conteudo="Olá!",
            tipo="TEXTO",
        )
        msg.marcar_como_lida()
        primeiro_lida = msg.lida_em

        msg.marcar_como_lida()
        self.assertEqual(msg.lida_em, primeiro_lida)


class TestStatusOrdem(TestCase):
    """Testes para a constante STATUS_ORDEM."""

    def test_cancelado_tem_ordem_zero(self):
        """CANCELADO deve ter ordem 0 (menor que SOLICITADO)."""
        self.assertEqual(STATUS_ORDEM["CANCELADO"], 0)

    def test_solicitado_e_o_minimo_para_chat(self):
        """SOLICITADO deve ser o mínimo (ordem 1) para habilitar o chat."""
        self.assertEqual(STATUS_ORDEM["SOLICITADO"], 1)

    def test_ordem_crescente(self):
        """Status devem seguir ordem crescente do FSM."""
        self.assertTrue(
            STATUS_ORDEM["SOLICITADO"]
            < STATUS_ORDEM["CAUCAO_RETIDA"]
            < STATUS_ORDEM["ATIVO"]
            < STATUS_ORDEM["DEVOLVIDO"]
            < STATUS_ORDEM["CONCLUIDO"]
        )


class TestCriacaoAutomaticaSalaChat(TestCase):
    """Testes para o signal de criação automática de SalaChat."""

    def test_sala_criada_automaticamente_ao_criar_locacao(self):
        """Criar uma locação deve criar uma SalaChat automaticamente."""
        locacao = LocacaoFactory()
        self.assertTrue(
            SalaChat.objects.filter(locacao=locacao).exists()
        )

    def test_sala_tem_locador_e_locatario_corretos(self):
        """SalaChat criada via signal deve ter participantes corretos."""
        locacao = LocacaoFactory()
        sala = SalaChat.objects.get(locacao=locacao)
        self.assertEqual(sala.locador, locacao.item.locador)
        self.assertEqual(sala.locatario, locacao.locatario)

    def test_nao_cria_sala_duplicada(self):
        """Salvar locação novamente não deve criar sala duplicada."""
        locacao = LocacaoFactory()
        locacao.save()  # Salvar novamente (não é created)
        self.assertEqual(
            SalaChat.objects.filter(locacao=locacao).count(),
            1,
        )
