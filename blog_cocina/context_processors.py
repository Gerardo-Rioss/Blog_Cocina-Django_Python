"""Context processors del proyecto."""

from apps.articulos.models import Categoria


def categorias_footer(request):
    """Agrega las categorias al contexto global para el footer."""
    return {
        'categorias_footer': Categoria.objects.all().order_by('descripcion')[:6],
    }
