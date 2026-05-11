"""
Template tags utilitárias para arquivos estáticos.

Resolve o problema clássico do navegador servir uma versão antiga do CSS
(ou JS) do cache mesmo após o arquivo ter sido recompilado. Adicionamos
um query string `?v=<mtime>` que muda toda vez que o arquivo é regenerado,
forçando o navegador a baixar a versão atual.
"""
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


def _resolve_local_path(path: str) -> Path | None:
    """Procura o arquivo nas pastas configuradas em STATICFILES_DIRS."""
    for static_dir in getattr(settings, "STATICFILES_DIRS", []):
        candidate = Path(static_dir) / path
        if candidate.is_file():
            return candidate
    return None


@register.simple_tag
def static_v(path: str) -> str:
    """
    Retorna a URL estática de `path` com sufixo `?v=<mtime>` para invalidar
    o cache do navegador automaticamente sempre que o arquivo for alterado.

    Uso no template:
        {% load static_extras %}
        <link rel="stylesheet" href="{% static_v 'css/style.css' %}">
    """
    url = static(path)
    local_path = _resolve_local_path(path)
    if local_path is None:
        return url
    version = int(local_path.stat().st_mtime)
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"
