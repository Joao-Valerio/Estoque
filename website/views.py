from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView

from .forms import (
    ProdutoForm,
    CategoriaForm,
    MovimentacaoForm,
    FornecedorForm,
    UpdateProdutoForm,
)
from .models import (
    Produto,
    Categoria,
    Movimentacao,
    Fornecedor,
)

class DashboardContextMixin:

    def get_dashboard_context(self):
        total = (
            Produto.objects.annotate(
                subtotal=F("quantidade") * F("preco")
            ).aggregate(
                total=Sum("subtotal")
            )["total"]
        )

        estoque_baixo = Produto.objects.filter(
            quantidade__gt=0,
            quantidade__lte=F("quantidade_minima")
        )

        em_estoque = Produto.objects.filter(
            quantidade__gt=0
        )

        return {
            "produtos_count": Produto.objects.count(),

            "sem_estoque_count": Produto.objects.filter(
                quantidade=0
            ).count(),

            "estoque_baixo_count": estoque_baixo.count(),

            "estoque_baixo": estoque_baixo,

            "em_estoque_count": em_estoque.count(),

            "em_estoque": em_estoque,

            "valor_total": total or Decimal("0"),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_dashboard_context())
        return context

class ProdutosPageView(DashboardContextMixin, TemplateView):
    template_name = "produtos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["produtos"] = (
            Produto.objects
            .select_related("categoria", "fornecedor")
            .order_by("nome")
        )

        return context

class HomePageView(TemplateView):
    template_name = "home.html"

class ModeloPageView(TemplateView):
    template_name = "modelo.html"

class EstoquePageView(DashboardContextMixin, TemplateView):
    template_name = "estoque.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["produtos"] = (
            Produto.objects.select_related("categoria", "fornecedor").order_by(
                "nome"
            )
        )
        return context


class RelatorioPageView(TemplateView):
    template_name = "relatorio.html"

class PerfilPageView(TemplateView):
    template_name = "perfil.html"

class ConfiguracoesPageView(TemplateView):
    template_name = "configuracoes.html"

class ContatoPageView(TemplateView):
    template_name = "contato.html"

class PainelPageView(DashboardContextMixin, TemplateView):
    template_name = "painel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = Categoria.objects.order_by("nome")
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

class UpdateProdutoPageView(UpdateView):
    model = Produto
    form_class = UpdateProdutoForm
    template_name = "update_produto.html"
    success_url = reverse_lazy("produtos")