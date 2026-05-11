from django import forms

from .models import (
    Produto,
    Categoria,
    Movimentacao,
    Fornecedor,
)


# Classes utilitárias compartilhadas para padronizar o visual dos campos.
# Usamos .input-field (definido em static/css/src/input.css) + utilitários Tailwind.
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


class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ["produto", "tipo", "quantidade", "observacao"]
        widgets = {
            "produto": forms.Select(attrs={"class": INPUT_CLASSES}),
            "tipo": forms.Select(attrs={"class": INPUT_CLASSES}),
            "quantidade": forms.NumberInput(
                attrs={"class": INPUT_CLASSES, "placeholder": "0"}
            ),
            "observacao": forms.Textarea(
                attrs={"class": TEXTAREA_CLASSES, "placeholder": "Observações..."}
            ),
        }


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

class UpdateProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "descricao", "preco", "quantidade", "quantidade_minima", "categoria", "fornecedor"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Ex.: Notebook Dell"}),
            "descricao": forms.Textarea(attrs={"class": TEXTAREA_CLASSES, "placeholder": "Descrição do produto..."}),
            "preco": forms.NumberInput(attrs={"class": f"{INPUT_CLASSES} text-base", "placeholder": "0.00", "step": "0.01", "min": "0", "inputmode": "decimal"}),
            "quantidade": forms.NumberInput(attrs={"class": INPUT_CLASSES, "placeholder": "0", "min": "0", "inputmode": "numeric"}),
            "quantidade_minima": forms.NumberInput(attrs={"class": INPUT_CLASSES, "placeholder": "15", "min": "0", "inputmode": "numeric"}),
            "categoria": forms.Select(attrs={"class": INPUT_CLASSES}),
            "fornecedor": forms.Select(attrs={"class": INPUT_CLASSES}),
        }