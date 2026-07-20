from django import forms
from .models import Contacto


class ContactoForm(forms.ModelForm):
    """Formulario de contacto publico.

    Expone los campos del modelo Contacto: nombre, email y mensaje.
    """

    class Meta:
        model = Contacto
        fields = ['nombre', 'email', 'telefono', 'mensaje']