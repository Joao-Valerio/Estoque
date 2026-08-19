from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, ContatoMensagem, Fornecedor, Movimentacao, Produto


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
