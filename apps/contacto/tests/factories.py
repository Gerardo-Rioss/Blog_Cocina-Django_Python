"""Factory para el modelo Contacto."""

import factory
from apps.contacto.models import Contacto


class ContactoFactory(factory.django.DjangoModelFactory):
    """Factory para Contacto. Genera datos validos para todos los campos requeridos."""

    class Meta:
        model = Contacto

    nombre = factory.Faker('name')
    email = factory.Faker('email')
    telefono = factory.Faker('phone_number')
    mensaje = factory.Faker('paragraph', nb_sentences=3)
