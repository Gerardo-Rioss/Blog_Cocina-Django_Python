"""Tests de la senal post_save sincronizar_grupo_usuario.

Verifica:
- Creacion de usuario normal asigna grupo 'Miembro' y tipo_usuario 'Miembro'.
- Creacion de superuser asigna grupo 'Administrador' y tipo_usuario 'Administrador'.
- Actualizacion de tipo_usuario sincroniza el grupo.
- La senal no causa recursion (no llama a instance.save()).
"""

import pytest
from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario
from apps.usuarios.tests.factories import UsuarioFactory


@pytest.mark.django_db
class TestSenalSincronizarGrupo:
    """Tests de la senal sincronizar_grupo_usuario."""

    def test_usuario_nuevo_asigna_miembro(self):
        """Al crear Usuario sin tipo_usuario, la senal asigna 'Miembro'."""
        user = UsuarioFactory()  # sin trait → _grupo=None → la senal maneja el else
        user.refresh_from_db()
        # Si no se asigno via factory, la senal post_save deberia asignarlo
        # Pero como la factory asigna via update(), la senal sincroniza en siguiente save
        # Para probar la senal pura: creamos via ORM sin factory
        user2 = Usuario.objects.create_user(
            username='senaltest1', password='testpass123',
        )
        # La senal post_save debio dispararse en create_user
        assert user2.tipo_usuario == Usuario.USUARIO_MIEMBRO
        assert user2.groups.filter(name='Miembro').exists()

    def test_superuser_asigna_administrador(self):
        """Al crear superuser, la senal asigna 'Administrador'."""
        user = Usuario.objects.create_superuser(
            username='admintest', email='admin@test.com', password='testpass123',
        )
        user.refresh_from_db()
        assert user.tipo_usuario == Usuario.USUARIO_ADMINISTRADOR
        assert user.groups.filter(name='Administrador').exists()

    def test_colaborador_asigna_grupo(self):
        """Usuario con tipo_usuario Colaborador → grupo Colaborador."""
        user = Usuario.objects.create_user(
            username='colabtest', password='testpass123',
        )
        # La senal default asigna Miembro. Forzamos Colaborador via update()
        Usuario.objects.filter(pk=user.pk).update(
            tipo_usuario=Usuario.USUARIO_COLABORADOR,
        )
        # Ahora guardamos para que la senal sincronice el grupo
        user.refresh_from_db()
        user.save()
        assert user.groups.filter(name='Colaborador').exists()

    def test_administrador_asigna_grupo(self):
        """Usuario con tipo_usuario Administrador → grupo Administrador."""
        user = Usuario.objects.create_user(
            username='admingrupo', password='testpass123',
        )
        Usuario.objects.filter(pk=user.pk).update(
            tipo_usuario=Usuario.USUARIO_ADMINISTRADOR,
        )
        user.refresh_from_db()
        user.save()
        assert user.groups.filter(name='Administrador').exists()

    def test_no_recursion_al_actualizar(self):
        """Actualizar usuario sin cambiar tipo_usuario NO causa recursion."""
        user = Usuario.objects.create_user(
            username='norecur', password='testpass123',
        )
        # Obtener el tipo_usuario asignado por la senal inicial
        tipo_actual = user.tipo_usuario
        # Guardar sin cambios — la senal no debe modificar nada
        user.first_name = 'Test'
        user.save()
        user.refresh_from_db()
        # El tipo_usuario debe seguir siendo el mismo
        assert user.tipo_usuario == tipo_actual
        # No debe haber duplicacion de grupos
        assert user.groups.filter(name='Miembro').count() == 1

    def test_superuser_creado_con_factory(self, usuario_administrador):
        """Usuario creado con trait administrador tiene grupo y tipo correctos."""
        assert usuario_administrador.tipo_usuario == Usuario.USUARIO_ADMINISTRADOR
        assert usuario_administrador.groups.filter(name='Administrador').exists()

    def test_update_queryset_no_dispara_senal(self, db):
        """QuerySet.update() no dispara la senal post_save.

        Esta es una limitacion conocida de Django: update() bypassea save().
        El test documenta el comportamiento esperado.
        """
        user = Usuario.objects.create_user(
            username='updatetest', password='testpass123',
        )
        # La senal inicial asigno Miembro
        grupo_inicial = user.groups.first().name if user.groups.exists() else None
        # update() NO dispara senal → el grupo NO cambia
        Usuario.objects.filter(pk=user.pk).update(
            tipo_usuario=Usuario.USUARIO_ADMINISTRADOR,
        )
        user.refresh_from_db()
        # El grupo sigue siendo el mismo porque la senal no se disparo
        grupo_final = user.groups.first().name if user.groups.exists() else None
        assert grupo_final == grupo_inicial
