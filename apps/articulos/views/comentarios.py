"""Vistas CRUD para el modelo Comentario.

Maneja creacion, edicion y eliminacion de comentarios en articulos.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from ..models import Articulo, Comentario
from ..forms import ComentarioForm


@login_required
def agregar_comentario(request, articulo_id):
    """Agrega un comentario a un articulo. Requiere autenticacion.

    Args:
        articulo_id: ID del Articulo donde se agrega el comentario.

    Redirect:
        Detalle del articulo tras creacion exitosa o con mensaje de error.
    """
    articulo = get_object_or_404(Articulo, id=articulo_id)

    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.articulo_comentario = articulo
            comentario.usuario_comentario = request.user
            comentario.save()
            return redirect('articulos:detalle_articulos', pk=articulo_id)
        else:
            messages.error(request, 'El comentario no puede estar vacio.')
            return redirect('articulos:detalle_articulos', pk=articulo_id)

    return redirect('articulos:detalle_articulos', pk=articulo_id)


@login_required
def editar_comentario(request, comentario_id):
    """Edita un comentario existente. Solo el autor o un Administrador.

    Args:
        comentario_id: ID del Comentario a editar.

    Templates:
        articulos/edit_comentario.html

    Context:
        form: ComentarioForm con datos del comentario.
        comment: Instancia del Comentario editado.
    """
    comentario = get_object_or_404(Comentario, id=comentario_id)

    if not request.user.puede_editar_comentario(comentario):
        raise PermissionDenied()

    if request.method == 'POST':
        form = ComentarioForm(request.POST, instance=comentario)
        if form.is_valid():
            form.save()
            return redirect(
                'articulos:detalle_articulos',
                pk=comentario.articulo_comentario.pk,
            )
    else:
        form = ComentarioForm(instance=comentario)

    contexto = {
        'form': form,
        'comment': comentario,
    }
    return render(request, 'articulos/edit_comentario.html', contexto)


@login_required
def eliminar_comentario(request, comentario_id):
    """Elimina un comentario. Solo el autor o un Administrador.

    Args:
        comentario_id: ID del Comentario a eliminar.

    Redirect:
        Detalle del articulo tras eliminacion.
    """
    comentario = get_object_or_404(Comentario, id=comentario_id)
    if not request.user.puede_editar_comentario(comentario):
        raise PermissionDenied()
    articulo_pk = comentario.articulo_comentario.pk
    comentario.delete()
    return redirect('articulos:detalle_articulos', pk=articulo_pk)
