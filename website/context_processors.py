"""Contexto global para templates (ex.: item ativo na sidebar)."""


def navigation(request):
    """
    Define `nav_section` conforme `request.resolver_match.url_name`,
    para destacar o link certo na sidebar (inclui sub-rotas de criação).
    """
    match = getattr(request, "resolver_match", None)
    name = (match.url_name or "") if match else ""

    section = ""
    if name in ("painel",):
        section = "painel"
    elif name in ("produtos", "create_produto", "create_categoria"):
        section = "produtos"
    elif name in ("estoque", "create_estoque", "create_movimentacao"):
        section = "estoque"
    elif name in ("relatorios", "relatorio"):
        section = "relatorios"
    elif name in ("fornecedores", "create_fornecedor", "update_fornecedor", "delete_fornecedor"):
        section = "fornecedores"
    elif name in ("configuracoes", "perfil"):
        section = "configuracoes"
    elif name in ("contato",):
        section = "contato"

    return {"nav_section": section}
