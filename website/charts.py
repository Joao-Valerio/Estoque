"""Dados agregados para gráficos Chart.js (por usuário)."""

from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import Movimentacao, Produto


def _movimentacoes_do_usuario(user):
    return Movimentacao.objects.filter(produto__usuario=user)


def _produtos_do_usuario(user):
    return Produto.objects.filter(usuario=user)

_MESES_CURTOS = (
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
)
_DIAS_SEMANA = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")


def dados_movimento_diario(user, *, dias=7):
    """Soma de unidades de entrada e saída por dia (últimos N dias)."""
    hoje = timezone.localdate()
    labels = []
    entrada = []
    saida = []
    base = _movimentacoes_do_usuario(user)

    for offset in range(dias - 1, -1, -1):
        dia = hoje - timedelta(days=offset)
        labels.append(_DIAS_SEMANA[dia.weekday()])
        qs = base.filter(data__date=dia)
        entrada.append(
            qs.filter(tipo="E").aggregate(total=Sum("quantidade"))["total"] or 0
        )
        saida.append(
            qs.filter(tipo="S").aggregate(total=Sum("quantidade"))["total"] or 0
        )

    return {
        "labels": labels,
        "entrada": entrada,
        "saida": saida,
        "placeholder": not base.exists(),
    }


def dados_top_produtos_movimentados(user, *, limit=5):
    """Top produtos por quantidade total movimentada (entradas + saídas)."""
    rows = (
        _movimentacoes_do_usuario(user)
        .values("produto__nome")
        .annotate(total=Sum("quantidade"))
        .order_by("-total")[:limit]
    )
    labels = []
    values = []
    for r in rows:
        nome = r["produto__nome"] or "Sem nome"
        total = r["total"] or 0
        if total > 0:
            labels.append(nome)
            values.append(int(total))

    if not labels:
        return {
            "labels": ["Nenhuma movimentação"],
            "values": [0],
            "placeholder": True,
        }
    return {"labels": labels, "values": values, "placeholder": False}


def _ultimos_periodos_meses(quantidade: int):
    agora = timezone.localdate()
    y, m = agora.year, agora.month
    periodos = []
    for _ in range(quantidade):
        periodos.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    periodos.reverse()
    return periodos


def dados_valor_estoque_mensal(user, *, meses=12):
    """
    Valor em estoque (Σ qtd × preço) ao fim de cada mês,
    estimado revertendo movimentações a partir do estoque atual.
    """
    produtos = list(_produtos_do_usuario(user))
    periodos = _ultimos_periodos_meses(meses)

    if not produtos:
        return {
            "labels": [_MESES_CURTOS[m - 1] for _, m in periodos],
            "values": [0.0] * len(periodos),
            "placeholder": True,
        }

    qty = {p.pk: p.quantidade for p in produtos}
    preco = {p.pk: float(p.preco) for p in produtos}

    def valor_atual():
        return round(
            sum(max(0, qty.get(pk, 0)) * preco.get(pk, 0) for pk in preco), 2
        )

    movs = list(_movimentacoes_do_usuario(user).order_by("-data"))
    valores_rev = []

    for y, m in reversed(periodos):
        valores_rev.append(valor_atual())
        for mov in movs:
            if mov.data.year != y or mov.data.month != m:
                continue
            pk = mov.produto_id
            if pk not in qty:
                continue
            if mov.tipo == "E":
                qty[pk] -= mov.quantidade
            else:
                qty[pk] += mov.quantidade

    valores = list(reversed(valores_rev))
    placeholder = not movs and valor_atual() == 0

    return {
        "labels": [_MESES_CURTOS[m - 1] for _, m in periodos],
        "values": valores,
        "placeholder": placeholder,
    }
