"""Tests de formularios de la app usuarios: RegistroForm."""

import pytest
from apps.usuarios.forms import RegistroForm


@pytest.mark.django_db
class TestRegistroForm:
    """Tests del formulario RegistroForm (UserCreationForm custom)."""

    def test_form_valido_con_datos_correctos(self):
        """Form es valido con todos los campos requeridos llenos."""
        data = {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'username': 'juanperez',
            'email': 'juan@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegistroForm(data=data)
        assert form.is_valid(), f'Errores: {form.errors}'

    def test_form_crea_usuario(self, db):
        """Form valido crea un Usuario con los datos correctos."""
        data = {
            'first_name': 'Maria',
            'last_name': 'Gomez',
            'username': 'mariagomez',
            'email': 'maria@test.com',
            'password1': 'SecurePass456!',
            'password2': 'SecurePass456!',
        }
        form = RegistroForm(data=data)
        assert form.is_valid()
        user = form.save()
        assert user.pk is not None
        assert user.username == 'mariagomez'
        assert user.email == 'maria@test.com'
        assert user.first_name == 'Maria'
        assert user.last_name == 'Gomez'

    def test_form_invalido_sin_first_name(self):
        """Form es invalido si first_name esta vacio."""
        data = {
            'first_name': '',
            'last_name': 'Perez',
            'username': 'testuser',
            'email': 'test@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegistroForm(data=data)
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_form_invalido_sin_email(self):
        """Form es invalido si email esta vacio."""
        data = {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'username': 'testuser',
            'email': '',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegistroForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_form_invalido_password_mismatch(self):
        """Form es invalido si password1 y password2 no coinciden."""
        data = {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'username': 'juanperez',
            'email': 'juan@test.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass!',
        }
        form = RegistroForm(data=data)
        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_form_invalido_username_duplicado(self, db):
        """Form es invalido si el username ya existe."""
        from apps.usuarios.tests.factories import UsuarioFactory
        UsuarioFactory(username='existente')
        data = {
            'first_name': 'Otro',
            'last_name': 'Usuario',
            'username': 'existente',
            'email': 'otro@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegistroForm(data=data)
        assert not form.is_valid()
        assert 'username' in form.errors

    def test_form_imagen_opcional(self):
        """Form es valido sin imagen (campo opcional)."""
        data = {
            'first_name': 'Pedro',
            'last_name': 'Lopez',
            'username': 'pedrolopez',
            'email': 'pedro@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegistroForm(data=data)
        assert form.is_valid(), f'Errores: {form.errors}'
