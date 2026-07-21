"""Comando para resetear articulos y re-asignar imagenes Unsplash correctas."""

import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.articulos.models import Articulo, Comentario
from apps.contacto.models import Contacto


# Mapeo exacto: indice de TITULOS en seed_data → imagen correspondiente
IMAGENES_POR_ARTICULO = [
    'risotto.jpg', 'seafood.jpg', 'dessert.jpg', 'sushi.jpg',
    'tacos.jpg', 'soup.jpg', 'pasta.jpg', 'seafood.jpg',
    'chocolate.jpg', 'curry.jpg', 'vegetables.jpg', 'steak.jpg',
    'cake.jpg', 'noodles.jpg', 'steak.jpg', 'bread.jpg',
    'pancakes.jpg', 'soup.jpg', 'pizza.jpg', 'bread.jpg',
]


class Command(BaseCommand):
    help = 'Resetea articulos y re-asigna imagenes Unsplash reales'

    def handle(self, *args, **options):
        dest_dir = settings.MEDIA_ROOT / 'articulos'
        dest_dir.mkdir(parents=True, exist_ok=True)

        # 1. Copiar las imagenes de Unsplash desde el repo a media/
        repo_media = Path(settings.BASE_DIR) / 'media' / 'articulos'
        copiadas = 0
        for img in IMAGENES_POR_ARTICULO:
            src = repo_media / img
            if src.exists():
                dst = dest_dir / img
                shutil.copy2(src, dst)
                copiadas += 1
        self.stdout.write(f'  ✅ {copiadas} imagenes copiadas a media/')

        # 2. Eliminar articulos viejos (con imagenes genericas)
        viejos = Articulo.objects.filter(imagen__startswith='articulos/articulo_')
        self.stdout.write(f'  🗑️  {viejos.count()} articulos con imagenes genericas eliminados')
        viejos.delete()

        # 3. Re-asignar imagenes correctas a los articulos restantes
        #    (los creados por seed_data que usaron el fallback de nombres random)
        for i, art in enumerate(Articulo.objects.all().order_by('fecha_publicacion')):
            nombre_img = IMAGENES_POR_ARTICULO[i % len(IMAGENES_POR_ARTICULO)]
            art.imagen.name = f'articulos/{nombre_img}'
            art.save(update_fields=['imagen'])
        self.stdout.write(f'  ✅ {Articulo.objects.count()} articulos con imagenes correctas')

        # 4. Verificar
        malos = Articulo.objects.filter(imagen__startswith='articulos/articulo_')
        if malos.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠️ Quedan {malos.count()} articulos con imagenes genericas'))
        else:
            self.stdout.write(self.style.SUCCESS('🎉 Todas las imagenes son reales!'))
