"""Vistas principales del proyecto."""

from django.shortcuts import render
from apps.articulos.models import Articulo


def home(request):
    """Renderiza la pagina de inicio con los ultimos articulos.

    Templates:
        index.html

    Context:
        ultimos_articulos: Ultimos 6 articulos publicados.
    """
    ultimos_articulos = Articulo.objects.select_related(
        'categoria_articulo', 'usuario_articulo'
    ).order_by('-fecha_publicacion')[:6]

    return render(request, 'index.html', {
        'ultimos_articulos': ultimos_articulos,
    })


def acerca_de(request):
    """Renderiza la pagina Acerca de.

    Templates:
        acerca_de.html
    """
    return render(request, 'acerca_de.html')
