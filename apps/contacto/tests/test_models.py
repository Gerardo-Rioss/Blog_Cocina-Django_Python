"""Tests unitarios del modelo Contacto.

Cubre creacion con campos requeridos, __str__, y validacion de email.
"""

import pytest
from django.core.exceptions import ValidationError
from apps.contacto.models import Contacto
from apps.contacto.tests.factories import ContactoFactory


@pytest.mark.django_db
class TestContacto:
    """Tests del modelo Contacto."""

    def test_crear_contacto(self):
        """Contacto se crea correctamente con nombre, email y mensaje."""
        c = ContactoFactory(
            nombre='Maria Gomez',
            email='maria@test.com',
            mensaje='Me gusta el blog',
        )
        assert c.pk is not None
        assert c.nombre == 'Maria Gomez'
        assert c.email == 'maria@test.com'
        assert c.mensaje == 'Me gusta el blog'

    def test_str_retorna_nombre(self):
        """__str__ retorna el nombre del contacto."""
        c = ContactoFactory.build(nombre='Juan Perez')
        assert str(c) == 'Juan Perez'

    def test_campos_requeridos(self, db):
        """nombre, email y mensaje son requeridos."""
        c = Contacto(nombre='', email='', mensaje='')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_email_invalido_rechazado(self, db):
        """EmailField rechaza emails con formato invalido."""
        c = Contacto(nombre='Test', email='no-es-un-email', mensaje='Hola')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_email_valido_aceptado(self, db):
        """EmailField acepta emails con formato valido."""
        c = Contacto(nombre='Test', email='valido@test.com', telefono='123456789', mensaje='Hola')
        # No debe lanzar ValidationError
        c.full_clean()
