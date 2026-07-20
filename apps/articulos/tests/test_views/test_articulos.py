"""Tests de vistas de Articulo: acceso, autorizacion y metodos HTTP.

Cubre: anonimo, Miembro, Colaborador, Administrador.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from apps.articulos.models import Articulo
from apps.articulos.tests.factories import ArticuloFactory


def _imagen_test():
    """Helper: imagen SimpleUploadedFile para tests de POST (1x1 GIF valido)."""
    return SimpleUploadedFile(
        'test.jpg',
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        content_type='image/gif',
    )


# ─── listar_articulos (publica) ───

@pytest.mark.django_db
class TestListarArticulos:
    """Tests de la vista listar_articulos."""

    def test_anonimo_200(self, cliente_anonimo):
        url = reverse('articulos:listar_articulos')
        response = cliente_anonimo.get(url)
        assert response.status_code == 200

    def test_template_correcto(self, cliente_anonimo):
        url = reverse('articulos:listar_articulos')
        response = cliente_anonimo.get(url)
        assert 'articulos/listarArticulos.html' in [
            getattr(t, 'name', t) for t in response.templates
        ]

    def test_con_filtro_categoria(self, cliente_anonimo, categoria):
        url = reverse('articulos:listar_articulos') + f'?categoria={categoria.pk}'
        response = cliente_anonimo.get(url)
        assert response.status_code == 200

    def test_con_orden_asc(self, cliente_anonimo):
        url = reverse('articulos:listar_articulos') + '?antiguedad_asc=1'
        response = cliente_anonimo.get(url)
        assert response.status_code == 200


# ─── detalle_articulos (publica) ───

@pytest.mark.django_db
class TestDetalleArticulos:
    """Tests de la vista detalle_articulos."""

    def test_anonimo_200(self, cliente_anonimo, articulo):
        url = reverse('articulos:detalle_articulos', kwargs={'pk': articulo.pk})
        response = cliente_anonimo.get(url)
        assert response.status_code == 200

    def test_template_correcto(self, cliente_anonimo, articulo):
        url = reverse('articulos:detalle_articulos', kwargs={'pk': articulo.pk})
        response = cliente_anonimo.get(url)
        assert 'articulos/detalleArticulos.html' in [
            getattr(t, 'name', t) for t in response.templates
        ]


# ─── crear_articulo ───

@pytest.mark.django_db
class TestCrearArticulo:
    """Tests de la vista crear_articulo."""

    def test_anonimo_redirect_login(self, cliente_anonimo):
        url = reverse('articulos:crear_articulo')
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_403(self, usuario_miembro, client):
        url = reverse('articulos:crear_articulo')
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_get_200(self, usuario_colaborador, client):
        url = reverse('articulos:crear_articulo')
        response = client.get(url)
        assert response.status_code == 200

    def test_colaborador_post_redirect(self, usuario_colaborador, categoria, client):
        url = reverse('articulos:crear_articulo')
        data = {
            'titulo': 'Nuevo Articulo',
            'contenido_breve': 'Resumen breve del articulo.',
            'contenido_completo': 'Contenido completo del articulo nuevo.',
            'categoria_articulo': categoria.pk,
            'imagen': _imagen_test(),
        }
        response = client.post(url, data)
        assert response.status_code == 302

    def test_administrador_get_200(self, usuario_administrador, client):
        url = reverse('articulos:crear_articulo')
        response = client.get(url)
        assert response.status_code == 200


# ─── editar_articulo ───

@pytest.mark.django_db
class TestEditarArticulo:
    """Tests de la vista editar_articulo."""

    def test_anonimo_redirect_login(self, cliente_anonimo, articulo):
        url = reverse('articulos:editar_articulo', kwargs={'pk': articulo.pk})
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_403(self, usuario_miembro, articulo, client):
        url = reverse('articulos:editar_articulo', kwargs={'pk': articulo.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_propio_200(self, usuario_colaborador, client):
        art = ArticuloFactory(usuario_articulo=usuario_colaborador)
        url = reverse('articulos:editar_articulo', kwargs={'pk': art.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_colaborador_ajeno_403(self, usuario_colaborador, articulo, client):
        url = reverse('articulos:editar_articulo', kwargs={'pk': articulo.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_ajeno_200(self, usuario_administrador, articulo, client):
        url = reverse('articulos:editar_articulo', kwargs={'pk': articulo.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_post_exitoso_redirect(self, usuario_colaborador, client):
        art = ArticuloFactory(usuario_articulo=usuario_colaborador)
        url = reverse('articulos:editar_articulo', kwargs={'pk': art.pk})
        data = {
            'titulo': 'Titulo Editado',
            'contenido_breve': art.contenido_breve,
            'contenido_completo': art.contenido_completo,
            'imagen': _imagen_test(),
        }
        response = client.post(url, data)
        assert response.status_code == 302


# ─── eliminar_articulo ───

@pytest.mark.django_db
class TestEliminarArticulo:
    """Tests de la vista eliminar_articulo."""

    def test_anonimo_redirect_login(self, cliente_anonimo, articulo):
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = cliente_anonimo.post(url)
        assert response.status_code == 302

    def test_miembro_redirect_con_error(self, usuario_miembro, articulo, client):
        """Miembro es redirigido con mensaje de error, el articulo NO se borra."""
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert Articulo.objects.filter(pk=articulo.pk).exists()

    def test_colaborador_propio_elimina(self, usuario_colaborador, client):
        art = ArticuloFactory(usuario_articulo=usuario_colaborador)
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': art.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Articulo.objects.filter(pk=art.pk).exists()

    def test_colaborador_ajeno_no_elimina(self, usuario_colaborador, articulo, client):
        """Colaborador es redirigido, el articulo ajeno sigue existiendo."""
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert Articulo.objects.filter(pk=articulo.pk).exists()

    def test_admin_elimina_cualquiera(self, usuario_administrador, articulo, client):
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Articulo.objects.filter(pk=articulo.pk).exists()
