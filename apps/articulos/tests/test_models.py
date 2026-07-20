"""Tests unitarios de los modelos Categoria, Articulo y Comentario.

Cubre creacion, __str__, relaciones FK, y on_delete behavior.
"""

import pytest
from apps.articulos.models import Categoria, Articulo, Comentario
from apps.articulos.tests.factories import (
    CategoriaFactory, ArticuloFactory, ComentarioFactory,
)


@pytest.mark.django_db
class TestCategoria:
    """Tests del modelo Categoria."""

    def test_crear_categoria(self):
        """Categoria se crea correctamente con descripcion."""
        cat = CategoriaFactory(descripcion='Postres')
        assert cat.pk is not None
        assert cat.descripcion == 'Postres'

    def test_str_retorna_descripcion(self):
        """__str__ retorna la descripcion."""
        cat = CategoriaFactory.build(descripcion='Ensaladas')
        assert str(cat) == 'Ensaladas'


@pytest.mark.django_db
class TestArticulo:
    """Tests del modelo Articulo."""

    def test_crear_articulo(self, categoria, usuario_colaborador):
        """Articulo se crea correctamente con titulo, FK categoria y FK usuario."""
        art = ArticuloFactory(
            titulo='Mi Receta',
            categoria_articulo=categoria,
            usuario_articulo=usuario_colaborador,
        )
        assert art.pk is not None
        assert art.titulo == 'Mi Receta'

    def test_str_retorna_titulo(self):
        """__str__ retorna el titulo."""
        art = ArticuloFactory.build(titulo='Tarta de Manzana')
        assert str(art) == 'Tarta de Manzana'

    def test_fk_categoria_es_instancia(self, categoria, db):
        """categoria_articulo es instancia de Categoria."""
        art = ArticuloFactory(categoria_articulo=categoria)
        assert isinstance(art.categoria_articulo, Categoria)

    def test_fk_usuario_es_instancia(self, usuario_colaborador, db):
        """usuario_articulo es instancia de Usuario."""
        art = ArticuloFactory(usuario_articulo=usuario_colaborador)
        assert art.usuario_articulo == usuario_colaborador

    def test_categoria_nullable(self, db):
        """Articulo permite categoria_articulo nulo."""
        art = ArticuloFactory(categoria_articulo=None)
        assert art.categoria_articulo is None

    def test_on_delete_categoria_set_null(self, categoria, db):
        """Al borrar Categoria, Articulo.categoria_articulo queda NULL."""
        art = ArticuloFactory(categoria_articulo=categoria)
        categoria.delete()
        art.refresh_from_db()
        assert art.categoria_articulo is None

    def test_on_delete_usuario_cascade(self, usuario_colaborador, db):
        """Al borrar Usuario, sus Articulos se borran en cascada."""
        ArticuloFactory(usuario_articulo=usuario_colaborador)
        art_count = Articulo.objects.count()
        usuario_colaborador.delete()
        assert Articulo.objects.count() == art_count - 1


@pytest.mark.django_db
class TestComentario:
    """Tests del modelo Comentario."""

    def test_crear_comentario(self, articulo, usuario_colaborador, db):
        """Comentario se crea correctamente con FK articulo y FK usuario."""
        com = ComentarioFactory(
            articulo_comentario=articulo,
            usuario_comentario=usuario_colaborador,
            comentario='Muy buena receta!',
        )
        assert com.pk is not None
        assert com.comentario == 'Muy buena receta!'

    def test_str_retorna_comentario(self):
        """__str__ retorna el contenido del comentario."""
        com = ComentarioFactory.build(comentario='Excelente post')
        assert str(com) == 'Excelente post'

    def test_fk_articulo_es_instancia(self, articulo, db):
        """articulo_comentario es instancia de Articulo."""
        com = ComentarioFactory(articulo_comentario=articulo)
        assert isinstance(com.articulo_comentario, Articulo)

    def test_fk_usuario_es_instancia(self, usuario_colaborador, db):
        """usuario_comentario es instancia de Usuario."""
        com = ComentarioFactory(usuario_comentario=usuario_colaborador)
        assert com.usuario_comentario == usuario_colaborador

    def test_on_delete_articulo_cascade(self, articulo, db):
        """Al borrar Articulo, sus Comentarios se borran en cascada."""
        ComentarioFactory(articulo_comentario=articulo)
        comentario_count_before = Comentario.objects.count()
        articulo.delete()
        assert Comentario.objects.count() == comentario_count_before - 1

    def test_on_delete_usuario_cascade(self, usuario_colaborador, db):
        """Al borrar Usuario, sus Comentarios se borran en cascada."""
        ComentarioFactory(usuario_comentario=usuario_colaborador)
        comentario_count_before = Comentario.objects.count()
        usuario_colaborador.delete()
        assert Comentario.objects.count() == comentario_count_before - 1
