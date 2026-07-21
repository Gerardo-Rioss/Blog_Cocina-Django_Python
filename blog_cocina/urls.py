"""
URL configuration for blog_cocina project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import RedirectView

from . import views


def consola_admin(request):
    return redirect('/admin/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('acerca de/', views.acerca_de, name='acerca_de'),
    path('usuarios/', include('apps.usuarios.urls')),
    path('articulos/', include('apps.articulos.urls')),
    path('contacto/', include('apps.contacto.urls')),
    path('administrador/', consola_admin, name='administrador'),

    path('articulos/addArticulo/', RedirectView.as_view(
        pattern_name='articulos:crear_articulo', permanent=True)),
    path('articulos/detalleArticulos/<int:pk>/', RedirectView.as_view(
        pattern_name='articulos:detalle_articulos', permanent=True)),
    path('articulos/articulos/<int:pk>/edit/', RedirectView.as_view(
        pattern_name='articulos:editar_articulo', permanent=True)),
    path('articulos/articulo/delete/<int:pk>/', RedirectView.as_view(
        pattern_name='articulos:eliminar_articulo', permanent=True)),
    path('articulos/addCategoria/', RedirectView.as_view(
        pattern_name='articulos:crear_categoria', permanent=True)),
    path('articulos/categorias/edit/<int:categoria_id>/', RedirectView.as_view(
        pattern_name='articulos:editar_categoria', permanent=True)),
    path('articulos/categorias/delete/<int:categoria_id>/', RedirectView.as_view(
        pattern_name='articulos:eliminar_categoria', permanent=True)),
    path('articulos/comentario/add/<int:articulo_id>/', RedirectView.as_view(
        pattern_name='articulos:agregar_comentario', permanent=True)),
    path('articulos/comentario/edit/<int:comentario_id>/', RedirectView.as_view(
        pattern_name='articulos:editar_comentario', permanent=True)),
    path('articulos/comentario/delete/<int:comentario_id>/', RedirectView.as_view(
        pattern_name='articulos:eliminar_comentario', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
