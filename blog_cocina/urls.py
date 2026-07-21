"""
URL configuration for blog_cocina project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
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

    # ─── Redirects temporarios de URLs viejas a nuevas ───
    # TODO: eliminar despues de 3 meses (2026-10-12)
    # Articulos
    path('articulos/addArticulo/', RedirectView.as_view(
        pattern_name='articulos:crear_articulo', permanent=True)),
    path('articulos/detalleArticulos/<int:pk>/', RedirectView.as_view(
        pattern_name='articulos:detalle_articulos', permanent=True)),
    path('articulos/articulos/<int:pk>/edit/', RedirectView.as_view(
        pattern_name='articulos:editar_articulo', permanent=True)),
    path('articulos/articulo/delete/<int:pk>/', RedirectView.as_view(
        pattern_name='articulos:eliminar_articulo', permanent=True)),
    # Categorias
    path('articulos/addCategoria/', RedirectView.as_view(
        pattern_name='articulos:crear_categoria', permanent=True)),
    path('articulos/categorias/edit/<int:categoria_id>/', RedirectView.as_view(
        pattern_name='articulos:editar_categoria', permanent=True)),
    path('articulos/categorias/delete/<int:categoria_id>/', RedirectView.as_view(
        pattern_name='articulos:eliminar_categoria', permanent=True)),
    # Comentarios
    path('articulos/comentario/add/<int:articulo_id>/', RedirectView.as_view(
        pattern_name='articulos:agregar_comentario', permanent=True)),
    path('articulos/comentario/edit/<int:comentario_id>/', RedirectView.as_view(
        pattern_name='articulos:editar_comentario', permanent=True)),
    path('articulos/comentario/delete/<int:comentario_id>/', RedirectView.as_view(
        pattern_name='articulos:eliminar_comentario', permanent=True)),
]

# ─── Servir archivos media (tanto en dev como en prod) ───
# En produccion Render usamos WhiteNoise + static(media)
from django.views.static import serve as static_serve
urlpatterns += [
    path('media/<path:path>', static_serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
