from django.contrib import admin
from .models import Produto, Categoria, Movimentacao, Fornecedor

admin.site.register(Categoria)
admin.site.register(Fornecedor)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        "data",
        "tipo",
        "produto",
        "quantidade",
        "fornecedor",
        "destinatario",
    )
    list_filter = ("tipo",)
    search_fields = ("produto__nome", "destinatario", "observacao")
    date_hierarchy = "data"