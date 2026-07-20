"""Vistas CRUD para el modelo Categoria.

Maneja listado, creacion, edicion y eliminacion de categorias.
Acceso restringido a Administradores para operaciones de escritura.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from ..models import Categoria
from ..forms import CategoriaForm


def listar_categorias(request):
    """Lista todas las categorias disponibles.

    Templates:
        categorias/listarCategorias.html

    Context:
        categorias: QuerySet de todas las Categoria.
    """
    categorias = Categoria.objects.all()
    contexto = {
        'categorias': categorias,
    }
    return render(request, 'categorias/listarCategorias.html', contexto)


@login_required
def crear_categoria(request):
    """Crea una nueva categoria. Solo Administradores.

    Templates:
        categorias/addCategoria.html

    Context:
        form: CategoriaForm vacio o con errores de validacion.
    """
    if not request.user.es_administrador():
        raise PermissionDenied()

    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.save()
            return redirect('articulos:listar_categorias')
    else:
        form = CategoriaForm()

    return render(request, 'categorias/addCategoria.html', {'form': form})


@login_required
def editar_categoria(request, categoria_id):
    """Edita una categoria existente. Solo Administradores.

    Args:
        categoria_id: ID de la Categoria a editar.

    Templates:
        categorias/edit_categoria.html

    Context:
        form: CategoriaForm con datos de la categoria o errores.
    """
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if not request.user.es_administrador():
        raise PermissionDenied()

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('articulos:listar_categorias')
    else:
        form = CategoriaForm(instance=categoria)

    contexto = {
        'form': form,
    }
    return render(request, 'categorias/edit_categoria.html', contexto)


@login_required
def eliminar_categoria(request, categoria_id):
    """Elimina una categoria. Solo Administradores.

    Args:
        categoria_id: ID de la Categoria a eliminar.

    Redirect:
        Listado de categorias tras eliminacion.
    """
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if not request.user.es_administrador():
        raise PermissionDenied()
    categoria.delete()
    return redirect('articulos:listar_categorias')
