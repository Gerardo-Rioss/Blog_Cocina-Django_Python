"""Formularios de la app de articulos: Articulo, Categoria y Comentario."""

from django import forms
from .models import Articulo, Categoria, Comentario


class ArticuloForm(forms.ModelForm):
    """Formulario para crear y editar Articulos.

    Incluye todos los campos editables por el usuario excepto
    usuario_articulo (asignado en la vista).
    """

    class Meta:
        model = Articulo
        fields = [
            'titulo', 'contenido_breve', 'contenido_completo',
            'imagen', 'categoria_articulo',
        ]


class CategoriaForm(forms.ModelForm):
    """Formulario para crear y editar Categorias.

    Solo expone el campo descripcion.
    """

    class Meta:
        model = Categoria
        fields = ['descripcion']


class ComentarioForm(forms.ModelForm):
    """Formulario para crear y editar Comentarios.

    Solo expone el campo comentario. Las FKs (articulo_comentario
    y usuario_comentario) se asignan en la vista con commit=False.
    """

    class Meta:
        model = Comentario
        fields = ['comentario']
