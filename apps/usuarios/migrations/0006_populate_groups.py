# Data migration: crea grupos Miembro, Colaborador, Administrador
# y asigna usuarios existentes segun su tipo_usuario actual.
from django.db import migrations

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


def crear_grupos_y_asignar(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Usuario = apps.get_model('usuarios', 'Usuario')

    # 1. Crear grupos si no existen
    for nombre in GROUPS:
        Group.objects.get_or_create(name=nombre)

    # 2. Mapear usuarios existentes
    for user in Usuario.objects.all():
        grupo_nombre = GRUPO_MAP.get(user.tipo_usuario, 'Miembro')
        grupo = Group.objects.get(name=grupo_nombre)
        user.groups.add(grupo)


def revertir(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_alter_usuario_tipo_usuario'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(crear_grupos_y_asignar, revertir),
    ]
