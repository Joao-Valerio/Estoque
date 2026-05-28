"""Alertas de estoque (sem estoque / estoque baixo) por usuário."""

from django.db.models import F

from .models import Produto

_NIVEL_SEM_ESTOQUE = "out"
_NIVEL_ESTOQUE_BAIXO = "low"

_ESTILOS = {
    _NIVEL_SEM_ESTOQUE: {
        "card_class": "bg-red-50 border-red-200",
        "icon": "close-circle",
        "icon_class": "text-red-600",
        "title_class": "text-red-900",
        "text_class": "text-red-700",
    },
    _NIVEL_ESTOQUE_BAIXO: {
        "card_class": "bg-yellow-50 border-yellow-200",
        "icon": "warning",
        "icon_class": "text-yellow-600",
        "title_class": "text-yellow-900",
        "text_class": "text-yellow-700",
    },
}


def _alerta_dict(produto, *, nivel: str, status: str) -> dict:
    estilo = _ESTILOS[nivel]
    return {
        "produto_id": produto.pk,
        "nome": produto.nome,
        "status": status,
        "quantidade": produto.quantidade,
        "quantidade_minima": produto.quantidade_minima,
        "nivel": nivel,
        **estilo,
    }


def alertas_estoque_usuario(user, *, limit=50):
    """
    Notificações quando produto está sem estoque ou abaixo do mínimo.
    Ordem: sem estoque primeiro, depois estoque baixo (nome A–Z).
    """
    if not user or not user.is_authenticated:
        return []

    base = Produto.objects.filter(usuario=user)
    alertas = []

    for produto in base.filter(quantidade=0).order_by("nome")[:limit]:
        alertas.append(
            _alerta_dict(produto, nivel=_NIVEL_SEM_ESTOQUE, status="Sem estoque")
        )

    restante = limit - len(alertas)
    if restante > 0:
        for produto in (
            base.filter(quantidade__gt=0, quantidade__lte=F("quantidade_minima"))
            .order_by("nome")[:restante]
        ):
            alertas.append(
                _alerta_dict(produto, nivel=_NIVEL_ESTOQUE_BAIXO, status="Estoque baixo")
            )

    return alertas
