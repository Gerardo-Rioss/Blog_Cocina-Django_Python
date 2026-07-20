"""Vistas de la app de contacto: formulario publico y administracion de mensajes."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Contacto
from .forms import ContactoForm


def msj_contacto(request):
    """Procesa el formulario de contacto publico.

    Templates:
        contacto/contacto.html

    Context:
        form: ContactoForm vacio o con errores de validacion.
    """
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            contacto = form.save(commit=False)
            contacto.save()            
            return redirect('home')
    else:
        form = ContactoForm()
    return render(request,'contacto/contacto.html',{'form':form})

@login_required
def listarMensajes(request):
    """Lista todos los mensajes de contacto. Solo Administradores.

    Templates:
        contacto/listarMensajes.html

    Context:
        mensajes: QuerySet de todos los Contacto.
    """
    if not request.user.es_administrador():
        raise PermissionDenied()
    mensajes = Contacto.objects.all()

    contexto = {
        'mensajes': mensajes,        
    }
    return render(request, 'contacto/listarMensajes.html',contexto)

@login_required
def delete_mensaje(request, mensaje_id):
    """Elimina un mensaje de contacto. Solo Administradores.

    Args:
        mensaje_id: ID del Contacto a eliminar.

    Redirect:
        Listado de mensajes tras eliminacion.
    """
    mensaje = get_object_or_404(Contacto, id=mensaje_id)
    if not request.user.es_administrador():
        raise PermissionDenied()
    mensaje.delete()
    return redirect('contacto:mensajes')