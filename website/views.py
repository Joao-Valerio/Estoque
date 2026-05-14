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
from .mixins import DeleteConfirmPageMixin, ModelFormPageMixin

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

        qs = (
            Produto.objects.select_related("categoria", "fornecedor").order_by("nome")
        )

        busca = self.request.GET.get("q", "").strip()
        if busca:
            qs = qs.filter(nome__icontains=busca)

        categoria_raw = self.request.GET.get("categoria", "").strip()
        categoria_atual = None
        if categoria_raw.isdigit():
            categoria_atual = int(categoria_raw)
            qs = qs.filter(categoria_id=categoria_atual)

        context["produtos"] = qs
        context["categorias"] = Categoria.objects.order_by("nome")
        context["busca_q"] = busca
        context["categoria_atual"] = categoria_atual

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

class CreateProdutoPageView(ModelFormPageMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    success_url = reverse_lazy("produtos")
    form_page_block_title = "Novo Produto - StockBot"
    form_page_title = "Novo Produto"
    form_page_subtitle = "Cadastre um novo produto no sistema de estoque"


class CreateCategoriaPageView(ModelFormPageMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    success_url = reverse_lazy("painel")
    form_page_block_title = "Nova Categoria - StockBot"
    form_page_title = "Nova Categoria"
    form_page_subtitle = "Organize seus produtos em categorias"

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


class CreateMovimentacaoEntradaView(ModelFormPageMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoEntradaForm
    success_url = reverse_lazy("movimentacoes")
    form_page_block_title = "Entrada de estoque - StockBot"
    form_page_title = "Entrada de estoque"
    form_page_subtitle = (
        "Registre um pedido ao fornecedor e atualize a quantidade do produto."
    )
    form_header_style = "offset"
    form_outer_shell_class = "mx-auto max-w-2xl"

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


class CreateMovimentacaoSaidaView(ModelFormPageMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoSaidaForm
    success_url = reverse_lazy("movimentacoes")
    form_page_block_title = "Saída de estoque - StockBot"
    form_page_title = "Saída de estoque"
    form_page_subtitle = "Registre uma venda ou saída informando o destinatário."
    form_header_style = "offset"
    form_outer_shell_class = "mx-auto max-w-2xl"

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

class CreateFornecedorPageView(ModelFormPageMixin, CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    success_url = reverse_lazy("fornecedores")
    form_page_block_title = "Novo Fornecedor - StockBot"
    form_page_title = "Novo Fornecedor"
    form_page_subtitle = "Cadastre um novo fornecedor"


class UpdateFornecedorPageView(ModelFormPageMixin, UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    success_url = reverse_lazy("fornecedores")
    form_submit_label = "Salvar alterações"
    form_page_block_title = "Editar Fornecedor - StockBot"
    form_page_title = "Editar Fornecedor"
    form_page_subtitle = "Atualize os dados do fornecedor"


class DeleteFornecedorView(DeleteConfirmPageMixin, DeleteView):
    model = Fornecedor
    success_url = reverse_lazy("fornecedores")
    form_page_block_title = "Excluir Fornecedor - StockBot"
    form_page_title = "Excluir fornecedor"
    form_page_subtitle = "Esta ação não pode ser desfeita."
    form_delete_cancel_url = reverse_lazy("fornecedores")


class UpdateProdutoPageView(ModelFormPageMixin, UpdateView):
    model = Produto
    form_class = UpdateProdutoForm
    success_url = reverse_lazy("produtos")
    form_variant = "hero"
    form_page_block_title = "Editar Produto - StockBot"
    form_page_title = "Editar Produto"
    form_page_subtitle = "Atualize as informações do produto"