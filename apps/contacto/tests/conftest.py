"""Fixtures compartidos para tests de la app contacto."""

import pytest
from apps.usuarios.tests.factories import UsuarioFactory
from .factories import ContactoFactory


@pytest.fixture
def contacto(db):
    """Mensaje de contacto persistido."""
    return ContactoFactory()


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
