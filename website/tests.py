from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import (
    Categoria,
    ContatoMensagem,
    Fornecedor,
    Movimentacao,
    Produto,
    ConfiguracaoUsuario,
)
from .notifications import alertas_estoque_usuario


class WebsiteFlowsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="123456Teste!",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="123456Teste!",
        )
        self.categoria = Categoria.objects.create(
            usuario=self.user,
            nome="Eletronicos",
            descricao="Categoria principal",
        )
        self.fornecedor = Fornecedor.objects.create(
            usuario=self.user,
            nome="Fornecedor A",
            email="fornecedor@example.com",
            telefone="(11) 99999-9999",
            endereco="Rua A, 123",
        )
        self.produto = Produto.objects.create(
            usuario=self.user,
            nome="Produto teste",
            descricao="Descricao",
            preco=Decimal("10.00"),
            quantidade=15,
            quantidade_minima=5,
            categoria=self.categoria,
            fornecedor=self.fornecedor,
        )

    def test_modelo_route_works(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("modelo"))
        self.assertEqual(response.status_code, 200)

    def test_delete_produto_only_owner(self):
        other_categoria = Categoria.objects.create(
            usuario=self.other_user,
            nome="Categoria outro",
            descricao="Descricao",
        )
        other_produto = Produto.objects.create(
            usuario=self.other_user,
            nome="Produto outro",
            descricao="Descricao",
            preco=Decimal("20.00"),
            quantidade=3,
            quantidade_minima=1,
            categoria=other_categoria,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("delete_produto", args=[self.produto.pk]))
        self.assertRedirects(response, reverse("produtos"))
        self.assertFalse(Produto.objects.filter(pk=self.produto.pk).exists())

        forbidden = self.client.post(reverse("delete_produto", args=[other_produto.pk]))
        self.assertEqual(forbidden.status_code, 404)
        self.assertTrue(Produto.objects.filter(pk=other_produto.pk).exists())

    def test_contato_post_cria_mensagem(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("contato"),
            data={
                "nome": "Usuario Teste",
                "email": "owner@example.com",
                "assunto": "Ajuda",
                "mensagem": "Preciso de suporte.",
            },
        )
        self.assertRedirects(response, reverse("contato"))
        self.assertEqual(ContatoMensagem.objects.count(), 1)
        mensagem = ContatoMensagem.objects.first()
        self.assertEqual(mensagem.usuario, self.user)
        self.assertEqual(mensagem.assunto, "Ajuda")

    def test_movimentacao_saida_atualiza_estoque(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("create_movimentacao_saida"),
            data={
                "produto": self.produto.pk,
                "destinatario": "Cliente 1",
                "quantidade": 4,
                "observacao": "",
            },
        )
        self.assertRedirects(response, reverse("movimentacoes"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 11)


class CadastroEmailDuplicadoTestCase(TestCase):
    """Verifica que o cadastro rejeita e-mails já existentes."""

    def test_cadastro_email_duplicado(self):
        User.objects.create_user(
            username="existente@example.com",
            email="existente@example.com",
            password="Abc12345!",
        )
        response = self.client.post(
            reverse("cadastro"),
            data={
                "nome": "Novo Usuário",
                "email": "existente@example.com",
                "password1": "NovaSenha123!",
                "password2": "NovaSenha123!",
            },
        )
        # Deve retornar 200 (re-renderiza form com erros), não redirecionar
        self.assertEqual(response.status_code, 200)
        # Não deve ter criado um segundo usuário com o mesmo e-mail
        self.assertEqual(
            User.objects.filter(email__iexact="existente@example.com").count(), 1
        )


class EstoqueInsuficienteTestCase(TestCase):
    """Verifica que saída maior que o estoque disponível é rejeitada."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="teste@example.com",
            email="teste@example.com",
            password="Abc12345!",
        )
        self.categoria = Categoria.objects.create(
            usuario=self.user,
            nome="Geral",
            descricao="Categoria geral",
        )
        self.produto = Produto.objects.create(
            usuario=self.user,
            nome="Produto limitado",
            descricao="Pouco estoque",
            preco=Decimal("50.00"),
            quantidade=3,
            quantidade_minima=1,
            categoria=self.categoria,
        )

    def test_saida_estoque_insuficiente(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("create_movimentacao_saida"),
            data={
                "produto": self.produto.pk,
                "destinatario": "Cliente X",
                "quantidade": 10,  # Maior que 3 disponíveis
                "observacao": "",
            },
        )
        # Deve re-renderizar o form (status 200), não redirecionar
        self.assertEqual(response.status_code, 200)
        # Estoque não deve ter mudado
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 3)
        # Nenhuma movimentação deve ter sido criada
        self.assertEqual(Movimentacao.objects.count(), 0)


class EntradaEstoqueTestCase(TestCase):
    """Verifica que a entrada incrementa o estoque corretamente."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="entrada@example.com",
            email="entrada@example.com",
            password="Abc12345!",
        )
        self.categoria = Categoria.objects.create(
            usuario=self.user,
            nome="Geral",
            descricao="Categoria geral",
        )
        self.fornecedor = Fornecedor.objects.create(
            usuario=self.user,
            nome="Fornecedor B",
            email="b@example.com",
            telefone="(21) 98888-7777",
            endereco="Rua B, 456",
        )
        self.produto = Produto.objects.create(
            usuario=self.user,
            nome="Produto para entrada",
            descricao="Desc",
            preco=Decimal("25.00"),
            quantidade=10,
            quantidade_minima=5,
            categoria=self.categoria,
            fornecedor=self.fornecedor,
        )

    def test_entrada_atualiza_estoque(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("create_movimentacao_entrada"),
            data={
                "produto": self.produto.pk,
                "fornecedor": self.fornecedor.pk,
                "quantidade": 20,
                "observacao": "Reposição mensal",
            },
        )
        self.assertRedirects(response, reverse("movimentacoes"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 30)
        self.assertEqual(Movimentacao.objects.count(), 1)
        mov = Movimentacao.objects.first()
        self.assertEqual(mov.tipo, "E")
        self.assertEqual(mov.quantidade, 20)


class ProdutoValidacoesTestCase(TestCase):
    """Verifica que os validators do model rejeitam valores inválidos."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="valid@example.com",
            email="valid@example.com",
            password="Abc12345!",
        )
        self.categoria = Categoria.objects.create(
            usuario=self.user,
            nome="Teste",
            descricao="Categoria de teste",
        )

    def test_produto_preco_negativo_invalido(self):
        produto = Produto(
            usuario=self.user,
            nome="Produto inválido",
            descricao="Desc",
            preco=Decimal("-5.00"),
            quantidade=10,
            quantidade_minima=1,
            categoria=self.categoria,
        )
        with self.assertRaises(ValidationError):
            produto.full_clean()

    def test_produto_quantidade_negativa_invalida(self):
        produto = Produto(
            usuario=self.user,
            nome="Produto inválido",
            descricao="Desc",
            preco=Decimal("10.00"),
            quantidade=-1,
            quantidade_minima=1,
            categoria=self.categoria,
        )
        with self.assertRaises(ValidationError):
            produto.full_clean()


class ConfiguracaoUsuarioTestCase(TestCase):
    """Testa persistência e efeitos das configurações do usuário."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="config@example.com",
            email="config@example.com",
            password="Password123!",
        )
        self.categoria = Categoria.objects.create(
            usuario=self.user,
            nome="Geral",
            descricao="Desc",
        )
        self.produto = Produto.objects.create(
            usuario=self.user,
            nome="Produto Zerado",
            descricao="Desc",
            preco=Decimal("10.00"),
            quantidade=0,
            quantidade_minima=5,
            categoria=self.categoria,
        )

    def test_configuracoes_get_cria_ou_carrega_configuracao(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("configuracoes"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ConfiguracaoUsuario.objects.filter(usuario=self.user).exists())

    def test_configuracoes_post_salva_preferencias(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("configuracoes"),
            data={
                "notificacoes_ativas": False,
                "notificar_sem_estoque": True,
                "notificar_estoque_baixo": False,
                "relatorios_resumo": True,
            },
        )
        self.assertRedirects(response, reverse("configuracoes"))
        config = ConfiguracaoUsuario.objects.get(usuario=self.user)
        self.assertFalse(config.notificacoes_ativas)
        self.assertFalse(config.notificar_estoque_baixo)

        # Verifica que alertas_estoque_usuario respeita notificacoes_ativas = False
        alertas = alertas_estoque_usuario(self.user)
        self.assertEqual(len(alertas), 0)


class FornecedorBuscaTestCase(TestCase):
    """Testa a funcionalidade de busca por fornecedores."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="fornecedor@example.com",
            email="fornecedor@example.com",
            password="Password123!",
        )
        self.fornecedor1 = Fornecedor.objects.create(
            usuario=self.user,
            nome="Distribuidora Alpha",
            email="alpha@distribuidora.com",
            telefone="(11) 91111-1111",
            endereco="Av. Paulista, 100",
        )
        self.fornecedor2 = Fornecedor.objects.create(
            usuario=self.user,
            nome="Beta Logística",
            email="contato@betalog.com",
            telefone="(21) 92222-2222",
            endereco="Rua do Ouvidor, 50",
        )

    def test_busca_fornecedor_por_nome(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("fornecedores"), {"q": "Alpha"})
        self.assertEqual(response.status_code, 200)
        fornecedores = response.context["fornecedores"]
        self.assertEqual(fornecedores.count(), 1)
        self.assertEqual(fornecedores.first(), self.fornecedor1)

    def test_busca_fornecedor_por_email(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("fornecedores"), {"q": "betalog"})
        self.assertEqual(response.status_code, 200)
        fornecedores = response.context["fornecedores"]
        self.assertEqual(fornecedores.count(), 1)
        self.assertEqual(fornecedores.first(), self.fornecedor2)

    def test_busca_fornecedor_por_telefone(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("fornecedores"), {"q": "91111"})
        self.assertEqual(response.status_code, 200)
        fornecedores = response.context["fornecedores"]
        self.assertEqual(fornecedores.count(), 1)
        self.assertEqual(fornecedores.first(), self.fornecedor1)

