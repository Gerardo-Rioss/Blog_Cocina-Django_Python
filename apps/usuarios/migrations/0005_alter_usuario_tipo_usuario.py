# Generated manually — simplifica choices: elimina Visitante,
# reemplaza Superusuario por Administrador.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_alter_usuario_tipo_usuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='tipo_usuario',
            field=models.CharField(
                choices=[
                    ('Miembro', 'Miembro'),
                    ('Colaborador', 'Colaborador'),
                    ('Administrador', 'Administrador'),
                ],
                default='Miembro',
                max_length=20,
            ),
        ),
    ]
