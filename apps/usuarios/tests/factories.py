"""Factories para el modelo Usuario con traits por rol."""

import factory
from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario


def _asignar_grupo_exclusivo(usuario, grupo_nombre):
    """Asigna SOLO el grupo especificado, removiendo cualquier otro."""
    # Limpiar todos los grupos existentes
    usuario.groups.clear()
    # Asignar el grupo correcto
    grupo, _ = Group.objects.get_or_create(name=grupo_nombre)
    usuario.groups.add(grupo)
    usuario.tipo_usuario = grupo_nombre
    Usuario.objects.filter(pk=usuario.pk).update(tipo_usuario=grupo_nombre)


class UsuarioFactory(factory.django.DjangoModelFactory):
    """Factory base para Usuario.

    Traits disponibles:
        miembro: Usuario con grupo y tipo 'Miembro'.
        colaborador: Usuario con grupo y tipo 'Colaborador'.
        administrador: Usuario con grupo y tipo 'Administrador' (superuser).

    Uso:
        UsuarioFactory()  # Miembro por defecto
        UsuarioFactory(colaborador=True)
        UsuarioFactory(administrador=True)
    """

    class Meta:
        model = Usuario

    username = factory.Sequence(lambda n: f'usuario{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@test.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Crea el usuario y asigna grupo segun el trait usado.

        Permite que el signal post_save se ejecute normalmente,
        pero luego sobrescribe los grupos para que SOLO tenga el
        grupo correspondiente al trait.
        """
        grupo_nombre = kwargs.pop('GRUPO_TRAIT', None)
        is_staff = kwargs.pop('is_staff', False)
        is_superuser = kwargs.pop('is_superuser', False)

        usuario = model_class(*args, **kwargs)
        usuario.is_staff = is_staff
        usuario.is_superuser = is_superuser
        usuario.save()

        # El signal post_save ya asigno 'Miembro' o lo que corresponda.
        # Sobrescribimos con el grupo correcto (exclusivo).
        asignar = grupo_nombre or 'Miembro'
        _asignar_grupo_exclusivo(usuario, asignar)

        return usuario

    class Params:
        miembro = factory.Trait(GRUPO_TRAIT='Miembro')
        colaborador = factory.Trait(
            GRUPO_TRAIT='Colaborador', is_staff=True,
        )
        administrador = factory.Trait(
            GRUPO_TRAIT='Administrador', is_staff=True, is_superuser=True,
        )
