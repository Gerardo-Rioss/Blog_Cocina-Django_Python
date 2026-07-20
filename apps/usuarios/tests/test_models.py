"""Tests unitarios del modelo Usuario:

- Creacion basica con create_user()
- __str__ retorna el username
- tipo_usuario default es 'Miembro'
- Username unico
- Helpers de autorizacion: es_miembro, es_colaborador, es_administrador
- Helpers de ownership: puede_editar_articulo, puede_eliminar_articulo,
  puede_editar_comentario
"""

import pytest
from django.db import IntegrityError
from apps.usuarios.models import Usuario
from apps.usuarios.tests.factories import UsuarioFactory


@pytest.mark.django_db
class TestUsuarioCreacion:
    """Tests de creacion del modelo Usuario."""

    def test_crear_usuario_basico(self):
        """Un usuario se crea correctamente con create_user()."""
        user = Usuario.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
        )
        assert user.pk is not None
        assert user.username == 'testuser'
        assert user.email == 'test@test.com'
        assert user.check_password('testpass123')

    def test_str_retorna_username(self):
        """__str__ retorna el username."""
        user = UsuarioFactory.build(username='pepe')
        assert str(user) == 'pepe'

    def test_tipo_usuario_default_es_miembro(self):
        """El tipo_usuario default es 'Miembro'."""
        user = UsuarioFactory.build()
        assert user.tipo_usuario == Usuario.USUARIO_MIEMBRO

    def test_is_active_default_es_true(self, db):
        """Usuario nuevo tiene is_active=True por defecto."""
        user = UsuarioFactory()
        assert user.is_active is True

    def test_username_unico(self, db):
        """No se pueden crear dos usuarios con el mismo username."""
        UsuarioFactory(username='unico123')
        with pytest.raises(IntegrityError):
            UsuarioFactory(username='unico123')


@pytest.mark.django_db
class TestUsuarioHelpers:
    """Tests de los helpers de autorizacion en el modelo Usuario."""

    def test_es_miembro(self, usuario_miembro):
        """Usuario con grupo Miembro: es_miembro() retorna True."""
        assert usuario_miembro.es_miembro() is True
        assert usuario_miembro.es_colaborador() is False
        assert usuario_miembro.es_administrador() is False

    def test_es_colaborador(self, usuario_colaborador):
        """Usuario con grupo Colaborador: es_colaborador() retorna True."""
        assert usuario_colaborador.es_miembro() is False
        assert usuario_colaborador.es_colaborador() is True
        assert usuario_colaborador.es_administrador() is False

    def test_es_administrador(self, usuario_administrador):
        """Usuario con grupo Administrador: es_administrador() retorna True."""
        assert usuario_administrador.es_miembro() is False
        assert usuario_administrador.es_colaborador() is False
        assert usuario_administrador.es_administrador() is True

    def test_superuser_es_administrador(self):
        """Un superuser es administrador aunque no tenga grupo explicito."""
        user = UsuarioFactory(is_superuser=True, administrador=True)
        assert user.es_administrador() is True


@pytest.mark.django_db
class TestUsuarioOwnershipHelpers:
    """Tests de los helpers de ownership (puede_editar_*, puede_eliminar_*)."""

    def test_puede_editar_articulo_propio(self, usuario_colaborador, db):
        """Colaborador puede editar su propio articulo."""
        from apps.articulos.tests.factories import ArticuloFactory
        articulo = ArticuloFactory(usuario_articulo=usuario_colaborador)
        assert usuario_colaborador.puede_editar_articulo(articulo) is True

    def test_puede_editar_articulo_ajeno(self, usuario_colaborador, db):
        """Colaborador NO puede editar articulo ajeno."""
        from apps.articulos.tests.factories import ArticuloFactory
        otro = UsuarioFactory(colaborador=True)
        articulo = ArticuloFactory(usuario_articulo=otro)
        assert usuario_colaborador.puede_editar_articulo(articulo) is False

    def test_admin_puede_editar_articulo_ajeno(self, usuario_administrador, db):
        """Administrador puede editar cualquier articulo."""
        from apps.articulos.tests.factories import ArticuloFactory
        otro = UsuarioFactory(colaborador=True)
        articulo = ArticuloFactory(usuario_articulo=otro)
        assert usuario_administrador.puede_editar_articulo(articulo) is True

    def test_puede_eliminar_articulo_propio(self, usuario_colaborador, db):
        """Colaborador puede eliminar su propio articulo."""
        from apps.articulos.tests.factories import ArticuloFactory
        articulo = ArticuloFactory(usuario_articulo=usuario_colaborador)
        assert usuario_colaborador.puede_eliminar_articulo(articulo) is True

    def test_puede_eliminar_articulo_ajeno(self, usuario_colaborador, db):
        """Colaborador NO puede eliminar articulo ajeno."""
        from apps.articulos.tests.factories import ArticuloFactory
        otro = UsuarioFactory(colaborador=True)
        articulo = ArticuloFactory(usuario_articulo=otro)
        assert usuario_colaborador.puede_eliminar_articulo(articulo) is False

    def test_admin_puede_eliminar_articulo_ajeno(self, usuario_administrador, db):
        """Administrador puede eliminar cualquier articulo."""
        from apps.articulos.tests.factories import ArticuloFactory
        otro = UsuarioFactory(colaborador=True)
        articulo = ArticuloFactory(usuario_articulo=otro)
        assert usuario_administrador.puede_eliminar_articulo(articulo) is True

    def test_puede_editar_comentario_propio(self, usuario_colaborador, db):
        """Colaborador puede editar su propio comentario."""
        from apps.articulos.tests.factories import ComentarioFactory
        comentario = ComentarioFactory(usuario_comentario=usuario_colaborador)
        assert usuario_colaborador.puede_editar_comentario(comentario) is True

    def test_puede_editar_comentario_ajeno(self, usuario_colaborador, db):
        """Colaborador NO puede editar comentario ajeno."""
        from apps.articulos.tests.factories import ComentarioFactory
        otro = UsuarioFactory(colaborador=True)
        comentario = ComentarioFactory(usuario_comentario=otro)
        assert usuario_colaborador.puede_editar_comentario(comentario) is False

    def test_admin_puede_editar_comentario_ajeno(self, usuario_administrador, db):
        """Administrador puede editar cualquier comentario."""
        from apps.articulos.tests.factories import ComentarioFactory
        otro = UsuarioFactory(colaborador=True)
        comentario = ComentarioFactory(usuario_comentario=otro)
        assert usuario_administrador.puede_editar_comentario(comentario) is True
