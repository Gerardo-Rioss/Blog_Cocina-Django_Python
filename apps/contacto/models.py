"""Modelo de la app de contacto."""

from django.db import models


class Contacto(models.Model):
    """Mensaje de contacto enviado por un visitante del sitio.

    Attributes:
        nombre (CharField): Nombre de la persona que contacta.
        email (EmailField): Correo electronico de contacto.
        telefono (CharField): Telefono de contacto.
        mensaje (TextField): Contenido del mensaje.
        fecha (DateTimeField): Fecha de envio automatica.
    """
    nombre = models.CharField(max_length=150)
    email = models.EmailField(max_length=150)
    telefono = models.CharField(max_length=20)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Representacion en string: el nombre de la persona."""
        return self.nombre
