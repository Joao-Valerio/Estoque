from django.urls import path
from django.views.generic import RedirectView

from .views import (
    HomePageView,
    ModeloPageView,
    PainelPageView,
    RelatoriosPageView,
    ProdutosPageView,
    EstoquePageView,
    RelatorioPageView,
    PerfilPageView,
    ConfiguracoesPageView,
    ContatoPageView,
    FornecedoresPageView,
    MovimentacoesPageView,
    MovimentacaoHubView,
    CreateMovimentacaoEntradaView,
    CreateMovimentacaoSaidaView,
    CreateProdutoPageView,
    CreateCategoriaPageView,
    CreateFornecedorPageView,
    UpdateFornecedorPageView,
    DeleteFornecedorView,
    UpdateProdutoPageView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("modelo/", ModeloPageView.as_view(), name="modelo"),
    path("painel/", PainelPageView.as_view(), name="painel"),
    path("relatorios/", RelatoriosPageView.as_view(), name="relatorios"),
    path("produtos/", ProdutosPageView.as_view(), name="produtos"),
    path("estoque/", EstoquePageView.as_view(), name="estoque"),
    path("movimentacoes/", MovimentacoesPageView.as_view(), name="movimentacoes"),
    path("movimentacao/", MovimentacaoHubView.as_view(), name="movimentacao_hub"),
    path(
        "movimentacao/novo/",
        RedirectView.as_view(pattern_name="movimentacao_hub", permanent=False),
        name="create_movimentacao",
    ),
    path(
        "movimentacao/entrada/",
        CreateMovimentacaoEntradaView.as_view(),
        name="create_movimentacao_entrada",
    ),
    path(
        "movimentacao/saida/",
        CreateMovimentacaoSaidaView.as_view(),
        name="create_movimentacao_saida",
    ),
    path("fornecedores/", FornecedoresPageView.as_view(), name="fornecedores"),
    path("relatorio/", RelatorioPageView.as_view(), name="relatorio"),
    path("perfil/", PerfilPageView.as_view(), name="perfil"),
    path("configuracoes/", ConfiguracoesPageView.as_view(), name="configuracoes"),
    path("contato/", ContatoPageView.as_view(), name="contato"),
    path("produto/novo/", CreateProdutoPageView.as_view(), name="create_produto"),
    path("categoria/novo/", CreateCategoriaPageView.as_view(), name="create_categoria"),
    path("fornecedor/novo/", CreateFornecedorPageView.as_view(), name="create_fornecedor"),
    path("fornecedor/editar/<int:pk>/", UpdateFornecedorPageView.as_view(), name="update_fornecedor"),
    path("fornecedor/excluir/<int:pk>/", DeleteFornecedorView.as_view(), name="delete_fornecedor"),
    path("produto/editar/<int:pk>/", UpdateProdutoPageView.as_view(), name="update_produto"),   
    
]