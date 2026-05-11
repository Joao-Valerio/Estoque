from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView

from .forms import (
    ProdutoForm,
    CategoriaForm,
    MovimentacaoForm,
    FornecedorForm,
)
from .models import (
    Produto,
    Categoria,
    Movimentacao,
    Fornecedor,
)

class ProdutosPageView(TemplateView):
    template_name = "produtos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produtos = Produto.objects.select_related(
            "categoria", "fornecedor"
        ).order_by("nome")
        context["produtos"] = produtos
        context["produtos_count"] = produtos.count()    
        context["sem_estoque"] = Produto.objects.filter(
            quantidade=0
        ).count()
        context["estoque_baixo"] = Produto.objects.filter(
            quantidade__gt=0,
            quantidade__lte=F("quantidade_minima")
        )
        return context

class HomePageView(TemplateView):
    template_name = "home.html"

class ModeloPageView(TemplateView):
    template_name = "modelo.html"

class EstoquePageView(TemplateView):
    template_name = "estoque.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["produtos_count"] = Produto.objects.count()
        return context

class RelatorioPageView(TemplateView):
    template_name = "relatorio.html"

class PerfilPageView(TemplateView):
    template_name = "perfil.html"

class ConfiguracoesPageView(TemplateView):
    template_name = "configuracoes.html"

class ContatoPageView(TemplateView):
    template_name = "contato.html"

class PainelPageView(TemplateView):
    template_name = "painel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["produtos_count"] = Produto.objects.count()

        context["sem_estoque"] = Produto.objects.filter(
            quantidade=0
        ).count()

        context["estoque_baixo"] = Produto.objects.filter(
            quantidade__gt=0,
            quantidade__lte=F("quantidade_minima")
        ).count()

        context["mais_vendidos"] = 0

        total = (
            Produto.objects.annotate(
                subtotal=F("quantidade") * F("preco")
            ).aggregate(
                v=Sum("subtotal")
            )["v"]
        )

        context["valor_total"] = (
            total if total is not None else Decimal("0")
        )

        return context


class RelatoriosPageView(TemplateView):
    template_name = "relatorios.html"

class CreateProdutoPageView(CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = "create_produto.html"
    success_url = reverse_lazy("produtos")

class CreateCategoriaPageView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "create_categoria.html"
    success_url = reverse_lazy("painel")

class CreateMovimentacaoPageView(CreateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = "create_movimentacao.html"
    success_url = reverse_lazy("painel")


class CreateFornecedorPageView(CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = "create_fornecedor.html"
    success_url = reverse_lazy("painel")
