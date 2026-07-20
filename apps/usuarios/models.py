from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_save
from django.dispatch import receiver


class Usuario(AbstractUser):
    """Modelo de usuario personalizado con roles via tipo_usuario y grupos.

    Los grupos Django son el mecanismo canonico de autorizacion.
    tipo_usuario se mantiene como campo de datos sincronizado por senal.
    """
    imagen = models.ImageField(upload_to='usuarios', default='default-user.png')

    # USUARIOS:
    USUARIO_COLABORADOR = 'Colaborador'
    USUARIO_MIEMBRO = 'Miembro'
    USUARIO_ADMINISTRADOR = 'Administrador'

    TIPO_DE_USUARIO = [
        (USUARIO_MIEMBRO, 'Miembro'),
        (USUARIO_COLABORADOR, 'Colaborador'),
        (USUARIO_ADMINISTRADOR, 'Administrador'),
    ]

    tipo_usuario = models.CharField(
        max_length=20, choices=TIPO_DE_USUARIO, default=USUARIO_MIEMBRO
    )

    def __str__(self):
        return self.username

    # ─── Helpers de autorizacion ───

    def es_miembro(self):
        """Usuario registrado basico. Solo lectura de contenido publico."""
        return self.groups.filter(name='Miembro').exists()

    def es_colaborador(self):
        """Puede crear y editar sus propios articulos."""
        return self.groups.filter(name='Colaborador').exists()

    def es_administrador(self):
        """Control total: CRUD sobre cualquier contenido + acceso a mensajes."""
        return self.groups.filter(name='Administrador').exists() or self.is_superuser

    def puede_editar_articulo(self, articulo):
        """Verifica si el usuario puede editar un articulo.

        Un usuario puede editar si es administrador o si es el autor.

        Args:
            articulo: Instancia de Articulo a verificar.

        Returns:
            bool: True si el usuario puede editar.
        """
        return self.es_administrador() or articulo.usuario_articulo == self

    def puede_eliminar_articulo(self, articulo):
        """Verifica si el usuario puede eliminar un articulo.

        Un usuario puede eliminar si es administrador o si es el autor.

        Args:
            articulo: Instancia de Articulo a verificar.

        Returns:
            bool: True si el usuario puede eliminar.
        """
        return self.es_administrador() or articulo.usuario_articulo == self

    def puede_editar_comentario(self, comentario):
        """Verifica si el usuario puede editar un comentario.

        Solo el autor o un administrador pueden editar.

        Args:
            comentario: Instancia de Comentario a verificar.

        Returns:
            bool: True si el usuario puede editar.
        """
        return self.es_administrador() or comentario.usuario_comentario == self


@receiver(post_save, sender=Usuario)
def sincronizar_grupo_usuario(sender, instance, created, **kwargs):
    """Sincroniza el grupo Django segun tipo_usuario.

    Usa update() en el QuerySet para no disparar post_save recursivo.
    Se ejecuta en created=True Y en updates para mantener sincronia.
    """
    if instance.is_superuser:
        grupo_nombre = 'Administrador'
        tipo = Usuario.USUARIO_ADMINISTRADOR
    elif instance.tipo_usuario == Usuario.USUARIO_ADMINISTRADOR:
        grupo_nombre = 'Administrador'
        tipo = Usuario.USUARIO_ADMINISTRADOR
    elif instance.tipo_usuario == Usuario.USUARIO_COLABORADOR:
        grupo_nombre = 'Colaborador'
        tipo = Usuario.USUARIO_COLABORADOR
    else:
        grupo_nombre = 'Miembro'
        tipo = Usuario.USUARIO_MIEMBRO

    grupo, _ = Group.objects.get_or_create(name=grupo_nombre)
    instance.groups.add(grupo)

    # Si el tipo_usuario no coincide con lo que deberia ser,
    # actualizar SIN disparar senal
    if instance.tipo_usuario != tipo:
        Usuario.objects.filter(pk=instance.pk).update(tipo_usuario=tipo)
