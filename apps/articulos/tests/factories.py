"""Factories para los modelos de la app articulos: Categoria, Articulo, Comentario."""

import factory
from apps.articulos.models import Categoria, Articulo, Comentario
from apps.usuarios.tests.factories import UsuarioFactory


class CategoriaFactory(factory.django.DjangoModelFactory):
    """Factory para Categoria. Genera descripcion secuencial unica."""

    class Meta:
        model = Categoria

    descripcion = factory.Sequence(lambda n: f'Categoria {n}')


class ArticuloFactory(factory.django.DjangoModelFactory):
    """Factory para Articulo.

    Usa SubFactory para categoria_articulo y usuario_articulo.
    Incluye una imagen dummy valida.
    """

    class Meta:
        model = Articulo

    titulo = factory.Sequence(lambda n: f'Articulo {n}')
    contenido_breve = factory.Faker('paragraph', nb_sentences=2)
    contenido_completo = factory.Faker('paragraph', nb_sentences=6)
    categoria_articulo = factory.SubFactory(CategoriaFactory)
    usuario_articulo = factory.SubFactory(UsuarioFactory)
    imagen = factory.django.ImageField(filename='test.jpg', color='green')


class ComentarioFactory(factory.django.DjangoModelFactory):
    """Factory para Comentario.

    Usa SubFactory para articulo_comentario y usuario_comentario.
    """

    class Meta:
        model = Comentario

    articulo_comentario = factory.SubFactory(ArticuloFactory)
    usuario_comentario = factory.SubFactory(UsuarioFactory)
    comentario = factory.Faker('sentence')
