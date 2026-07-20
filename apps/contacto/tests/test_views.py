"""Tests de vistas de contacto: formulario publico y administracion de mensajes."""

import pytest
from django.urls import reverse
from apps.contacto.models import Contacto
from apps.contacto.tests.factories import ContactoFactory


# ─── msj_contacto (publica) ───

@pytest.mark.django_db
class TestMsjContacto:
    """Tests de la vista msj_contacto."""

    def test_get_200(self, client):
        url = reverse('contacto:contacto')
        response = client.get(url)
        assert response.status_code == 200

    def test_template_correcto(self, client):
        url = reverse('contacto:contacto')
        response = client.get(url)
        assert 'contacto/contacto.html' in [
            getattr(t, 'name', t) for t in response.templates
        ]

    def test_post_valido_crea_y_redirect(self, client):
        url = reverse('contacto:contacto')
        data = {
            'nombre': 'Juan',
            'email': 'juan@test.com',
            'telefono': '123456789',
            'mensaje': 'Hola, me gusta el blog.',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Contacto.objects.filter(
            nombre='Juan', email='juan@test.com',
        ).exists()

    def test_post_invalido_200(self, client):
        """POST con datos invalidos vuelve a renderizar el form con errores."""
        url = reverse('contacto:contacto')
        response = client.post(url, {'nombre': '', 'email': '', 'mensaje': ''})
        assert response.status_code == 200


# ─── listarMensajes (solo admin) ───

@pytest.mark.django_db
class TestListarMensajes:
    """Tests de la vista listarMensajes."""

    def test_anonimo_redirect_login(self, cliente_anonimo):
        url = reverse('contacto:mensajes')
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_403(self, usuario_miembro, client):
        url = reverse('contacto:mensajes')
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_403(self, usuario_colaborador, client):
        url = reverse('contacto:mensajes')
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_200(self, usuario_administrador, client, contacto):
        url = reverse('contacto:mensajes')
        response = client.get(url)
        assert response.status_code == 200
        assert 'contacto/listarMensajes.html' in [
            getattr(t, 'name', t) for t in response.templates
        ]


# ─── delete_mensaje (solo admin) ───

@pytest.mark.django_db
class TestDeleteMensaje:
    """Tests de la vista delete_mensaje."""

    def test_anonimo_redirect_login(self, cliente_anonimo, contacto):
        url = reverse('contacto:delete_mensaje',
                      kwargs={'mensaje_id': contacto.pk})
        response = cliente_anonimo.get(url)
        assert response.status_code == 302

    def test_miembro_403(self, usuario_miembro, contacto, client):
        url = reverse('contacto:delete_mensaje',
                      kwargs={'mensaje_id': contacto.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_colaborador_403(self, usuario_colaborador, contacto, client):
        url = reverse('contacto:delete_mensaje',
                      kwargs={'mensaje_id': contacto.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_admin_elimina_redirect(self, usuario_administrador, contacto, client):
        url = reverse('contacto:delete_mensaje',
                      kwargs={'mensaje_id': contacto.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert not Contacto.objects.filter(pk=contacto.pk).exists()
