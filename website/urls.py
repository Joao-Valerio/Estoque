from django.urls import path
from .views import HomePageView, ModeloPageView, PainelPageView, RelatoriosPageView, ProdutosPageView, EstoquePageView, RelatorioPageView, PerfilPageView, ConfiguracoesPageView, ContatoPageView, FornecedoresPageView
from .views import CreateProdutoPageView, CreateCategoriaPageView, CreateMovimentacaoPageView, CreateFornecedorPageView, UpdateFornecedorPageView, DeleteFornecedorView
from .views import UpdateProdutoPageView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("modelo/", ModeloPageView.as_view(), name="modelo"),
    path("painel/", PainelPageView.as_view(), name="painel"),
    path("relatorios/", RelatoriosPageView.as_view(), name="relatorios"),
    path("produtos/", ProdutosPageView.as_view(), name="produtos"),
    path("estoque/", EstoquePageView.as_view(), name="estoque"),
    path("fornecedores/", FornecedoresPageView.as_view(), name="fornecedores"),
    path("relatorio/", RelatorioPageView.as_view(), name="relatorio"),
    path("perfil/", PerfilPageView.as_view(), name="perfil"),
    path("configuracoes/", ConfiguracoesPageView.as_view(), name="configuracoes"),
    path("contato/", ContatoPageView.as_view(), name="contato"),
    path("produto/novo/", CreateProdutoPageView.as_view(), name="create_produto"),
    path("categoria/novo/", CreateCategoriaPageView.as_view(), name="create_categoria"),
    path("movimentacao/novo/", CreateMovimentacaoPageView.as_view(), name="create_movimentacao"),
    path("fornecedor/novo/", CreateFornecedorPageView.as_view(), name="create_fornecedor"),
    path("fornecedor/editar/<int:pk>/", UpdateFornecedorPageView.as_view(), name="update_fornecedor"),
    path("fornecedor/excluir/<int:pk>/", DeleteFornecedorView.as_view(), name="delete_fornecedor"),
    path("produto/editar/<int:pk>/", UpdateProdutoPageView.as_view(), name="update_produto"),   
    
]