"""Modelos de la app de articulos: Categoria, Articulo, Comentario."""

from django.db import models
from apps.usuarios.models import Usuario


class Categoria(models.Model):
    """Categoria a la que pertenece un articulo.

    Attributes:
        descripcion (CharField): Nombre de la categoria (unico).
    """
    descripcion = models.CharField(max_length=200)

    def __str__(self):
        """Representacion en string: la descripcion de la categoria."""
        return self.descripcion


class Articulo(models.Model):
    """Articulo principal del blog.

    Cada articulo pertenece a una Categoria y un Usuario autor.
    La categoria puede ser nula (on_delete=SET_NULL).

    Attributes:
        titulo (CharField): Titulo del articulo.
        contenido_breve (TextField): Resumen para el listado.
        contenido_completo (TextField): Contenido completo del articulo.
        fecha_publicacion (DateTimeField): Fecha de creacion automatica.
        imagen (ImageField): Imagen principal del articulo.
        categoria_articulo (ForeignKey): Categoria asociada (nullable).
        usuario_articulo (ForeignKey): Autor del articulo (CASCADE).
    """
    titulo = models.CharField(max_length=250)
    contenido_breve = models.TextField()
    contenido_completo = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='articulos')
    categoria_articulo = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True,
    )
    usuario_articulo = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        """Representacion en string: el titulo del articulo."""
        return self.titulo


class Comentario(models.Model):
    """Comentario de un usuario en un articulo.

    Se elimina en cascada si se borra el Articulo o el Usuario asociado.

    Attributes:
        articulo_comentario (ForeignKey): Articulo al que pertenece (CASCADE).
        usuario_comentario (ForeignKey): Autor del comentario (CASCADE).
        comentario (TextField): Contenido del comentario.
        fecha_publicacion (DateTimeField): Fecha de creacion automatica.
    """
    articulo_comentario = models.ForeignKey(
        Articulo, on_delete=models.CASCADE, related_name='comentarios',
    )
    usuario_comentario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    comentario = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Representacion en string: el contenido del comentario."""
        return self.comentario
