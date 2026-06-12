"""Mixins para páginas de formulário unificadas (Crispy + template único)."""

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class RedirectIfAuthenticatedMixin:
    """Redireciona usuários já autenticados (login/cadastro)."""

    redirect_authenticated_to = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            url = self.redirect_authenticated_to or settings.LOGIN_REDIRECT_URL
            return redirect(url)
        return super().dispatch(request, *args, **kwargs)


class AppLoginRequiredMixin(LoginRequiredMixin):
    """Exige login nas páginas internas do StockBot."""

    login_url = "login"


class OwnerScopedMixin:
    """Lista/edita apenas registros do usuário logado; novos cadastros recebem `usuario`."""

    def get_queryset(self):
        qs = super().get_queryset()
        model = qs.model
        if model.__name__ == "Movimentacao":
            return qs.filter(produto__usuario=self.request.user)
        if hasattr(model, "usuario"):
            return qs.filter(usuario=self.request.user)
        return qs

    def form_valid(self, form):
        instance = getattr(form, "instance", None)
        if instance is not None and hasattr(instance, "usuario_id"):
            instance.usuario = self.request.user
        return super().form_valid(form)


class ModelFormPageMixin:
    """
    Contexto compartilhado para `model_form_page.html` + `components/forms.html`.
    Views devem definir títulos; `form_variant` controla o layout do cartão/formulário.
    """

    template_name = "model_form_page.html"

    form_page_block_title = "StockBot"
    form_page_title = ""
    form_page_subtitle = ""
    # default | offset_subtitle | hero | delete
    form_variant = "default"
    # Largura do wrapper externo (max-w-2xl, min-h-screen..., etc.)
    form_outer_shell_class = "max-w-2xl mx-auto"
    # Cabeçalho da página: stacked (padrão) | offset (movimentações)
    form_header_style = "stacked"
    # delete: URL do botão cancelar (link)
    form_delete_cancel_url = ""
    # True em login/cadastro: layout sem sidebar e header do painel
    auth_layout = False

    def get_form_submit_label(self):
        return getattr(self, "form_submit_label", None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "form_page_block_title": self.form_page_block_title,
                "form_page_title": self.form_page_title,
                "form_page_subtitle": self.form_page_subtitle,
                "form_variant": self.form_variant,
                "form_outer_shell_class": self.form_outer_shell_class,
                "form_delete_cancel_url": self.form_delete_cancel_url,
                "form_header_style": self.form_header_style,
                "auth_layout": getattr(self, "auth_layout", False),
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        label = self.get_form_submit_label()
        if label:
            kwargs["submit_label"] = label
        request = getattr(self, "request", None)
        if request and request.user.is_authenticated:
            kwargs["user"] = request.user
        return kwargs


class DeleteConfirmPageMixin:
    """Página de confirmação de exclusão (sem ModelForm Crispy)."""

    template_name = "model_form_page.html"
    form_page_block_title = "StockBot"
    form_page_title = ""
    form_page_subtitle = ""
    form_variant = "delete"
    form_outer_shell_class = "max-w-lg mx-auto"
    form_delete_cancel_url = ""
    form_delete_extra_message = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "form_page_block_title": self.form_page_block_title,
                "form_page_title": self.form_page_title,
                "form_page_subtitle": self.form_page_subtitle,
                "form_variant": self.form_variant,
                "form_outer_shell_class": self.form_outer_shell_class,
                "form_delete_cancel_url": self.form_delete_cancel_url,
                "form_delete_extra_message": self.form_delete_extra_message,
            }
        )
        return context
