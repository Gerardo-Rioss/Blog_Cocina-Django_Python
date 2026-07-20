"""Fixtures compartidos para tests de la app usuarios."""

import pytest
from .factories import UsuarioFactory


@pytest.fixture
def usuario() -> 'Usuario':
    """Usuario basico sin grupo ni tipo_usuario asignado."""
    return UsuarioFactory.build()


@pytest.fixture
def usuario_miembro(db) -> 'Usuario':
    """Usuario persistido con rol Miembro."""
    return UsuarioFactory(miembro=True)


@pytest.fixture
def usuario_colaborador(db) -> 'Usuario':
    """Usuario persistido con rol Colaborador."""
    return UsuarioFactory(colaborador=True)


@pytest.fixture
def usuario_administrador(db) -> 'Usuario':
    """Usuario persistido con rol Administrador."""
    return UsuarioFactory(administrador=True)
