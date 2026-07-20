"""Tests del formulario ContactoForm.

Verifica validacion con campos requeridos, email valido/invalido,
y campos vacios.
"""

import pytest
from apps.contacto.forms import ContactoForm


@pytest.mark.django_db
class TestContactoForm:
    """Tests del formulario ContactoForm."""

    def test_form_valido_con_todos_los_campos(self):
        """Form es valido con nombre, email, telefono y mensaje."""
        data = {
            'nombre': 'Juan Perez',
            'email': 'juan@test.com',
            'telefono': '123456789',
            'mensaje': 'Hola, me gusta el blog.',
        }
        form = ContactoForm(data=data)
        assert form.is_valid(), f'Errores: {form.errors}'

    def test_form_invalido_sin_nombre(self):
        """Form es invalido si nombre esta vacio."""
        data = {
            'nombre': '',
            'email': 'juan@test.com',
            'telefono': '123456789',
            'mensaje': 'Hola.',
        }
        form = ContactoForm(data=data)
        assert not form.is_valid()
        assert 'nombre' in form.errors

    def test_form_invalido_sin_email(self):
        """Form es invalido si email esta vacio."""
        data = {
            'nombre': 'Juan',
            'email': '',
            'telefono': '123456789',
            'mensaje': 'Hola.',
        }
        form = ContactoForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_form_invalido_sin_mensaje(self):
        """Form es invalido si mensaje esta vacio."""
        data = {
            'nombre': 'Juan',
            'email': 'juan@test.com',
            'telefono': '123456789',
            'mensaje': '',
        }
        form = ContactoForm(data=data)
        assert not form.is_valid()
        assert 'mensaje' in form.errors

    def test_form_invalido_email_malformado(self):
        """Form es invalido si el email no tiene formato valido."""
        data = {
            'nombre': 'Juan',
            'email': 'no-es-un-email',
            'telefono': '123456789',
            'mensaje': 'Hola.',
        }
        form = ContactoForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_form_invalido_sin_telefono(self):
        """Form es invalido si telefono esta vacio."""
        data = {
            'nombre': 'Juan',
            'email': 'juan@test.com',
            'telefono': '',
            'mensaje': 'Hola.',
        }
        form = ContactoForm(data=data)
        assert not form.is_valid()
        assert 'telefono' in form.errors
