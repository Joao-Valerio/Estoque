"""
Layouts Crispy Forms reutilizáveis (labels + ícones + ações) alinhados ao visual StockBot.
"""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, HTML, Layout


def _actions_row(
    *,
    submit_label: str,
    submit_extra_class: str = "",
    submit_icon: bool = True,
) -> HTML:
    icon = (
        '<ion-icon name="checkmark-circle" class="text-lg"></ion-icon>'
        if submit_icon
        else ""
    )
    extra = f" {submit_extra_class}" if submit_extra_class else ""
    return HTML(
        f"""
        <div class="flex gap-3 pt-6 border-t border-sand-100">
            <button type="button" onclick="window.history.back()" class="btn-secondary flex-1">Cancelar</button>
            <button type="submit" class="btn-primary flex flex-1 items-center justify-center gap-2{extra}">
                {icon}
                {submit_label}
            </button>
        </div>
        """
    )


def _lbl(field: str, icon: str, text: str) -> HTML:
    return HTML(
        f"""
        <label for="{{{{ form.{field}.id_for_label }}}}" class="block text-sm font-medium text-sand-900 mb-2">
            <ion-icon name="{icon}" class="text-lg align-middle"></ion-icon>
            {text}
        </label>
        """
    )


def produto_layout(*, submit_label: str, submit_extra_class: str = "") -> Layout:
    return Layout(
        _lbl("nome", "text", "Nome do Produto *"),
        Field("nome", wrapper_class=""),
        _lbl("descricao", "document-text", "Descrição *"),
        Field("descricao", wrapper_class=""),
        Div(
            HTML(
                """
                <label for="{{ form.preco.id_for_label }}" class="block text-sm font-semibold text-sand-900">
                    <ion-icon name="cash" class="text-lg align-middle"></ion-icon>
                    Valor do produto (R$) *
                </label>
                <p class="text-xs text-sand-600">Preço unitário de venda. Use ponto para centavos (ex.: 19.90).</p>
                """
            ),
            Div(
                HTML(
                    """
                    <span class="flex items-center rounded-lg border border-sand-200 bg-white px-3 text-sand-700 font-medium shrink-0">
                        R$
                    </span>
                    """
                ),
                Field("preco", wrapper_class="flex-1 min-w-0"),
                css_class="flex items-stretch gap-2",
            ),
            css_class="rounded-xl border-2 border-stone-200 bg-sand-50 p-4 space-y-2",
        ),
        _lbl("quantidade", "cube", "Quantidade em estoque *"),
        Field("quantidade", wrapper_class=""),
        _lbl(
            "quantidade_minima",
            "alert-circle-outline",
            "Quantidade mínima (alerta de estoque baixo)",
        ),
        Field("quantidade_minima", wrapper_class=""),
        _lbl("categoria", "list", "Categoria *"),
        Field("categoria", wrapper_class=""),
        _lbl("fornecedor", "business", "Fornecedor"),
        Field("fornecedor", wrapper_class=""),
        _actions_row(
            submit_label=submit_label, submit_extra_class=submit_extra_class
        ),
    )


def categoria_layout(*, submit_label: str) -> Layout:
    return Layout(
        _lbl("nome", "text", "Nome da Categoria *"),
        Field("nome", wrapper_class=""),
        _lbl("descricao", "document-text", "Descrição *"),
        Field("descricao", wrapper_class=""),
        _actions_row(submit_label=submit_label),
    )


def fornecedor_layout(*, submit_label: str) -> Layout:
    return Layout(
        _lbl("nome", "business", "Nome do Fornecedor *"),
        Field("nome", wrapper_class=""),
        _lbl("email", "mail", "Email *"),
        Field("email", wrapper_class=""),
        _lbl("telefone", "call", "Telefone *"),
        Field("telefone", wrapper_class=""),
        _lbl("endereco", "location", "Endereço *"),
        Field("endereco", wrapper_class=""),
        _actions_row(submit_label=submit_label),
    )


def movimentacao_entrada_layout(*, submit_label: str) -> Layout:
    return Layout(
        _lbl("produto", "cube", "Produto *"),
        Field("produto", wrapper_class=""),
        _lbl("fornecedor", "business", "Fornecedor (pedido) *"),
        Field("fornecedor", wrapper_class=""),
        _lbl("quantidade", "layers", "Quantidade recebida *"),
        Field("quantidade", wrapper_class=""),
        _lbl("observacao", "document-text", "Observação"),
        Field("observacao", wrapper_class=""),
        _actions_row(
            submit_label=submit_label,
            submit_extra_class="bg-green-700 hover:bg-green-800",
        ),
    )


def movimentacao_saida_layout(*, submit_label: str) -> Layout:
    return Layout(
        _lbl("produto", "cube", "Produto *"),
        Field("produto", wrapper_class=""),
        _lbl("destinatario", "person", "Destinatário (cliente) *"),
        Field("destinatario", wrapper_class=""),
        _lbl("quantidade", "layers", "Quantidade vendida *"),
        Field("quantidade", wrapper_class=""),
        _lbl("observacao", "document-text", "Observação"),
        Field("observacao", wrapper_class=""),
        _actions_row(submit_label=submit_label),
    )


def produto_hero_layout(*, submit_label: str) -> Layout:
    """Mesmos campos que produto, sem bloco destacado de preço (layout hero usa card externo)."""
    return Layout(
        _lbl("nome", "text", "Nome do Produto *"),
        Field("nome", wrapper_class=""),
        _lbl("descricao", "document-text", "Descrição *"),
        Field("descricao", wrapper_class=""),
        _lbl("preco", "cash", "Preço (R$) *"),
        Field("preco", wrapper_class=""),
        _lbl("quantidade", "cube", "Quantidade em estoque *"),
        Field("quantidade", wrapper_class=""),
        _lbl(
            "quantidade_minima",
            "alert-circle-outline",
            "Quantidade mínima (alerta de estoque baixo)",
        ),
        Field("quantidade_minima", wrapper_class=""),
        _lbl("categoria", "list", "Categoria *"),
        Field("categoria", wrapper_class=""),
        _lbl("fornecedor", "business", "Fornecedor"),
        Field("fornecedor", wrapper_class=""),
        HTML(
            f"""
            <div class="flex items-center justify-end gap-4 pt-6">
                <button type="button" onclick="window.history.back()"
                    class="px-5 py-3 rounded-xl border border-sand-300 text-sand-700 hover:bg-sand-100 transition">
                    Cancelar
                </button>
                <button type="submit"
                    class="px-6 py-3 rounded-xl bg-sand-900 text-white font-semibold hover:bg-sand-800 transition shadow-lg hover:scale-[1.02]">
                    {submit_label}
                </button>
            </div>
            """
        ),
    )


def attach_helper(
    helper: FormHelper,
    layout: Layout,
    *,
    form_class: str = "space-y-6",
) -> None:
    helper.form_tag = False
    helper.form_show_labels = False
    helper.form_class = form_class
    helper.field_class = "mb-0"
    helper.layout = layout
