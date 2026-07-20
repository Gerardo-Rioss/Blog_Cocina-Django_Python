"""Fixtures compartidos para tests de la app articulos."""

import pytest
from apps.usuarios.tests.factories import UsuarioFactory
from .factories import CategoriaFactory, ArticuloFactory, ComentarioFactory


@pytest.fixture
def usuario_miembro(client, db):
    """Cliente autenticado con usuario Miembro."""
    user = UsuarioFactory(miembro=True)
    client.force_login(user)
    return user


@pytest.fixture
def usuario_colaborador(client, db):
    """Cliente autenticado con usuario Colaborador."""
    user = UsuarioFactory(colaborador=True)
    client.force_login(user)
    return user


@pytest.fixture
def usuario_administrador(client, db):
    """Cliente autenticado con usuario Administrador."""
    user = UsuarioFactory(administrador=True)
    client.force_login(user)
    return user


@pytest.fixture
def cliente_anonimo(client):
    """Cliente sin autenticacion."""
    return client


@pytest.fixture
def categoria(db):
    """Categoria persistida."""
    return CategoriaFactory()


@pytest.fixture
def articulo(db):
    """Articulo persistido con categoria y usuario autor."""
    return ArticuloFactory()


@pytest.fixture
def comentario(db):
    """Comentario persistido con articulo y usuario autor."""
    return ComentarioFactory()
