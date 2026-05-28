"""Filtros GET da página de relatórios."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.utils import timezone

PERIODO_OPCOES = (
    ("7d", "Últimos 7 dias"),
    ("30d", "Últimos 30 dias"),
    ("3m", "Últimos 3 meses"),
    ("6m", "Últimos 6 meses"),
    ("ano", "Este ano"),
)
_PERIODO_VALIDOS = {c for c, _ in PERIODO_OPCOES}
_DIAS_PERIODO = {"7d": 7, "30d": 30, "3m": 90, "6m": 180}


@dataclass
class FiltroRelatorio:
    periodo: str = "30d"
    categoria_id: int | None = None
    tipo: str = ""

    @classmethod
    def from_request(cls, request):
        periodo = (request.GET.get("periodo") or "30d").strip()
        if periodo not in _PERIODO_VALIDOS:
            periodo = "30d"

        cat_raw = (request.GET.get("categoria") or "").strip()
        categoria_id = int(cat_raw) if cat_raw.isdigit() else None

        tipo = (request.GET.get("tipo") or "").strip().upper()
        if tipo not in ("E", "S"):
            tipo = ""

        return cls(periodo=periodo, categoria_id=categoria_id, tipo=tipo)

    @property
    def ativo(self):
        return (
            self.periodo != "30d"
            or self.categoria_id is not None
            or bool(self.tipo)
        )

    def data_inicio(self):
        agora = timezone.now()
        if self.periodo == "ano":
            return timezone.make_aware(
                datetime(agora.year, 1, 1, 0, 0, 0),
                timezone.get_current_timezone(),
            )
        dias = _DIAS_PERIODO[self.periodo]
        return agora - timedelta(days=dias)

    def dias_grafico_linha(self):
        """Quantidade de pontos no gráfico de movimento diário."""
        if self.periodo == "7d":
            return 7
        if self.periodo == "30d":
            return 30
        if self.periodo == "3m":
            return 30
        if self.periodo == "6m":
            return 30
        agora = timezone.localdate()
        inicio_ano = agora.replace(month=1, day=1)
        return min((agora - inicio_ano).days + 1, 31)

    def meses_grafico_valor(self):
        if self.periodo == "7d":
            return 1
        if self.periodo == "30d":
            return 2
        if self.periodo == "3m":
            return 3
        if self.periodo == "6m":
            return 6
        agora = timezone.localdate()
        return agora.month

    def aplicar_movimentacoes(self, qs):
        qs = qs.filter(data__gte=self.data_inicio())
        if self.categoria_id:
            qs = qs.filter(produto__categoria_id=self.categoria_id)
        if self.tipo:
            qs = qs.filter(tipo=self.tipo)
        return qs

    def aplicar_produtos(self, qs):
        if self.categoria_id:
            qs = qs.filter(categoria_id=self.categoria_id)
        return qs

    def label_periodo(self):
        for codigo, nome in PERIODO_OPCOES:
            if codigo == self.periodo:
                return nome
        return "Período"
