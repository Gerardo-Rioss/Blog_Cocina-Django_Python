"""Vistas CRUD para el modelo Articulo.

Maneja listado, detalle, creacion, edicion y eliminacion de articulos.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from ..models import Articulo, Categoria, Comentario
from ..forms import ArticuloForm, ComentarioForm


def listar_articulos(request):
    """Lista todos los articulos con filtros por categoria, antiguedad y orden.

    Templates:
        articulos/listarArticulos.html

    Context:
        articulos: QuerySet de Articulo con select_related.
        categorias: QuerySet de todas las Categoria.
    """
    articulos = Articulo.objects.select_related(
        'categoria_articulo', 'usuario_articulo'
    ).all()

    # FILTRAR POR CATEGORIA
    categoria = request.GET.get('categoria')
    if categoria:
        articulos = articulos.filter(categoria_articulo=categoria)

    # FILTRAR POR ANTIGUEDAD ASCENDENTE
    antiguedad_asc = request.GET.get('antiguedad_asc')
    if antiguedad_asc:
        articulos = articulos.order_by('fecha_publicacion')

    # FILTRAR POR ANTIGUEDAD DESCENDENTE
    antiguedad_desc = request.GET.get('antiguedad_desc')
    if antiguedad_desc:
        articulos = articulos.order_by('-fecha_publicacion')

    # FILTRAR POR ORDEN ALFABETICO ASCENDENTE
    orden_asc = request.GET.get('orden_asc')
    if orden_asc:
        articulos = articulos.order_by('titulo')

    # FILTRAR POR ORDEN ALFABETICO DESCENDENTE
    orden_desc = request.GET.get('orden_desc')
    if orden_desc:
        articulos = articulos.order_by('-titulo')

    contexto = {
        'articulos': articulos,
        'categorias': Categoria.objects.all(),
    }
    return render(request, 'articulos/listarArticulos.html', contexto)


def detalle_articulos(request, pk):
    """Muestra el detalle de un articulo y su formulario de comentarios.

    Args:
        pk: Clave primaria del Articulo.

    Templates:
        articulos/detalleArticulos.html

    Context:
        articulo: Instancia de Articulo con prefetch de comentarios.
        comentarios: QuerySet de Comentario relacionados.
        form: ComentarioForm vacio o con errores de validacion.
    """
    articulo = get_object_or_404(
        Articulo.objects.select_related(
            'categoria_articulo', 'usuario_articulo'
        ).prefetch_related('comentarios__usuario_comentario'),
        pk=pk,
    )
    comentarios = articulo.comentarios.all()

    # COMENTARIO desde el detalle
    if request.method == 'POST' and 'add_comentario' in request.POST:
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.articulo_comentario = articulo
            comentario.usuario_comentario = request.user
            comentario.save()
            return redirect('articulos:detalle_articulos', pk=pk)
    else:
        form = ComentarioForm()

    contexto = {
        'articulo': articulo,
        'comentarios': comentarios,
        'form': form,
    }
    return render(request, 'articulos/detalleArticulos.html', contexto)


@login_required
def crear_articulo(request):
    """Crea un nuevo articulo. Requiere rol Colaborador o Administrador.

    Templates:
        articulos/addArticulo.html

    Context:
        form: ArticuloForm vacio o con errores de validacion.
    """
    if not (request.user.es_colaborador() or request.user.es_administrador()):
        raise PermissionDenied()

    if request.method == 'POST':
        form = ArticuloForm(request.POST, request.FILES)
        if form.is_valid():
            articulo = form.save(commit=False)
            articulo.usuario_articulo = request.user
            articulo.save()
            return redirect('home')
    else:
        form = ArticuloForm()

    return render(request, 'articulos/addArticulo.html', {'form': form})


@login_required
def editar_articulo(request, pk):
    """Edita un articulo existente. Requiere ser autor o Administrador.

    Args:
        pk: Clave primaria del Articulo a editar.

    Templates:
        articulos/edit_articulo.html

    Context:
        form: ArticuloForm con datos del articulo o errores de validacion.
    """
    articulo = get_object_or_404(Articulo, pk=pk)

    if not request.user.puede_editar_articulo(articulo):
        raise PermissionDenied()

    if request.method == 'POST':
        form = ArticuloForm(request.POST, request.FILES, instance=articulo)
        if form.is_valid():
            form.save()
            return redirect('articulos:detalle_articulos', pk=pk)
    else:
        form = ArticuloForm(instance=articulo)

    contexto = {
        'form': form,
    }
    return render(request, 'articulos/edit_articulo.html', contexto)


@login_required
def eliminar_articulo(request, pk):
    """Elimina un articulo. Requiere ser autor o Administrador.

    Args:
        pk: Clave primaria del Articulo a eliminar.

    Redirect:
        Listado de articulos tras eliminacion exitosa.
        Mismo listado con mensaje de error si no tiene permiso.
    """
    articulo = get_object_or_404(Articulo, id=pk)
    if not request.user.puede_eliminar_articulo(articulo):
        messages.error(request, 'No tenes permiso para eliminar este articulo')
        return redirect('articulos:listar_articulos')
    articulo.delete()
    return redirect('articulos:listar_articulos')
