"""Tests de vistas de Categoria: acceso, autorizacion y metodos HTTP.

Cubre: anonimo, Miembro, Colaborador, Administrador.
"""

import pytest
from django.urls import reverse
from apps.articulos.models import Categoria
from apps.articulos.tests.factories import CategoriaFactory


# ─── listar_categorias (publica) ───

@pytest.mark.django_db
class TestListarCategorias:
    """Tests de la vista listar_categorias."""

    def test_anonimo_200(self, cliente_anonimo):
        url = reverse('articulos:listar_categorias')
        response = cliente_anonimo.get(url)
        assert response.status_code == 200

    def test_template_correcto(self, cliente_anonimo):
        url = reverse('articulos:listar_categorias')
        response = cliente_anonimo.get(url)
        assert 'categorias/listarCategorias.html' in [
            getattr(t, 'name', t) for t in response.templates
        ]

    def test_lista_categorias(self, cliente_anonimo, categoria):
        url = reverse('articulos:listar_categorias')
        response = cliente_anonimo.get(url)
        assert categoria.descripcion in response.content.decode()


# ─── crear_categoria (solo admin) ───

@pytest.mark.django_db
class TestCrearCategoria:
    """Tests de la vista crear_categoria."""

    def test_anonimo_redirect_login(self, cliente_anonimo):
        url = reverse('articulos:crear_categoria')
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_403(self, usuario_miembro, client):
        url = reverse('articulos:crear_categoria')
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_403(self, usuario_colaborador, client):
        url = reverse('articulos:crear_categoria')
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_get_200(self, usuario_administrador, client):
        url = reverse('articulos:crear_categoria')
        response = client.get(url)
        assert response.status_code == 200

    def test_admin_post_redirect(self, usuario_administrador, client):
        url = reverse('articulos:crear_categoria')
        response = client.post(url, {'descripcion': 'Nueva Categoria'})
        assert response.status_code == 302
        assert Categoria.objects.filter(descripcion='Nueva Categoria').exists()


# ─── editar_categoria (solo admin) ───

@pytest.mark.django_db
class TestEditarCategoria:
    """Tests de la vista editar_categoria."""

    def test_anonimo_redirect_login(self, cliente_anonimo, categoria):
        url = reverse('articulos:editar_categoria', kwargs={'categoria_id': categoria.pk})
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_403(self, usuario_miembro, categoria, client):
        url = reverse('articulos:editar_categoria', kwargs={'categoria_id': categoria.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_403(self, usuario_colaborador, categoria, client):
        url = reverse('articulos:editar_categoria', kwargs={'categoria_id': categoria.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_get_200(self, usuario_administrador, categoria, client):
        url = reverse('articulos:editar_categoria', kwargs={'categoria_id': categoria.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_admin_post_redirect(self, usuario_administrador, categoria, client):
        url = reverse('articulos:editar_categoria', kwargs={'categoria_id': categoria.pk})
        response = client.post(url, {'descripcion': 'Editada'})
        assert response.status_code == 302
        categoria.refresh_from_db()
        assert categoria.descripcion == 'Editada'


# ─── eliminar_categoria (solo admin) ───

@pytest.mark.django_db
class TestEliminarCategoria:
    """Tests de la vista eliminar_categoria."""

    def test_anonimo_redirect_login(self, cliente_anonimo, categoria):
        url = reverse('articulos:eliminar_categoria', kwargs={'categoria_id': categoria.pk})
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_403(self, usuario_miembro, categoria, client):
        url = reverse('articulos:eliminar_categoria', kwargs={'categoria_id': categoria.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_403(self, usuario_colaborador, categoria, client):
        url = reverse('articulos:eliminar_categoria', kwargs={'categoria_id': categoria.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_elimina(self, usuario_administrador, categoria, client):
        url = reverse('articulos:eliminar_categoria', kwargs={'categoria_id': categoria.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert not Categoria.objects.filter(pk=categoria.pk).exists()
