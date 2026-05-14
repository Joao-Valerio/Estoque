"""Mixins para páginas de formulário unificadas (Crispy + template único)."""


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
            }
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        label = self.get_form_submit_label()
        if label:
            kwargs["submit_label"] = label
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
            }
        )
        return context
