from django import forms
from crispy_forms.helper import FormHelper

from .crispy_layouts import (
    attach_helper,
    categoria_layout,
    fornecedor_layout,
    movimentacao_entrada_layout,
    movimentacao_saida_layout,
    produto_hero_layout,
    produto_layout,
)
from .models import (
    Produto,
    Categoria,
    Movimentacao,
    Fornecedor,
)


INPUT_CLASSES = "input-field"
TEXTAREA_CLASSES = "input-field h-24 resize-none"


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "nome",
            "descricao",
            "preco",
            "quantidade",
            "quantidade_minima",
            "categoria",
            "fornecedor",
        ]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "Ex.: Notebook Dell"}
            ),
            "descricao": forms.Textarea(
                attrs={"class": TEXTAREA_CLASSES, "placeholder": "Descrição do produto..."}
            ),
            "preco": forms.NumberInput(
                attrs={
                    "class": f"{INPUT_CLASSES} text-base",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "inputmode": "decimal",
                }
            ),
            "quantidade": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "0",
                    "min": "0",
                    "inputmode": "numeric",
                }
            ),
            "quantidade_minima": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "15",
                    "min": "0",
                    "inputmode": "numeric",
                }
            ),
            "categoria": forms.Select(attrs={"class": INPUT_CLASSES}),
            "fornecedor": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, submit_label="Criar Produto", **kwargs):
        submit_extra_class = kwargs.pop("submit_extra_class", "")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        attach_helper(
            self.helper,
            produto_layout(
                submit_label=submit_label,
                submit_extra_class=submit_extra_class,
            ),
        )


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome", "descricao"]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "Ex.: Eletrônicos"}
            ),
            "descricao": forms.Textarea(
                attrs={"class": TEXTAREA_CLASSES, "placeholder": "Descrição da categoria..."}
            ),
        }

    def __init__(self, *args, submit_label="Criar Categoria", **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        attach_helper(self.helper, categoria_layout(submit_label=submit_label))


class MovimentacaoEntradaForm(forms.ModelForm):
    """Entrada de estoque (ex.: pedido ao fornecedor)."""

    class Meta:
        model = Movimentacao
        fields = ["produto", "fornecedor", "quantidade", "observacao"]
        widgets = {
            "produto": forms.Select(attrs={"class": INPUT_CLASSES}),
            "fornecedor": forms.Select(attrs={"class": INPUT_CLASSES}),
            "quantidade": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "0",
                    "min": "1",
                    "inputmode": "numeric",
                }
            ),
            "observacao": forms.Textarea(
                attrs={
                    "class": TEXTAREA_CLASSES,
                    "placeholder": "Nº do pedido, nota fiscal, etc.",
                }
            ),
        }

    def __init__(self, *args, submit_label="Confirmar entrada", **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        attach_helper(
            self.helper, movimentacao_entrada_layout(submit_label=submit_label)
        )

    def clean_quantidade(self):
        q = self.cleaned_data.get("quantidade")
        if q is not None and q < 1:
            raise forms.ValidationError("Informe uma quantidade maior ou igual a 1.")
        return q

    def clean_fornecedor(self):
        fornecedor = self.cleaned_data.get("fornecedor")
        if not fornecedor:
            raise forms.ValidationError("Selecione o fornecedor do pedido.")
        return fornecedor


class MovimentacaoSaidaForm(forms.ModelForm):
    """Saída de estoque (ex.: venda a um destinatário)."""

    class Meta:
        model = Movimentacao
        fields = ["produto", "destinatario", "quantidade", "observacao"]
        widgets = {
            "produto": forms.Select(attrs={"class": INPUT_CLASSES}),
            "destinatario": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Nome do cliente ou destinatário",
                }
            ),
            "quantidade": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "0",
                    "min": "1",
                    "inputmode": "numeric",
                }
            ),
            "observacao": forms.Textarea(
                attrs={
                    "class": TEXTAREA_CLASSES,
                    "placeholder": "Observações da venda (opcional)",
                }
            ),
        }

    def __init__(self, *args, submit_label="Confirmar saída", **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        attach_helper(self.helper, movimentacao_saida_layout(submit_label=submit_label))

    def clean_quantidade(self):
        q = self.cleaned_data.get("quantidade")
        if q is not None and q < 1:
            raise forms.ValidationError("Informe uma quantidade maior ou igual a 1.")
        return q

    def clean_destinatario(self):
        nome = (self.cleaned_data.get("destinatario") or "").strip()
        if not nome:
            raise forms.ValidationError("Informe o destinatário da venda.")
        return nome


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ["nome", "email", "telefone", "endereco"]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "Ex.: Fornecedor X Ltda."}
            ),
            "email": forms.EmailInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "contato@empresa.com"}
            ),
            "telefone": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "(00) 00000-0000"}
            ),
            "endereco": forms.Textarea(
                attrs={"class": TEXTAREA_CLASSES, "placeholder": "Endereço completo..."}
            ),
        }

    def __init__(self, *args, submit_label="Criar Fornecedor", **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        attach_helper(self.helper, fornecedor_layout(submit_label=submit_label))


class UpdateProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "nome",
            "descricao",
            "preco",
            "quantidade",
            "quantidade_minima",
            "categoria",
            "fornecedor",
        ]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "Ex.: Notebook Dell"}
            ),
            "descricao": forms.Textarea(
                attrs={"class": TEXTAREA_CLASSES, "placeholder": "Descrição do produto..."}
            ),
            "preco": forms.NumberInput(
                attrs={
                    "class": f"{INPUT_CLASSES} text-base",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "inputmode": "decimal",
                }
            ),
            "quantidade": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "0",
                    "min": "0",
                    "inputmode": "numeric",
                }
            ),
            "quantidade_minima": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "15",
                    "min": "0",
                    "inputmode": "numeric",
                }
            ),
            "categoria": forms.Select(attrs={"class": INPUT_CLASSES}),
            "fornecedor": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, submit_label="Salvar Alterações", **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        attach_helper(self.helper, produto_hero_layout(submit_label=submit_label))
