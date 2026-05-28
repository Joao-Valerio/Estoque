from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import (
    Case,
    CharField,
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
    Value,
    When,
    Q,
)
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    TemplateView,
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    FormView,
)

from .forms import (
    ProdutoForm,
    CategoriaForm,
    MovimentacaoEntradaForm,
    MovimentacaoSaidaForm,
    FornecedorForm,
    UpdateProdutoForm,
    CadastroUsuarioForm,
    LoginForm,
    PerfilNomeForm,
    PerfilEmailForm,
    PerfilSenhaForm,
    ExcluirContaForm,
)
from .models import (
    Produto,
    Categoria,
    Movimentacao,
    Fornecedor,
)
from .mixins import (
    AppLoginRequiredMixin,
    DeleteConfirmPageMixin,
    ModelFormPageMixin,
    OwnerScopedMixin,
    RedirectIfAuthenticatedMixin,
)
from .formatting import formatar_brl
from .charts import (
    dados_movimento_diario,
    dados_top_produtos_movimentados,
    dados_valor_estoque_mensal,
)


def produtos_do_usuario(user):
    return Produto.objects.filter(usuario=user)


def categorias_do_usuario(user):
    return Categoria.objects.filter(usuario=user)


def fornecedores_do_usuario(user):
    return Fornecedor.objects.filter(usuario=user)


def movimentacoes_do_usuario(user):
    return Movimentacao.objects.filter(produto__usuario=user)


def _estoque_status_opcoes_do_banco(user):
    """
    Slugs de status presentes nos produtos (regra: qtd = sem estoque;
    0 < qtd <= mínimo = baixo; senão = ok). Se não houver produtos, lista os três.
    """
    labels = {
        "ok": "Em Estoque",
        "low": "Estoque Baixo",
        "out": "Sem Estoque",
    }
    order = ("ok", "low", "out")
    slugs = set(
        produtos_do_usuario(user).annotate(
            status_slug=Case(
                When(quantidade=0, then=Value("out")),
                When(quantidade__lte=F("quantidade_minima"), then=Value("low")),
                default=Value("ok"),
                output_field=CharField(),
            )
        ).values_list("status_slug", flat=True)
    )
    if not slugs:
        slugs = set(order)
    return [{"value": s, "label": labels[s]} for s in order if s in slugs]


def _movimentacao_tipos_relatorio(user):
    """
    Entrada (E) e Saída (S) a partir de Movimentacao no banco.
    Sem registros: lista as duas opções do modelo (TIPOS).
    """
    labels = dict(Movimentacao.TIPOS)
    order = ("E", "S")
    found = set(
        movimentacoes_do_usuario(user).values_list("tipo", flat=True).distinct()
    )
    if not found:
        found = set(order)
    return [{"id": code, "nome": labels[code]} for code in order if code in found]


def _categoria_distribuicao_estoque(user):
    """
    Distribuição do valor em estoque por categoria (Σ quantidade × preço unitário).
    Retorna dict com labels, values (float) e flag placeholder quando não há dados.
    """
    rows = (
        produtos_do_usuario(user).values("categoria__nome")
        .annotate(
            total_valor=Sum(
                ExpressionWrapper(
                    F("quantidade") * F("preco"),
                    output_field=DecimalField(max_digits=16, decimal_places=2),
                )
            )
        )
        .order_by("categoria__nome")
    )
    labels = []
    values = []
    for r in rows:
        nome = r["categoria__nome"] or "Sem nome"
        v = r["total_valor"] or Decimal("0")
        if v > 0:
            labels.append(nome)
            values.append(float(v))
    if not labels:
        return {
            "labels": ["Sem valor em estoque"],
            "values": [1.0],
            "placeholder": True,
        }
    return {"labels": labels, "values": values, "placeholder": False}


def _movimentacoes_recentes(user, limit=15, *, annotate_valor_mov=False):
    """
    Últimas movimentações (produto/fornecedor em join).
    Com annotate_valor_mov=True, acrescenta quantidade × preço unitário atual.
    """
    qs = movimentacoes_do_usuario(user).select_related("produto", "fornecedor")
    if annotate_valor_mov:
        qs = qs.annotate(
            valor_mov=ExpressionWrapper(
                F("quantidade") * F("produto__preco"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
    return qs.order_by("-data")[:limit]


class DashboardContextMixin:

    def get_dashboard_context(self):
        user = self.request.user
        produtos = produtos_do_usuario(user)
        total = (
            produtos.annotate(
                subtotal=F("quantidade") * F("preco")
            ).aggregate(
                total=Sum("subtotal")
            )["total"]
        )

        estoque_baixo = produtos.filter(
            quantidade__gt=0,
            quantidade__lte=F("quantidade_minima")
        )

        em_estoque = produtos.filter(
            quantidade__gt=0
        )

        vt = total or Decimal("0")
        return {
            "produtos_count": produtos.count(),

            "sem_estoque_count": produtos.filter(
                quantidade=0
            ).count(),

            "estoque_baixo_count": estoque_baixo.count(),

            "estoque_baixo": estoque_baixo,

            "em_estoque_count": em_estoque.count(),

            "em_estoque": em_estoque,

            "valor_total": vt,
            "valor_total_brl": formatar_brl(vt),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_dashboard_context())
        return context


class ProdutosPageView(AppLoginRequiredMixin, TemplateView):
    template_name = "produtos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = produtos_do_usuario(self.request.user).select_related(
            "categoria", "fornecedor"
        ).order_by("nome")
        busca = self.request.GET.get("q", "").strip()
        categoria_raw = self.request.GET.get("categoria", "").strip()
        categoria_atual = None
        if categoria_raw and categoria_raw.isdigit():
            categoria_atual = int(categoria_raw)
            qs = qs.filter(categoria_id=categoria_atual)
        if busca:
            filtros = Q(nome__icontains=busca)
            if busca.isdigit():
                filtros |= Q(pk=int(busca))
            qs = qs.filter(filtros)
        context["produtos"] = qs
        context["categorias"] = categorias_do_usuario(self.request.user).order_by(
            "nome"
        )
        context["busca_q"] = busca
        context["categoria_atual"] = categoria_atual or categoria_raw

        return context

class HomePageView(TemplateView):
    template_name = "home.html"

class ModeloPageView(AppLoginRequiredMixin, TemplateView):
    template_name = "modelo.html"

class EstoquePageView(AppLoginRequiredMixin, DashboardContextMixin, TemplateView):
    template_name = "estoque.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = produtos_do_usuario(self.request.user).select_related(
            "categoria", "fornecedor"
        ).order_by("nome")
        busca = self.request.GET.get("q", "").strip()
        if busca:
            filtros = Q(nome__icontains=busca)
            if busca.isdigit():
                filtros |= Q(pk=int(busca))
            qs = qs.filter(filtros)
        context["produtos"] = qs
        context["busca_q"] = busca
        context["movimentacoes_count"] = movimentacoes_do_usuario(
            self.request.user
        ).count()
        return context


class FornecedoresPageView(AppLoginRequiredMixin, TemplateView):
    template_name = "fornecedores.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fornecedores"] = fornecedores_do_usuario(self.request.user).order_by(
            "nome"
        )
        return context

class PerfilPageView(AppLoginRequiredMixin, TemplateView):
    template_name = "perfil.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        nome = (user.first_name or "").strip()
        context["perfil_nome"] = nome or "—"
        context["perfil_email"] = user.email or user.username
        return context


class ConfiguracoesPageView(AppLoginRequiredMixin, TemplateView):
    template_name = "configuracoes.html"

class ContatoPageView(AppLoginRequiredMixin, TemplateView):
    template_name = "contato.html"

class PainelPageView(AppLoginRequiredMixin, DashboardContextMixin, TemplateView):
    template_name = "painel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["categorias"] = categorias_do_usuario(user).order_by("nome")
        context["estoque_status_opcoes"] = _estoque_status_opcoes_do_banco(user)
        context["movimentacoes"] = _movimentacoes_recentes(user, 15)
        context["chart_movimento_diario"] = dados_movimento_diario(user)
        return context

class RelatoriosPageView(AppLoginRequiredMixin, TemplateView):
    template_name = "relatorios.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["categorias"] = categorias_do_usuario(user).order_by("nome")
        context["tipos"] = _movimentacao_tipos_relatorio(user)
        context["movimentacoes"] = _movimentacoes_recentes(
            user, 15, annotate_valor_mov=True
        )
        context["movimentacoes_total"] = movimentacoes_do_usuario(user).count()
        context["categoria_distribuicao"] = _categoria_distribuicao_estoque(user)
        context["chart_movimento_diario"] = dados_movimento_diario(user)
        context["chart_top_produtos"] = dados_top_produtos_movimentados(user)
        context["chart_valor_estoque_mensal"] = dados_valor_estoque_mensal(user)
        return context


class CreateProdutoPageView(
    AppLoginRequiredMixin, OwnerScopedMixin, ModelFormPageMixin, CreateView
):
    model = Produto
    form_class = ProdutoForm
    success_url = reverse_lazy("produtos")
    form_page_block_title = "Novo Produto - StockBot"
    form_page_title = "Novo Produto"
    form_page_subtitle = "Cadastre um novo produto no sistema de estoque"


class CreateCategoriaPageView(
    AppLoginRequiredMixin, OwnerScopedMixin, ModelFormPageMixin, CreateView
):
    model = Categoria
    form_class = CategoriaForm
    success_url = reverse_lazy("relatorios")
    form_page_block_title = "Nova Categoria - StockBot"
    form_page_title = "Nova Categoria"
    form_page_subtitle = "Organize seus produtos em categorias"

class MovimentacoesPageView(AppLoginRequiredMixin, OwnerScopedMixin, ListView):
    model = Movimentacao
    template_name = "movimentacoes.html"
    context_object_name = "movimentacoes"
    paginate_by = 25

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("produto", "fornecedor")
            .order_by("-data")
        )


class MovimentacaoHubView(AppLoginRequiredMixin, TemplateView):
    template_name = "movimentacao_hub.html"


class CreateMovimentacaoEntradaView(
    AppLoginRequiredMixin, ModelFormPageMixin, CreateView
):
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
            updated = produtos_do_usuario(self.request.user).filter(
                pk=mov.produto_id
            ).update(quantidade=F("quantidade") + qty)
            if not updated:
                form.add_error(None, "Produto não encontrado.")
                return self.form_invalid(form)
            mov.save()
        self.object = mov
        return redirect(self.get_success_url())


class CreateMovimentacaoSaidaView(
    AppLoginRequiredMixin, ModelFormPageMixin, CreateView
):
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
                produtos_do_usuario(self.request.user)
                .select_for_update()
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
            produtos_do_usuario(self.request.user).filter(pk=prod.pk).update(
                quantidade=F("quantidade") - qty
            )
            mov.save()
        self.object = mov
        return redirect(self.get_success_url())

class CreateFornecedorPageView(
    AppLoginRequiredMixin, OwnerScopedMixin, ModelFormPageMixin, CreateView
):
    model = Fornecedor
    form_class = FornecedorForm
    success_url = reverse_lazy("fornecedores")
    form_page_block_title = "Novo Fornecedor - StockBot"
    form_page_title = "Novo Fornecedor"
    form_page_subtitle = "Cadastre um novo fornecedor"


class UpdateFornecedorPageView(
    AppLoginRequiredMixin, OwnerScopedMixin, ModelFormPageMixin, UpdateView
):
    model = Fornecedor
    form_class = FornecedorForm
    success_url = reverse_lazy("fornecedores")
    form_submit_label = "Salvar alterações"
    form_page_block_title = "Editar Fornecedor - StockBot"
    form_page_title = "Editar Fornecedor"
    form_page_subtitle = "Atualize os dados do fornecedor"


class DeleteFornecedorView(
    AppLoginRequiredMixin, OwnerScopedMixin, DeleteConfirmPageMixin, DeleteView
):
    model = Fornecedor
    success_url = reverse_lazy("fornecedores")
    form_page_block_title = "Excluir Fornecedor - StockBot"
    form_page_title = "Excluir fornecedor"
    form_page_subtitle = "Esta ação não pode ser desfeita."
    form_delete_cancel_url = reverse_lazy("fornecedores")


class UpdateProdutoPageView(
    AppLoginRequiredMixin, OwnerScopedMixin, ModelFormPageMixin, UpdateView
):
    model = Produto
    form_class = UpdateProdutoForm
    success_url = reverse_lazy("produtos")
    form_variant = "hero"
    form_page_block_title = "Editar Produto - StockBot"
    form_page_title = "Editar Produto"
    form_page_subtitle = "Atualize as informações do produto"


# --- Autenticação e conta do usuário ---


class CadastroUsuarioView(RedirectIfAuthenticatedMixin, ModelFormPageMixin, CreateView):
    auth_layout = True
    model = User
    form_class = CadastroUsuarioForm
    success_url = reverse_lazy("painel")
    form_page_block_title = "Cadastro - StockBot"
    form_page_title = "Criar conta"
    form_page_subtitle = "Nome, e-mail e senha para acessar o sistema"
    form_submit_label = "Criar conta"
    form_page_footer = (
        'Já tem conta? <a href="{url}" class="font-medium text-stone-700 hover:underline">Entrar</a>'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_page_footer"] = self.form_page_footer.format(
            url=reverse("login")
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        auth_login(self.request, self.object)
        messages.success(self.request, "Conta criada com sucesso. Bem-vindo!")
        return response


class LoginUsuarioView(RedirectIfAuthenticatedMixin, ModelFormPageMixin, LoginView):
    auth_layout = True
    form_class = LoginForm
    redirect_authenticated_to = reverse_lazy("painel")
    form_page_block_title = "Login - StockBot"
    form_page_title = "Entrar"
    form_page_subtitle = "Use seu e-mail e senha cadastrados"
    form_submit_label = "Entrar"
    form_page_footer = (
        'Não tem conta? <a href="{url}" class="font-medium text-stone-700 hover:underline">Criar conta</a>'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_page_footer"] = self.form_page_footer.format(
            url=reverse("cadastro")
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, "Login realizado com sucesso.")
        return super().form_valid(form)


class LogoutUsuarioView(LogoutView):
    """Logout via GET ou POST (link direto na sidebar)."""

    next_page = reverse_lazy("login")
    http_method_names = ["get", "post", "options", "head"]

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            auth_logout(request)
            messages.info(request, "Você saiu da sua conta.")
        return redirect(self.next_page)


class PerfilNomeUpdateView(AppLoginRequiredMixin, ModelFormPageMixin, FormView):
    form_class = PerfilNomeForm
    success_url = reverse_lazy("perfil")
    form_page_block_title = "Alterar nome - StockBot"
    form_page_title = "Alterar nome"
    form_page_subtitle = "Atualize como seu nome aparece no sistema"
    form_submit_label = "Salvar nome"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Nome atualizado.")
        return super().form_valid(form)


class PerfilEmailUpdateView(AppLoginRequiredMixin, ModelFormPageMixin, FormView):
    form_class = PerfilEmailForm
    success_url = reverse_lazy("perfil")
    form_page_block_title = "Alterar e-mail - StockBot"
    form_page_title = "Alterar e-mail"
    form_page_subtitle = "O e-mail também será usado para fazer login"
    form_submit_label = "Salvar e-mail"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "E-mail atualizado.")
        return super().form_valid(form)


class PerfilSenhaUpdateView(AppLoginRequiredMixin, ModelFormPageMixin, FormView):
    form_class = PerfilSenhaForm
    success_url = reverse_lazy("perfil")
    form_page_block_title = "Alterar senha - StockBot"
    form_page_title = "Alterar senha"
    form_page_subtitle = "Informe a senha atual e defina uma nova senha"
    form_submit_label = "Alterar senha"

    def get_form(self, form_class=None):
        form_class = form_class or self.form_class
        return form_class(self.request.user, **self.get_form_kwargs())

    def form_valid(self, form):
        form.save()
        from django.contrib.auth import update_session_auth_hash

        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "Senha alterada com sucesso.")
        return super().form_valid(form)


class ExcluirContaView(AppLoginRequiredMixin, ModelFormPageMixin, FormView):
    form_class = ExcluirContaForm
    success_url = reverse_lazy("login")
    form_page_block_title = "Excluir conta - StockBot"
    form_page_title = "Excluir conta"
    form_page_subtitle = "Esta ação não pode ser desfeita"
    form_submit_label = "Excluir minha conta"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        auth_logout(self.request)
        user.delete()
        messages.info(self.request, "Sua conta foi excluída.")
        return super().form_valid(form)