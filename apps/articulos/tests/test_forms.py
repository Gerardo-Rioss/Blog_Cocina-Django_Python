"""Tests de formularios de la app articulos: ArticuloForm, CategoriaForm, ComentarioForm."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.articulos.forms import ArticuloForm, CategoriaForm, ComentarioForm
from apps.articulos.tests.factories import CategoriaFactory


@pytest.mark.django_db
class TestArticuloForm:
    """Tests del formulario ArticuloForm."""

    def _imagen_mock(self):
        return SimpleUploadedFile(
            name='test.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/gif',
        )

    def test_form_valido_con_campos_requeridos(self):
        """Form es valido con titulo, contenidos, imagen y categoria."""
        cat = CategoriaFactory()
        data = {
            'titulo': 'Mi Receta',
            'contenido_breve': 'Resumen breve',
            'contenido_completo': 'Contenido completo de la receta.',
            'categoria_articulo': cat.pk,
        }
        files = {'imagen': self._imagen_mock()}
        form = ArticuloForm(data=data, files=files)
        assert form.is_valid(), f'Errores: {form.errors}'

    def test_form_invalido_sin_titulo(self):
        """Form es invalido si titulo esta vacio."""
        cat = CategoriaFactory()
        data = {
            'titulo': '',
            'contenido_breve': 'Resumen',
            'contenido_completo': 'Contenido completo.',
            'categoria_articulo': cat.pk,
        }
        form = ArticuloForm(data=data)
        assert not form.is_valid()
        assert 'titulo' in form.errors

    def test_form_invalido_sin_contenido_breve(self):
        """Form es invalido si contenido_breve esta vacio."""
        cat = CategoriaFactory()
        data = {
            'titulo': 'Mi Receta',
            'contenido_breve': '',
            'contenido_completo': 'Contenido completo.',
            'categoria_articulo': cat.pk,
        }
        form = ArticuloForm(data=data)
        assert not form.is_valid()

    def test_categoria_puede_ser_null(self, db):
        """Form es valido sin categoria (campo nullable)."""
        data = {
            'titulo': 'Receta Sin Categoria',
            'contenido_breve': 'Resumen',
            'contenido_completo': 'Contenido.',
        }
        files = {'imagen': self._imagen_mock()}
        form = ArticuloForm(data=data, files=files)
        assert form.is_valid(), f'Errores: {form.errors}'


@pytest.mark.django_db
class TestCategoriaForm:
    """Tests del formulario CategoriaForm."""

    def test_form_valido_con_descripcion(self):
        """Form es valido con descripcion provista."""
        form = CategoriaForm(data={'descripcion': 'Postres'})
        assert form.is_valid()

    def test_form_invalido_sin_descripcion(self):
        """Form es invalido si descripcion esta vacia."""
        form = CategoriaForm(data={'descripcion': ''})
        assert not form.is_valid()
        assert 'descripcion' in form.errors


@pytest.mark.django_db
class TestComentarioForm:
    """Tests del formulario ComentarioForm."""

    def test_form_valido_con_comentario(self):
        """Form es valido con contenido de comentario no vacio."""
        form = ComentarioForm(data={'comentario': 'Muy buen articulo!'})
        assert form.is_valid()

    def test_form_invalido_comentario_vacio(self):
        """Form es invalido si comentario esta vacio."""
        form = ComentarioForm(data={'comentario': ''})
        assert not form.is_valid()
        assert 'comentario' in form.errors

    def test_form_invalido_comentario_solo_espacios(self):
        """Form es invalido si comentario es solo espacios."""
        form = ComentarioForm(data={'comentario': '   '})
        assert not form.is_valid()
