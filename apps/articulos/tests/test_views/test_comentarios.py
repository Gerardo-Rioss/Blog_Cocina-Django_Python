"""Tests de vistas de Comentario: acceso, autorizacion y metodos HTTP."""

import pytest
from django.urls import reverse
from apps.articulos.models import Comentario
from apps.articulos.tests.factories import ComentarioFactory, ArticuloFactory


# ─── agregar_comentario ───

@pytest.mark.django_db
class TestAgregarComentario:
    """Tests de la vista agregar_comentario."""

    def test_anonimo_redirect_login(self, cliente_anonimo, articulo):
        url = reverse('articulos:agregar_comentario',
                      kwargs={'articulo_id': articulo.pk})
        response = cliente_anonimo.post(url, {'comentario': 'Hola'})
        assert response.status_code == 302

    def test_autenticado_post_redirect(self, usuario_colaborador, articulo, client):
        url = reverse('articulos:agregar_comentario',
                      kwargs={'articulo_id': articulo.pk})
        response = client.post(url, {'comentario': 'Buen articulo!'})
        assert response.status_code == 302
        assert Comentario.objects.filter(comentario='Buen articulo!').exists()

    def test_autenticado_post_vacio_redirect(self, usuario_colaborador, articulo, client):
        """POST con comentario vacio redirige con mensaje de error."""
        url = reverse('articulos:agregar_comentario',
                      kwargs={'articulo_id': articulo.pk})
        response = client.post(url, {'comentario': ''})
        assert response.status_code == 302
        # El comentario vacio NO se guarda
        assert not Comentario.objects.filter(comentario='').exists()


# ─── editar_comentario ───

@pytest.mark.django_db
class TestEditarComentario:
    """Tests de la vista editar_comentario."""

    def test_anonimo_redirect_login(self, cliente_anonimo, comentario):
        url = reverse('articulos:editar_comentario',
                      kwargs={'comentario_id': comentario.pk})
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_propio_200(self, usuario_miembro, client):
        com = ComentarioFactory(usuario_comentario=usuario_miembro)
        url = reverse('articulos:editar_comentario',
                      kwargs={'comentario_id': com.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_miembro_ajeno_403(self, usuario_miembro, comentario, client):
        url = reverse('articulos:editar_comentario',
                      kwargs={'comentario_id': comentario.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_propio_200(self, usuario_colaborador, client):
        com = ComentarioFactory(usuario_comentario=usuario_colaborador)
        url = reverse('articulos:editar_comentario',
                      kwargs={'comentario_id': com.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_colaborador_ajeno_403(self, usuario_colaborador, comentario, client):
        url = reverse('articulos:editar_comentario',
                      kwargs={'comentario_id': comentario.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_ajeno_200(self, usuario_administrador, comentario, client):
        url = reverse('articulos:editar_comentario',
                      kwargs={'comentario_id': comentario.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_post_exitoso_redirect(self, usuario_colaborador, client):
        com = ComentarioFactory(usuario_comentario=usuario_colaborador)
        url = reverse('articulos:editar_comentario',
                      kwargs={'comentario_id': com.pk})
        response = client.post(url, {'comentario': 'Editado'})
        assert response.status_code == 302
        com.refresh_from_db()
        assert com.comentario == 'Editado'


# ─── eliminar_comentario ───

@pytest.mark.django_db
class TestEliminarComentario:
    """Tests de la vista eliminar_comentario."""

    def test_anonimo_redirect_login(self, cliente_anonimo, comentario):
        url = reverse('articulos:eliminar_comentario',
                      kwargs={'comentario_id': comentario.pk})
        response = cliente_anonimo.post(url)
        assert response.status_code == 302

    def test_miembro_propio_elimina(self, usuario_miembro, client):
        com = ComentarioFactory(usuario_comentario=usuario_miembro)
        url = reverse('articulos:eliminar_comentario',
                      kwargs={'comentario_id': com.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Comentario.objects.filter(pk=com.pk).exists()

    def test_miembro_ajeno_403(self, usuario_miembro, comentario, client):
        url = reverse('articulos:eliminar_comentario',
                      kwargs={'comentario_id': comentario.pk})
        response = client.post(url)
        assert response.status_code == 403

    def test_admin_elimina_cualquiera(self, usuario_administrador, comentario, client):
        url = reverse('articulos:eliminar_comentario',
                      kwargs={'comentario_id': comentario.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Comentario.objects.filter(pk=comentario.pk).exists()
