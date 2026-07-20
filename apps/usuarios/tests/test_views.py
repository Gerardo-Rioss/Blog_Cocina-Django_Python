"""Tests de vistas de usuarios: login, registro, logout."""

import pytest
from django.urls import reverse
from apps.usuarios.models import Usuario
from apps.usuarios.tests.factories import UsuarioFactory


# ─── user_login ───

@pytest.mark.django_db
class TestLogin:
    """Tests de la vista user_login."""

    def test_get_200(self, client):
        url = reverse('login')
        response = client.get(url)
        assert response.status_code == 200

    def test_template_correcto(self, client):
        url = reverse('login')
        response = client.get(url)
        assert 'usuarios/login.html' in [
            getattr(t, 'name', t) for t in response.templates
        ]

    def test_post_credenciales_validas_redirect(self, client, db):
        user = UsuarioFactory(colaborador=True)
        url = reverse('login')
        response = client.post(url, {
            'username': user.username,
            'password': 'testpass123',
        })
        assert response.status_code == 302

    def test_post_credenciales_invalidas_200(self, client):
        url = reverse('login')
        response = client.post(url, {
            'username': 'noexiste',
            'password': 'mal',
        })
        assert response.status_code == 200
        assert 'usuario o contraseña invalido' in response.content.decode().lower()


# ─── user_logout ───

@pytest.mark.django_db
class TestLogout:
    """Tests de la vista user_logout."""

    def test_logout_redirige_login(self, usuario_miembro, client):
        url = reverse('logout')
        response = client.get(url)
        assert response.status_code == 302

    def test_logout_desautentica(self, usuario_miembro, client):
        url = reverse('logout')
        client.get(url)
        # Despues de logout, intentar crear articulo debe redirigir a login
        crear_url = reverse('articulos:crear_articulo')
        response = client.get(crear_url)
        assert response.status_code == 302


# ─── registro ───

@pytest.mark.django_db
class TestRegistro:
    """Tests de la vista Registro (CreateView)."""

    def test_get_200(self, client):
        url = reverse('registro')
        response = client.get(url)
        assert response.status_code == 200

    def test_template_correcto(self, client):
        url = reverse('registro')
        response = client.get(url)
        assert 'usuarios/registro.html' in [
            getattr(t, 'name', t) for t in response.templates
        ]

    def test_post_valido_redirect(self, client):
        url = reverse('registro')
        response = client.post(url, {
            'username': 'nuevo_user',
            'email': 'nuevo@test.com',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        assert response.status_code == 302
        assert Usuario.objects.filter(username='nuevo_user').exists()

    def test_post_duplicado_200(self, client, db):
        UsuarioFactory(username='existe')
        url = reverse('registro')
        response = client.post(url, {
            'username': 'existe',
            'email': 'otro@test.com',
            'first_name': 'X',
            'last_name': 'Y',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        assert response.status_code == 200

    def test_post_passwords_no_coinciden_200(self, client):
        url = reverse('registro')
        response = client.post(url, {
            'username': 'user_test',
            'email': 'test@test.com',
            'first_name': 'A',
            'last_name': 'B',
            'password1': 'Pass1',
            'password2': 'Pass2',
        })
        assert response.status_code == 200
