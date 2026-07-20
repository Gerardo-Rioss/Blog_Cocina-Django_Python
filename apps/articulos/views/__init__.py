"""Paquete de vistas de la app de articulos.

Re-exporta todas las vistas para mantener compatibilidad con imports existentes
(tanto internos — desde urls.py — como externos).
"""

from .articulos import (
    listar_articulos,
    detalle_articulos,
    crear_articulo,
    editar_articulo,
    eliminar_articulo,
)
from .categorias import (
    listar_categorias,
    crear_categoria,
    editar_categoria,
    eliminar_categoria,
)
from .comentarios import (
    agregar_comentario,
    editar_comentario,
    eliminar_comentario,
)

__all__ = [
    # Articulos
    'listar_articulos', 'detalle_articulos', 'crear_articulo',
    'editar_articulo', 'eliminar_articulo',
    # Categorias
    'listar_categorias', 'crear_categoria',
    'editar_categoria', 'eliminar_categoria',
    # Comentarios
    'agregar_comentario', 'editar_comentario', 'eliminar_comentario',
]
