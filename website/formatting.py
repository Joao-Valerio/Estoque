"""Formatação de valores monetários para exibição (padrão BRL)."""

from decimal import Decimal, InvalidOperation


def formatar_brl(valor):
    """Formata número em texto tipo R$ 1.234.567,89."""
    if valor is None:
        return "R$ 0,00"
    if isinstance(valor, Decimal):
        d = valor
    else:
        try:
            d = Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError):
            return "R$ 0,00"
    negativo = d < 0
    d = abs(d).quantize(Decimal("0.01"))
    inteira, frac = format(d, "f").split(".")
    blocos = []
    while len(inteira) > 3:
        blocos.append(inteira[-3:])
        inteira = inteira[:-3]
    blocos.append(inteira)
    num = ".".join(reversed(blocos))
    texto = f"R$ {num},{frac}"
    return f"-{texto}" if negativo else texto
