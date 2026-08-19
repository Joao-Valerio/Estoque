"""Dados agregados para gráficos Chart.js (por usuário)."""

from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import Movimentacao, Produto
from .relatorio_filtros import FiltroRelatorio

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


def dados_movimento_diario(user, *, dias=7, filtro=None):
    """Soma de unidades de entrada e saída por dia."""
    if filtro:
        dias = filtro.dias_grafico_linha()
        base = filtro.aplicar_movimentacoes(Movimentacao.objects.do_usuario(user))
    else:
        base = Movimentacao.objects.do_usuario(user)

    hoje = timezone.localdate()
    inicio = hoje - timedelta(days=dias - 1)
    labels = []
    entrada = []
    saida = []
    tem_dado = False

    for offset in range(dias - 1, -1, -1):
        dia = hoje - timedelta(days=offset)
        if dia < inicio:
            continue
        if dias <= 7:
            labels.append(_DIAS_SEMANA[dia.weekday()])
        else:
            labels.append(dia.strftime("%d/%m"))
        qs = base.filter(data__date=dia)
        e = qs.filter(tipo="E").aggregate(total=Sum("quantidade"))["total"] or 0
        s = qs.filter(tipo="S").aggregate(total=Sum("quantidade"))["total"] or 0
        entrada.append(e)
        saida.append(s)
        if e or s:
            tem_dado = True

    return {
        "labels": labels,
        "entrada": entrada,
        "saida": saida,
        "placeholder": not tem_dado,
    }


def dados_top_produtos_movimentados(user, *, limit=5, filtro=None):
    """Top produtos por quantidade total movimentada (entradas + saídas)."""
    base = Movimentacao.objects.do_usuario(user)
    if filtro:
        base = filtro.aplicar_movimentacoes(base)
    rows = (
        base.values("produto__nome")
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


def top_produtos_vendidos_painel(user, *, limit=5):
    """Top produtos por unidades vendidas (movimentações de saída)."""
    rows = list(
        Movimentacao.objects.do_usuario(user)
        .filter(tipo="S")
        .values("produto_id", "produto__nome")
        .annotate(total=Sum("quantidade"))
        .order_by("-total")[:limit]
    )
    if not rows or not (rows[0]["total"] or 0):
        return []

    max_total = rows[0]["total"] or 1
    itens = []
    for r in rows:
        qtd = r["total"] or 0
        if qtd <= 0:
            continue
        itens.append(
            {
                "produto_id": r["produto_id"],
                "nome": r["produto__nome"] or "Sem nome",
                "quantidade": int(qtd),
                "percentual": max(5, round((qtd / max_total) * 100)),
            }
        )
    return itens


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


def dados_valor_estoque_mensal(user, *, meses=12, filtro=None):
    """
    Valor em estoque (Σ qtd × preço) ao fim de cada mês,
    estimado revertendo movimentações a partir do estoque atual.
    """
    if filtro:
        meses = filtro.meses_grafico_valor()

    produtos_qs = Produto.objects.do_usuario(user)
    if filtro:
        produtos_qs = filtro.aplicar_produtos(produtos_qs)
    produtos = list(produtos_qs)
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

    movs_qs = Movimentacao.objects.do_usuario(user).order_by("-data")
    if filtro:
        movs_qs = filtro.aplicar_movimentacoes(movs_qs)
    movs = list(movs_qs)
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
