"""Comando para poblar la BD con datos de prueba e imágenes reales de comida."""

import random
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario
from apps.articulos.models import Categoria, Articulo
from apps.contacto.models import Contacto


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

# ─── Datos de prueba ───

CATEGORIAS = [
    'Entradas', 'Platos Principales', 'Pastas', 'Ensaladas',
    'Sopas', 'Postres', 'Panadería', 'Cocina Internacional',
    'Comida Saludable', 'Bebidas y Cócteles',
]

USUARIOS = [
    {'username': 'admin', 'password': 'admin123', 'rol': 'Administrador'},
    {'username': 'colaborador', 'password': 'colab123', 'rol': 'Colaborador'},
    {'username': 'chef_maria', 'password': 'chef123', 'rol': 'Colaborador'},
    {'username': 'cocinero_juan', 'password': 'cocina123', 'rol': 'Colaborador'},
    {'username': 'miembro1', 'password': 'miembro123', 'rol': 'Miembro'},
    {'username': 'lector_ana', 'password': 'lector123', 'rol': 'Miembro'},
]

TITULOS = [
    'Risotto de Hongos Silvestres',           # 0  → risotto.jpg
    'Paella Valenciana Tradicional',           # 1  → seafood.jpg
    'Tiramisú Clásico Italiano',               # 2  → dessert.jpg
    'Sushi Rolls de Salmón y Palta',           # 3  → sushi.jpg
    'Tacos al Pastor con Salsa Verde',         # 4  → tacos.jpg
    'Crema de Calabaza con Jengibre',          # 5  → soup.jpg
    'Lasaña de Berenjenas y Espinacas',        # 6  → pasta.jpg
    'Ceviche Peruano de Pescado',              # 7  → seafood.jpg
    'Brownies de Chocolate Belgas',            # 8  → chocolate.jpg
    'Pollo al Curry con Arroz Basmati',        # 9  → curry.jpg
    'Gazpacho Andaluz Tradicional',            # 10 → vegetables.jpg
    'Empanadas de Carne Cortadas a Cuchillo',  # 11 → steak.jpg
    'Flan Casero con Caramelo',                # 12 → cake.jpg
    'Wok de Verduras con Tofu',                # 13 → noodles.jpg
    'Parrillada Argentina Completa',           # 14 → steak.jpg
    'Hummus de Garbanzos Casero',              # 15 → bread.jpg
    'Tarta de Manzana con Helado',             # 16 → pancakes.jpg
    'Sopa de Miso con Tofu y Wakame',          # 17 → soup.jpg
    'Pizza Napolitana con Albahaca Fresca',    # 18 → pizza.jpg
    'Budín de Pan con Pasas de Uva',           # 19 → bread.jpg
]

IMAGENES_POR_ARTICULO = [
    'risotto.jpg', 'seafood.jpg', 'dessert.jpg', 'sushi.jpg',
    'tacos.jpg', 'soup.jpg', 'pasta.jpg', 'seafood.jpg',
    'chocolate.jpg', 'curry.jpg', 'vegetables.jpg', 'steak.jpg',
    'cake.jpg', 'noodles.jpg', 'steak.jpg', 'bread.jpg',
    'pancakes.jpg', 'soup.jpg', 'pizza.jpg', 'bread.jpg',
]

CONTENIDOS_BREVES = [
    'Una receta clásica con ingredientes frescos que resalta los sabores auténticos.',
    'Descubrí cómo preparar este plato tradicional con un toque moderno.',
    'Perfecto para compartir en familia, esta receta es infalible.',
    'Una opción saludable y deliciosa que podés preparar en 30 minutos.',
    'El secreto de este plato está en la cocción lenta de los ingredientes.',
    'Combinación única de sabores que transporta a la cocina casera.',
    'Ideal para ocasiones especiales, con una presentación espectacular.',
    'Receta tradicional con un twist contemporáneo que sorprende.',
    'Fácil, rápido y con ingredientes que seguro tenés en casa.',
    'Un clásico de la cocina internacional adaptado a nuestros ingredientes.',
]

CONTENIDOS_COMPLETOS = [
    """
En una olla grande, calentá un poco de aceite de oliva y rehogá la cebolla picada hasta que esté transparente.
Agregá los hongos previamente limpios y saltealos por 5 minutos. Incorporá el arroz y mezclá bien.
De a poco, andá agregando caldo caliente mientras revolvés constantemente.
Cuando el arroz esté al dente, retirá del fuego y agregá manteca y queso parmesano rallado.
Tapá y dejá reposar 2 minutos antes de servir. Espolvoreá con perejil fresco picado.
""",
    """
Prepará el café bien cargado y dejaló enfriar. Separar las claras de las yemas.
Batí las yemas con el azúcar hasta obtener una crema clara y espesa.
Agregá el mascarpone y mezclá suavemente con movimientos envolventes.
Batí las claras a punto nieve e incorporalas a la mezcla anterior.
Armá el tiramisú en capas: una de galletas mojadas en café, una de crema, repetí.
Llevá a la heladera por al menos 4 horas. Serví espolvoreado con cacao amargo.
""",
    """
Mariná la carne de cerdo con achiote, vinagre, ajo y comino por al menos 2 horas.
Cociná la carne en una sartén bien caliente hasta que esté dorada y cocida.
Picá la carne finamente. Calentá las tortillas de maíz en un comal.
Prepará la salsa verde hirviendo tomatillos con chile serrano y cilantro.
Armá los tacos con la carne, la salsa, cebolla picada y cilantro fresco.
Acompañá con rodajas de limón y salsa picante al gusto.
""",
    """
Prepará el arroz para sushi según las instrucciones del paquete y dejaló enfriar.
Cortá el salmón en tiras finas. Pelá la palta y cortala en láminas.
Colocá una hoja de alga nori sobre la esterilla de bambú.
Extendé una capa fina de arroz, dejando un borde libre. Poné el salmón y la palta en el centro.
Enrollá con cuidado usando la esterilla y presioná suavemente. Cortá en rodajas de 2 cm.
Serví con salsa de soja, wasabi y jengibre encurtido.
""",
    """
Calentá aceite de oliva en una sartén y dorá el pollo cortado en cubos. Retirar y reservar.
En la misma sartén, rehogá cebolla, ajo y jengibre rallado. Agregá curry en polvo y cociná 1 minuto.
Incorporá la leche de coco y el caldo de pollo. Dejá hervir y agregá el pollo.
Cociná a fuego bajo por 20 minutos. Serví sobre arroz basmati blanco.
Decorá con cilantro fresco y un toque de lima.
""",
]

COMENTARIOS = [
    '¡Excelente receta! Me salió perfecta la primera vez.',
    'Agregué un poco de ajo extra y quedó espectacular.',
    'La preparé para la cena de Navidad y todos amaron.',
    '¿Se puede reemplazar la crema por leche de coco?',
    'Probé con un toque de pimentón ahumado y suma mucho.',
    'Mi abuela hacía una versión similar, qué recuerdos.',
    'La próxima vez voy a duplicar la cantidad, se fue volando.',
    'Tips: dejá reposar la masa 30 minutos antes de estirarla.',
    'Queda increíble si le agregás un poco de queso de cabra.',
    'La hice sin TACC con harina de arroz y salió buenísima.',
]

MENSAJES_CONTACTO = [
    'Hola! Me encanta el blog. ¿Podrían agregar más recetas veganas?',
    'Excelente contenido, muy bien explicado todo. Sigan así!',
    'Consulta: ¿tienen pensado hacer un curso online de cocina?',
    'Felicitaciones por el blog. Las recetas son fáciles y ricas.',
    'Me gustaría colaborar como escritor, tengo varias recetas para compartir.',
]


def _imagen_articulo(idx):
    """Abre una imagen real de comida desde media/articulos/."""
    nombre = IMAGENES_POR_ARTICULO[idx % len(IMAGENES_POR_ARTICULO)]
    ruta = BASE_DIR / 'media' / 'articulos' / nombre
    if ruta.exists() and ruta.stat().st_size > 1000:
        return File(open(ruta, 'rb'), name=nombre)
    return None


class Command(BaseCommand):
    help = 'Pobla la BD con datos de prueba e imágenes reales de comida'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Poblando base de datos con imágenes reales...')

        # 1. Categorías
        for nombre in CATEGORIAS:
            Categoria.objects.get_or_create(descripcion=nombre)
        self.stdout.write(f'  ✅ {len(CATEGORIAS)} categorías')

        # 2. Usuarios
        for data in USUARIOS:
            user, created = Usuario.objects.get_or_create(username=data['username'])
            if created:
                user.set_password(data['password'])
                user.is_staff = data['rol'] in ('Colaborador', 'Administrador')
                user.is_superuser = data['rol'] == 'Administrador'
                user.save()
                grupo, _ = Group.objects.get_or_create(name=data['rol'])
                user.groups.add(grupo)
                user.tipo_usuario = data['rol']
                user.save(update_fields=['tipo_usuario'])
        self.stdout.write(f'  ✅ {len(USUARIOS)} usuarios')

        # 3. Artículos con imágenes REALES de comida
        colaboradores = Usuario.objects.filter(
            groups__name='Colaborador'
        ) | Usuario.objects.filter(groups__name='Administrador')
        categorias = list(Categoria.objects.all())

        if not colaboradores.exists():
            self.stdout.write(self.style.WARNING('  ⚠️ No hay colaboradores, se saltean artículos'))
        else:
            for i, titulo in enumerate(TITULOS):
                autor = random.choice(list(colaboradores))
                cat = random.choice(categorias)
                breve = random.choice(CONTENIDOS_BREVES)
                completo = random.choice(CONTENIDOS_COMPLETOS)

                articulo = Articulo(
                    titulo=titulo,
                    contenido_breve=breve,
                    contenido_completo=completo,
                    categoria_articulo=cat,
                    usuario_articulo=autor,
                )

                img = _imagen_articulo(i)
                if img:
                    articulo.imagen.save(img.name, img, save=False)
                else:
                    from django.core.files.uploadedfile import SimpleUploadedFile
                    articulo.imagen.save(
                        f'articulo_{i}.jpg',
                        SimpleUploadedFile(
                            f'articulo_{i}.jpg',
                            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
                            b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00'
                            b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
                            content_type='image/gif',
                        ),
                        save=False,
                    )

                articulo.save()
            self.stdout.write(f'  ✅ {len(TITULOS)} artículos con imágenes reales de comida')

        # 4. Comentarios
        articulos = list(Articulo.objects.all())
        miembros = Usuario.objects.filter(groups__name='Miembro')

        if articulos and miembros.exists():
            for _ in range(30):
                art = random.choice(articulos)
                autor = random.choice(list(miembros))
                texto = random.choice(COMENTARIOS)
                art.comentarios.create(
                    usuario_comentario=autor,
                    comentario=texto,
                )
        self.stdout.write(f'  ✅ 30 comentarios')

        # 5. Mensajes de contacto
        for msg in MENSAJES_CONTACTO:
            Contacto.objects.create(
                nombre=random.choice(['Gerardo', 'Ana', 'Juan', 'María', 'Pedro']),
                email=random.choice([
                    'correo@test.com', 'chef@example.com',
                    'cocinero@mail.com', 'info@recetas.com',
                ]),
                telefono=random.choice(['011-4567-8901', '351-1234567', '379-4234567']),
                mensaje=msg,
            )
        self.stdout.write(f'  ✅ {len(MENSAJES_CONTACTO)} mensajes de contacto')

        self.stdout.write(self.style.SUCCESS('🎉 BD poblada exitosamente!'))
        self.stdout.write('')
        self.stdout.write('🔑 Usuarios para probar:')
        for u in USUARIOS:
            self.stdout.write(f'   - {u["username"]} / {u["password"]}  ({u["rol"]})')
