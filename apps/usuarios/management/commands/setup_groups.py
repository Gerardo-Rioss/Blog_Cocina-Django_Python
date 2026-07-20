"""Comando de gestion: crea grupos de autorizacion y reconcilia membresias.

Uso:
    python manage.py setup_groups

Crea los grupos Miembro, Colaborador y Administrador si no existen,
y asigna cada usuario al grupo que corresponde segun su tipo_usuario.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario

GROUPS = ['Miembro', 'Colaborador', 'Administrador']

GRUPO_MAP = {
    'Miembro': 'Miembro',
    'Colaborador': 'Colaborador',
    'Superusuario': 'Administrador',
    'SuperUsuario': 'Administrador',
    'Administrador': 'Administrador',
    'Visitante': 'Miembro',
    'publico': 'Miembro',
    'colaborador': 'Colaborador',
}


class Command(BaseCommand):
    help = 'Crea grupos de autorizacion y reconcilia membresias de usuarios.'

    def handle(self, *args, **options):
        # 1. Crear grupos
        for nombre in GROUPS:
            grupo, created = Group.objects.get_or_create(name=nombre)
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Grupo "{nombre}" creado.'
                ))
            else:
                self.stdout.write(f'Grupo "{nombre}" ya existe.')

        # 2. Asignar usuarios a grupos
        asignados = 0
        for user in Usuario.objects.all():
            grupo_nombre = GRUPO_MAP.get(user.tipo_usuario, 'Miembro')
            grupo = Group.objects.get(name=grupo_nombre)
            if not user.groups.filter(pk=grupo.pk).exists():
                user.groups.add(grupo)
                asignados += 1

        self.stdout.write(self.style.SUCCESS(
            f'{asignados} usuarios asignados a sus grupos.'
        ))
