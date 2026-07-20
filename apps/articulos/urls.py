from django.urls import path
from . import views

app_name = 'articulos'

urlpatterns = [
    # ─── Articulos ───
    path('', views.listar_articulos, name='listar_articulos'),
    path('crear/', views.crear_articulo, name='crear_articulo'),
    path('<int:pk>/', views.detalle_articulos, name='detalle_articulos'),
    path('<int:pk>/editar/', views.editar_articulo, name='editar_articulo'),
    path('<int:pk>/eliminar/', views.eliminar_articulo, name='eliminar_articulo'),

    # ─── Categorias ───
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),

    # ─── Comentarios ───
    path('comentario/<int:articulo_id>/crear/', views.agregar_comentario, name='agregar_comentario'),
    path('comentario/<int:comentario_id>/editar/', views.editar_comentario, name='editar_comentario'),
    path('comentario/<int:comentario_id>/eliminar/', views.eliminar_comentario, name='eliminar_comentario'),
]
