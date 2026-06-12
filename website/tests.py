from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, ContatoMensagem, Fornecedor, Produto


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
            telefone="11999999999",
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
