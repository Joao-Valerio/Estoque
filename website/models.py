from django.db import models

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=15)
    endereco = models.TextField()

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.IntegerField(default=0)
    quantidade_minima = models.IntegerField(default=15)

    def estoque_status(self):
        if self.quantidade == 0:
            return "Sem estoque"
        elif self.quantidade <= self.quantidade_minima:
            return "Estoque baixo"
        else:
            return "Estoque ok"

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name='produtos'
    )

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos'
    )

    def __str__(self):
        return self.nome


class Movimentacao(models.Model):

    TIPOS = (
        ("E", "Entrada"),
        ("S", "Saída"),
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="movimentacoes",
    )

    tipo = models.CharField(max_length=1, choices=TIPOS)

    quantidade = models.IntegerField()

    data = models.DateTimeField(auto_now_add=True)

    observacao = models.TextField(blank=True, null=True)

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_entrada",
        verbose_name="Fornecedor",
    )

    destinatario = models.CharField(
        "Destinatário",
        max_length=200,
        blank=True,
        default="",
    )

    def __str__(self):
        return f"{self.produto.nome} - {self.get_tipo_display()}"