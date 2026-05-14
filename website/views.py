from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
)

from .forms import (
    ProdutoForm,
    CategoriaForm,
    MovimentacaoEntradaForm,
    MovimentacaoSaidaForm,
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
        context["movimentacoes_count"] = Movimentacao.objects.count()
        return context


class RelatorioPageView(TemplateView):
    template_name = "relatorio.html"

class FornecedoresPageView(TemplateView):
    template_name = "fornecedores.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fornecedores"] = Fornecedor.objects.order_by("nome")
        return context

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

class MovimentacoesPageView(ListView):
    model = Movimentacao
    template_name = "movimentacoes.html"
    context_object_name = "movimentacoes"
    paginate_by = 25

    def get_queryset(self):
        return (
            Movimentacao.objects.select_related("produto", "fornecedor")
            .order_by("-data")
        )


class MovimentacaoHubView(TemplateView):
    template_name = "movimentacao_hub.html"


class CreateMovimentacaoEntradaView(CreateView):
    model = Movimentacao
    form_class = MovimentacaoEntradaForm
    template_name = "create_movimentacao_entrada.html"
    success_url = reverse_lazy("movimentacoes")

    def form_valid(self, form):
        mov = form.save(commit=False)
        mov.tipo = "E"
        mov.destinatario = ""
        qty = mov.quantidade
        with transaction.atomic():
            updated = Produto.objects.filter(pk=mov.produto_id).update(
                quantidade=F("quantidade") + qty
            )
            if not updated:
                form.add_error(None, "Produto não encontrado.")
                return self.form_invalid(form)
            mov.save()
        return redirect(self.get_success_url())


class CreateMovimentacaoSaidaView(CreateView):
    model = Movimentacao
    form_class = MovimentacaoSaidaForm
    template_name = "create_movimentacao_saida.html"
    success_url = reverse_lazy("movimentacoes")

    def form_valid(self, form):
        mov = form.save(commit=False)
        mov.tipo = "S"
        mov.fornecedor = None
        qty = mov.quantidade
        with transaction.atomic():
            prod = (
                Produto.objects.select_for_update()
                .filter(pk=mov.produto_id)
                .first()
            )
            if prod is None:
                form.add_error(None, "Produto não encontrado.")
                return self.form_invalid(form)
            if prod.quantidade < qty:
                form.add_error(
                    "quantidade",
                    f"Estoque insuficiente. Disponível: {prod.quantidade}.",
                )
                return self.form_invalid(form)
            Produto.objects.filter(pk=prod.pk).update(quantidade=F("quantidade") - qty)
            mov.save()
        return redirect(self.get_success_url())

class CreateFornecedorPageView(CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = "create_fornecedor.html"
    success_url = reverse_lazy("fornecedores")


class UpdateFornecedorPageView(UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    template_name = "update_fornecedor.html"
    success_url = reverse_lazy("fornecedores")


class DeleteFornecedorView(DeleteView):
    model = Fornecedor
    template_name = "fornecedor_confirm_delete.html"
    success_url = reverse_lazy("fornecedores")

class UpdateProdutoPageView(UpdateView):
    model = Produto
    form_class = UpdateProdutoForm
    template_name = "update_produto.html"
    success_url = reverse_lazy("produtos")