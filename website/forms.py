from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper

from .crispy_layouts import (
    attach_helper,
    cadastro_layout,
    categoria_layout,
    excluir_conta_layout,
    fornecedor_layout,
    login_layout,
    movimentacao_entrada_layout,
    movimentacao_saida_layout,
    perfil_email_layout,
    perfil_nome_layout,
    perfil_senha_layout,
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


def _aplicar_querysets_do_usuario(form, user):
    if not user or not getattr(user, "is_authenticated", False):
        return
    if "categoria" in form.fields:
        form.fields["categoria"].queryset = Categoria.objects.filter(usuario=user)
    if "fornecedor" in form.fields:
        form.fields["fornecedor"].queryset = Fornecedor.objects.filter(usuario=user)
    if "produto" in form.fields:
        form.fields["produto"].queryset = Produto.objects.filter(usuario=user)


def _password_widget():
    return forms.PasswordInput(
        attrs={"class": INPUT_CLASSES, "placeholder": "••••••••", "autocomplete": "current-password"}
    )


class CadastroUsuarioForm(UserCreationForm):
    nome = forms.CharField(
        label="Nome",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": INPUT_CLASSES, "placeholder": "Seu nome completo", "autocomplete": "name"}
        ),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"class": INPUT_CLASSES, "placeholder": "seu@email.com", "autocomplete": "email"}
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

    def __init__(self, *args, submit_label="Criar conta", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.update(
                {"class": INPUT_CLASSES, "placeholder": "••••••••", "autocomplete": "new-password"}
            )
        self.helper = FormHelper()
        attach_helper(self.helper, cadastro_layout(submit_label=submit_label))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"].strip().lower()
        user.username = email
        user.email = email
        user.first_name = self.cleaned_data["nome"].strip()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, submit_label="Entrar", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "E-mail"
        self.fields["username"].widget = forms.EmailInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "seu@email.com",
                "autocomplete": "email",
            }
        )
        self.fields["password"].widget = _password_widget()
        self.helper = FormHelper()
        attach_helper(self.helper, login_layout(submit_label=submit_label))

    def clean_username(self):
        email = (self.cleaned_data.get("username") or "").strip().lower()
        if not email:
            return email
        user = User.objects.filter(email__iexact=email).first()
        if user:
            return user.username
        user = User.objects.filter(username__iexact=email).first()
        if user:
            return user.username
        return email


class PerfilNomeForm(forms.Form):
    nome = forms.CharField(
        label="Nome",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": INPUT_CLASSES, "placeholder": "Seu nome", "autocomplete": "name"}
        ),
    )

    def __init__(self, *args, user, submit_label="Salvar nome", **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["nome"].initial = user.first_name
        self.helper = FormHelper()
        attach_helper(self.helper, perfil_nome_layout(submit_label=submit_label))

    def save(self):
        self.user.first_name = self.cleaned_data["nome"].strip()
        self.user.save(update_fields=["first_name"])
        return self.user


class PerfilEmailForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"class": INPUT_CLASSES, "placeholder": "novo@email.com", "autocomplete": "email"}
        ),
    )

    def __init__(self, *args, user, submit_label="Salvar e-mail", **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["email"].initial = user.email
        self.helper = FormHelper()
        attach_helper(self.helper, perfil_email_layout(submit_label=submit_label))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise forms.ValidationError("Este e-mail já está em uso.")
        if (
            User.objects.filter(username__iexact=email)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def save(self):
        email = self.cleaned_data["email"]
        self.user.email = email
        self.user.username = email
        self.user.save(update_fields=["email", "username"])
        return self.user


class PerfilSenhaForm(PasswordChangeForm):
    def __init__(self, *args, submit_label="Alterar senha", **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].widget = _password_widget()
        self.helper = FormHelper()
        attach_helper(self.helper, perfil_senha_layout(submit_label=submit_label))


class ExcluirContaForm(forms.Form):
    senha = forms.CharField(
        label="Senha",
        widget=_password_widget(),
    )

    def __init__(self, *args, user, submit_label="Excluir minha conta", **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        attach_helper(self.helper, excluir_conta_layout(submit_label=submit_label))

    def clean_senha(self):
        senha = self.cleaned_data.get("senha")
        if not self.user.check_password(senha):
            raise forms.ValidationError("Senha incorreta.")
        return senha


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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _aplicar_querysets_do_usuario(self, user)
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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _aplicar_querysets_do_usuario(self, user)
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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _aplicar_querysets_do_usuario(self, user)
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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _aplicar_querysets_do_usuario(self, user)
        self.helper = FormHelper()
        attach_helper(self.helper, produto_hero_layout(submit_label=submit_label))
