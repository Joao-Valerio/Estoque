from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import F, Q


# ---------------------------------------------------------------------------
#  QuerySets reutilizáveis
# ---------------------------------------------------------------------------

class OwnerQuerySet(models.QuerySet):
    """QuerySet com filtro por proprietário (campo `usuario`)."""

    def do_usuario(self, user):
        return self.filter(usuario=user)


class MovimentacaoQuerySet(models.QuerySet):
    """QuerySet para movimentações (proprietário via produto__usuario)."""

    def do_usuario(self, user):
        return self.filter(produto__usuario=user)


# ---------------------------------------------------------------------------
#  Validators reutilizáveis
# ---------------------------------------------------------------------------

_TELEFONE_BR_REGEX = RegexValidator(
    regex=r"^\(?\d{2}\)?\s?\d{4,5}-?\d{4}$",
    message="Informe um telefone válido. Ex.: (11) 99999-9999",
)


# ---------------------------------------------------------------------------
#  Models
# ---------------------------------------------------------------------------

class Categoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorias",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField()

    objects = OwnerQuerySet.as_manager()

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fornecedores",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=15, validators=[_TELEFONE_BR_REGEX])
    endereco = models.TextField()

    objects = OwnerQuerySet.as_manager()

    def __str__(self):
        return self.nome


class Produto(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="produtos",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantidade = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    quantidade_minima = models.IntegerField(
        default=15,
        validators=[MinValueValidator(0)],
    )

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

    objects = OwnerQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(preco__gte=0),
                name="preco_positivo",
            ),
            models.CheckConstraint(
                check=Q(quantidade__gte=0),
                name="quantidade_positiva",
            ),
        ]

    def __str__(self):
        return self.nome

    # ------------------------------------------------------------------
    #  Lógica de negócio — entrada e saída de estoque
    # ------------------------------------------------------------------

    def registrar_entrada(self, quantidade: int) -> None:
        """
        Incrementa o estoque do produto de forma atômica.
        Deve ser chamado dentro de um ``transaction.atomic()``.
        """
        Produto.objects.filter(pk=self.pk).update(
            quantidade=F("quantidade") + quantidade
        )

    def registrar_saida(self, quantidade: int) -> None:
        """
        Decrementa o estoque do produto de forma atômica e com
        ``select_for_update`` para evitar race conditions.

        Levanta ``ValueError`` se o estoque for insuficiente.
        Deve ser chamado dentro de um ``transaction.atomic()``.
        """
        prod = (
            Produto.objects.select_for_update()
            .filter(pk=self.pk)
            .first()
        )
        if prod is None:
            raise ValueError("Produto não encontrado.")
        if prod.quantidade < quantidade:
            raise ValueError(
                f"Estoque insuficiente. Disponível: {prod.quantidade}."
            )
        Produto.objects.filter(pk=self.pk).update(
            quantidade=F("quantidade") - quantidade
        )


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

    quantidade = models.IntegerField(
        validators=[MinValueValidator(1)],
    )

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

    objects = MovimentacaoQuerySet.as_manager()

    def __str__(self):
        return f"{self.produto.nome} - {self.get_tipo_display()}"


class ContatoMensagem(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="mensagens_contato",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    assunto = models.CharField(max_length=180)
    mensagem = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-criado_em",)

    def __str__(self):
        return f"{self.assunto} ({self.email})"