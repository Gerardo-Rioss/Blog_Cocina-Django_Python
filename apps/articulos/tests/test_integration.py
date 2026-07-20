"""Tests de integracion: flujo completo end-to-end con roles.

Simula el recorrido de usuarios reales:
registro → login → asignar rol → CRUD articulos → comentarios → eliminacion.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario
from apps.articulos.models import Articulo, Comentario
from apps.articulos.tests.factories import CategoriaFactory
from apps.usuarios.tests.factories import UsuarioFactory


def _imagen_test():
    """Helper: imagen SimpleUploadedFile para tests de POST (1x1 GIF valido)."""
    return SimpleUploadedFile(
        'test.jpg',
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        content_type='image/gif',
    )


@pytest.mark.django_db
class TestFlujoCompleto:
    """Flujo end-to-end: registro, login, articulos, comentarios, eliminacion."""

    def test_flujo_colaborador_crea_edita_articulo(self, client):
        """Colaborador: login → crear articulo → editar → visible en listado."""
        # 1. Crear usuario colaborador directamente
        colab = UsuarioFactory(colaborador=True)
        colab.set_password('testpass123')
        colab.save()
        login_ok = client.login(username=colab.username, password='testpass123')
        assert login_ok

        # 2. Crear categoria y articulo
        cat = CategoriaFactory(descripcion='Recetas')
        crear_url = reverse('articulos:crear_articulo')
        response = client.post(crear_url, {
            'titulo': 'Mi Receta de Pasta',
            'contenido_breve': 'Una receta breve.',
            'contenido_completo': 'Contenido completo de la receta de pasta.',
            'categoria_articulo': cat.pk,
            'imagen': _imagen_test(),
        })
        assert response.status_code == 302
        art = Articulo.objects.get(titulo='Mi Receta de Pasta')
        assert art.usuario_articulo == colab

        # 3. Ver en listado
        listado_url = reverse('articulos:listar_articulos')
        response = client.get(listado_url)
        assert response.status_code == 200
        assert 'Mi Receta de Pasta' in response.content.decode()

        # 4. Editar articulo
        editar_url = reverse('articulos:editar_articulo', kwargs={'pk': art.pk})
        response = client.get(editar_url)
        assert response.status_code == 200
        response = client.post(editar_url, {
            'titulo': 'Pasta al Pesto (Editada)',
            'contenido_breve': art.contenido_breve,
            'contenido_completo': art.contenido_completo,
            'categoria_articulo': cat.pk,
            'imagen': _imagen_test(),
        })
        assert response.status_code == 302
        art.refresh_from_db()
        assert art.titulo == 'Pasta al Pesto (Editada)'

        # 5. Miembro comenta el articulo
        miembro = UsuarioFactory(miembro=True)
        miembro.set_password('pass123')
        miembro.save()
        client.login(username=miembro.username, password='pass123')
        comentar_url = reverse(
            'articulos:agregar_comentario',
            kwargs={'articulo_id': art.pk},
        )
        response = client.post(comentar_url, {'comentario': 'Que rica receta!'})
        assert response.status_code == 302
        assert Comentario.objects.filter(
            comentario='Que rica receta!',
            usuario_comentario=miembro,
        ).exists()

        # 6. Miembro intenta eliminar el articulo del colaborador (debe fallar)
        eliminar_url = reverse(
            'articulos:eliminar_articulo',
            kwargs={'pk': art.pk},
        )
        response = client.post(eliminar_url)
        assert response.status_code == 302
        assert Articulo.objects.filter(pk=art.pk).exists()

        # 7. Admin elimina el comentario del miembro
        admin = UsuarioFactory(administrador=True)
        admin.set_password('admin123')
        admin.save()
        client.login(username=admin.username, password='admin123')
        comentario = Comentario.objects.get(comentario='Que rica receta!')
        del_com_url = reverse(
            'articulos:eliminar_comentario',
            kwargs={'comentario_id': comentario.pk},
        )
        response = client.post(del_com_url)
        assert response.status_code == 302
        assert not Comentario.objects.filter(pk=comentario.pk).exists()

        # 8. Admin elimina el articulo
        response = client.post(eliminar_url)
        assert response.status_code == 302
        assert not Articulo.objects.filter(pk=art.pk).exists()

    def test_flujo_anonimo_redirigido(self, cliente_anonimo, articulo):
        """Anonimo: intenta comentar → redirigido a login."""
        comentar_url = reverse(
            'articulos:agregar_comentario',
            kwargs={'articulo_id': articulo.pk},
        )
        response = cliente_anonimo.post(comentar_url, {'comentario': 'Hola!'})
        assert response.status_code == 302
        assert '/usuarios/login/' in response.url

    def test_flujo_registro_login_crea_articulo(self, client):
        """Registro → login → crear articulo (flujo desde cero)."""
        # 1. Registro
        reg_url = reverse('registro')
        response = client.post(reg_url, {
            'username': 'chef_nuevo',
            'email': 'chef@test.com',
            'first_name': 'Chef',
            'last_name': 'Nuevo',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        assert response.status_code == 302
        user = Usuario.objects.get(username='chef_nuevo')
        assert user.tipo_usuario == 'Miembro'

        # 2. Login
        login_ok = client.login(username='chef_nuevo', password='TestPass123!')
        assert login_ok

        # 3. Miembro intenta crear articulo → 403
        crear_url = reverse('articulos:crear_articulo')
        response = client.get(crear_url)
        assert response.status_code == 403

        # 4. Admin promueve a Colaborador via ORM
        from django.contrib.auth.models import Group
        grupo_colab, _ = Group.objects.get_or_create(name='Colaborador')
        user.groups.add(grupo_colab)
        Usuario.objects.filter(pk=user.pk).update(tipo_usuario='Colaborador')
        user.refresh_from_db()
        assert user.es_colaborador()

        # 5. Ahora puede crear articulo
        cat = CategoriaFactory()
        response = client.post(crear_url, {
            'titulo': 'Articulo del Chef',
            'contenido_breve': 'Breve descripcion.',
            'contenido_completo': 'Contenido completo del chef nuevo.',
            'categoria_articulo': cat.pk,
            'imagen': _imagen_test(),
        })
        assert response.status_code == 302
        assert Articulo.objects.filter(titulo='Articulo del Chef').exists()
