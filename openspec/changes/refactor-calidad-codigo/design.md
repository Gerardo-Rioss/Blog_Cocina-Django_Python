# Architecture Design: Refactor Integral de Calidad de Código y Seguridad

**Change ID:** `refactor-calidad-codigo`
**Date:** 2026-07-12
**Based on:** proposal.md (2026-07-12), spec.md (2026-07-12)
**Codebase analyzed:** commit actual, todos los archivos fuente

---

## Executive Summary

Este documento define las 5 decisiones de arquitectura requeridas para el refactor del Blog de Cocina. Cada decisión está fundamentada en el análisis del código real — no en suposiciones. El código actual tiene fallas estructurales concretas (señales con recursión infinita, `blog_cocina/settings/__init__.py` ausente, `BASE_DIR` que no apunta a la raíz real, autorización basada en strings con lógica invertida) que este diseño corrige de raíz.

---

## Decisión 1: Sistema de Autorización

### 1.1 Diagnóstico del código actual

```python
# apps/usuarios/models.py — ESTADO ACTUAL (bugs conocidos)
class Usuario(AbstractUser):
    TIPO_DE_USUARIO=[
        (USUARIO_COLABORADOR, 'Colaborador'),
        (USUARIO_VISITANTE,'Visitante'),       # NUNCA asignado — código muerto
        (USUARIO_MIEMBRO,'Miembro'),
        (USUARIO_SUPER,'Superusuario'),
    ]
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_DE_USUARIO, default=USUARIO_MIEMBRO)

# Señal 1: asigna Superusuario → CORRECTO en intención, pero llama instance.save() → recursión
@receiver(post_save, sender=Usuario)
def asignar_tipo_usuario(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        instance.tipo_usuario = Usuario.USUARIO_SUPER
        instance.save()  # ← RECURSIÓN INFINITA

# Señal 2: SOBRESCRIBE la primera. Si es superuser → asigna Miembro (LÓGICA INVERTIDA)
@receiver(post_save, sender=Usuario)
def asignar_miembro(sender, instance, created, **kwargs):
    if created and instance.is_superuser:          # ← mismo trigger que señal 1
        instance.tipo_usuario= Usuario.USUARIO_MIEMBRO  # ← pisa el valor correcto
        instance.save()  # ← RECURSIÓN INFINITA
```

**Problemas concretos encontrados en vistas:**

| Archivo | Línea | Código actual | Problema |
|---------|-------|---------------|----------|
| `articulos/views.py` | 78 | `if request.user.tipo_usuario == 'Miembro':` | Niega acceso a Miembro pero **no verifica ownership**. Un Colaborador puede editar artículos ajenos. |
| `articulos/views.py` | 149 | `if request.user.tipo_usuario == 'publico':` | Valor `'publico'` **no existe** en choices. Código muerto. |
| `articulos/views.py` | 97 | `delete_articulo` sin verificación | **Cualquier usuario logueado borra cualquier artículo.** |
| `contacto/views.py` | 27 | `listarMensajes` sin `@login_required` | **Anónimos pueden ver mensajes de contacto.** |
| `articulos/views.py` | 170 | Ownership en `edit_comentario` | **COMENTADO.** Nadie verifica autoría. |

### 1.2 Alternativas consideradas

| Alternativa | Descripción | Ventajas | Desventajas |
|-------------|-------------|----------|-------------|
| **A. Grupos Django + UserPassesTestMixin + helpers en modelo** | Crear grupos `Colaborador`/`Administrador`, mantener `tipo_usuario` como campo de datos, asignar grupos vía señal | Estándar Django, integración con admin, permisos granulares futuros, `tipo_usuario` no se pierde | Requiere data migration, dos fuentes de verdad (sincronizadas) |
| B. Solo UserPassesTestMixin con métodos en modelo | Eliminar `tipo_usuario`, solo helpers `es_colaborador()` | Más simple, una sola fuente de verdad | Pierde datos existentes, no escala a permisos granulares, admin no muestra roles |
| C. Django permissions nativos por modelo | `Permission` objects: `puede_editar_articulo`, etc. | Máxima granularidad | Overkill para 3 roles, complejidad innecesaria en esta etapa |

### 1.3 Decisión: **Alternativa A** — Grupos Django + UserPassesTestMixin + signal sync

**Justificación técnica:**

1. **`tipo_usuario` se mantiene como campo de datos**, no como mecanismo de autorización. Esto preserva datos existentes y permite una transición sin pérdida.
2. **Los grupos Django son el mecanismo canónico de autorización.** El admin de Django ya los soporta. Las vistas los consultan con `request.user.groups.filter(name='...').exists()`.
3. **La señal `post_save` sincroniza en una dirección**: `tipo_usuario` → grupo. Si cambia `tipo_usuario`, el grupo se actualiza. Si cambia el grupo manualmente, `tipo_usuario` NO se actualiza automáticamente (la señal es la fuente de verdad para el campo).
4. **Helpers en el modelo** para legibilidad: `user.es_administrador()` es más expresivo que `user.groups.filter(...).exists()`.

#### API de verificación diseñada

```python
# apps/usuarios/models.py — NUEVO DISEÑO
class Usuario(AbstractUser):
    USUARIO_COLABORADOR = 'Colaborador'
    USUARIO_MIEMBRO = 'Miembro'
    USUARIO_ADMINISTRADOR = 'Administrador'
    # USUARIO_VISITANTE se ELIMINA — nunca fue asignado, no está en la DB
    
    TIPO_DE_USUARIO = [
        (USUARIO_MIEMBRO, 'Miembro'),
        (USUARIO_COLABORADOR, 'Colaborador'),
        (USUARIO_ADMINISTRADOR, 'Administrador'),
    ]
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_DE_USUARIO, default=USUARIO_MIEMBRO)

    # ─── Helpers de autorización ───
    def es_miembro(self):
        """Usuario registrado básico. Solo lectura de contenido público."""
        return self.groups.filter(name='Miembro').exists()

    def es_colaborador(self):
        """Puede crear y editar sus propios artículos."""
        return self.groups.filter(name='Colaborador').exists()

    def es_administrador(self):
        """Control total: CRUD sobre cualquier contenido + acceso a mensajes."""
        return self.groups.filter(name='Administrador').exists() or self.is_superuser

    def puede_editar_articulo(self, articulo):
        """Verifica ownership O privilegio de administrador."""
        return self.es_administrador() or articulo.usuario_articulo == self

    def puede_eliminar_articulo(self, articulo):
        """Verifica ownership O privilegio de administrador."""
        return self.es_administrador() or articulo.usuario_articulo == self

    def puede_editar_comentario(self, comentario):
        """Solo el autor o un admin pueden editar."""
        return self.es_administrador() or comentario.usuario_comentario == self
```

#### Señal corregida (sin recursión)

```python
# apps/usuarios/models.py — SEÑAL ÚNICA (reemplaza las 2 actuales)
@receiver(post_save, sender=Usuario)
def sincronizar_grupo_usuario(sender, instance, created, **kwargs):
    """
    Sincroniza el grupo Django según tipo_usuario.
    Usa update() en el QuerySet para NO disparar post_save recursivo.
    Se ejecuta en created=True Y en updates (para mantener sincronía).
    """
    if instance.is_superuser:
        grupo_nombre = 'Administrador'
        tipo = Usuario.USUARIO_ADMINISTRADOR
    elif instance.tipo_usuario == Usuario.USUARIO_ADMINISTRADOR:
        grupo_nombre = 'Administrador'
        tipo = Usuario.USUARIO_ADMINISTRADOR
    elif instance.tipo_usuario == Usuario.USUARIO_COLABORADOR:
        grupo_nombre = 'Colaborador'
        tipo = Usuario.USUARIO_COLABORADOR
    else:
        grupo_nombre = 'Miembro'
        tipo = Usuario.USUARIO_MIEMBRO

    grupo, _ = Group.objects.get_or_create(name=grupo_nombre)
    instance.groups.add(grupo)

    # Si el tipo_usuario no coincide con lo que debería ser, actualizar SIN disparar señal
    if instance.tipo_usuario != tipo:
        Usuario.objects.filter(pk=instance.pk).update(tipo_usuario=tipo)
```

**Por qué `update()` en el QuerySet:** `QuerySet.update()` no dispara `post_save`. Es la forma canónica de Django para modificar un campo desde una señal sin recursión.

#### Estrategia de migración de datos

```python
# apps/usuarios/migrations/XXXX_populate_groups.py (DATA MIGRATION)
from django.db import migrations

GROUPS = ['Miembro', 'Colaborador', 'Administrador']

def crear_grupos_y_asignar(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Usuario = apps.get_model('usuarios', 'Usuario')
    
    # 1. Crear grupos si no existen
    for nombre in GROUPS:
        Group.objects.get_or_create(name=nombre)
    
    # 2. Mapear usuarios existentes
    grupo_map = {
        'Miembro': 'Miembro',
        'Colaborador': 'Colaborador', 
        'Superusuario': 'Administrador',
        'SuperUsuario': 'Administrador',
    }
    
    for user in Usuario.objects.all():
        grupo_nombre = grupo_map.get(user.tipo_usuario, 'Miembro')
        grupo = Group.objects.get(name=grupo_nombre)
        user.groups.add(grupo)

def revertir(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GROUPS).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0004_alter_usuario_tipo_usuario'),
    ]
    operations = [
        migrations.RunPython(crear_grupos_y_asignar, revertir),
    ]
```

#### Vistas: antes/después

```python
# ─── ANTES ───
@login_required
def editArticulo(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    if request.user.tipo_usuario =='Miembro':          # ❌ string comparison
        return HttpResponseForbidden("No tenes permiso...") # ❌ no verifica ownership
    # ... cualquier no-Miembro edita cualquier artículo

@login_required
def delete_articulo(request, pk):
    articulo = get_object_or_404(Articulo, id=pk)
    articulo.delete()  # ❌ sin verificación alguna
    return redirect('articulos:listarArticulos')

# ─── DESPUÉS ───
@login_required
def editar_articulo(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    if not request.user.puede_editar_articulo(articulo):  # ✅ helper del modelo
        messages.error(request, 'No tenés permiso para editar este artículo.')
        raise PermissionDenied()                           # ✅ HTTP 403 estándar
    # ... resto de la lógica igual

@login_required
@require_POST                                              # ✅ solo POST
def eliminar_articulo(request, pk):
    articulo = get_object_or_404(Articulo, pk=pk)
    if not request.user.puede_eliminar_articulo(articulo): # ✅ verificación real
        raise PermissionDenied()
    articulo.delete()
    messages.success(request, 'Artículo eliminado.')
    return redirect('articulos:listar_articulos')
```

#### Templates: antes/después

```django
<!-- ─── ANTES ─── -->
{% if user.is_authenticated and user.is_staff or user.is_superuser %}
  <!-- Menú Colaborador -->
{% endif %}

<!-- ─── DESPUÉS ─── -->
{% if user.is_authenticated and user.es_colaborador or user.es_administrador %}
  <!-- Menú Colaborador: visible para ambos roles con permisos de escritura -->
{% endif %}
```

Para que `user.es_colaborador` funcione en templates, se registra un context processor o se usa `user.groups.filter` directamente. **Decisión:** usar `user.groups.filter` en templates (es nativo de Django, no requiere context processor) y helpers en Python. En templates:

```django
{% if user.groups.all.0.name == 'Administrador' %}
```

Pero esto es frágil si un usuario está en múltiples grupos. Mejor approach: un **template tag simple** o usar el helper accesible desde el objeto user:

```django
{% if user.es_administrador %}  {# El helper está en el modelo, accesible en template #}
```

Como `Usuario` hereda de `AbstractUser`, los métodos definidos en el modelo son directamente accesibles en el template. Esto funciona sin configuración adicional.

### 1.4 Trade-offs aceptados

| Trade-off | Impacto | Mitigación |
|-----------|---------|------------|
| `tipo_usuario` + grupos = dos fuentes de verdad | Riesgo de desincronización | La señal `post_save` sincroniza en cada save. El comando `setup_groups` reconcilia. |
| `update()` del QuerySet no dispara señales | Si alguien usa `Usuario.objects.update(tipo_usuario=...)`, el grupo no se actualiza | Documentado como limitación conocida. El comando `sync_groups` corrige. |
| Los helpers viven en el modelo, no en mixins separados | Acoplamiento modelo-autorización | Para este proyecto con 3 roles, la simplicidad gana. Si crece, se extraen a un módulo `authorization.py`. |

---

## Decisión 2: Estructura de Submódulos en `apps/articulos/`

### 2.1 Diagnóstico del código actual

`apps/articulos/views.py` tiene **184 líneas**, 16 funciones de vista, mezclando 3 dominios:

| Dominio | Funciones | Líneas |
|---------|-----------|--------|
| Artículos | `listarArticulos`, `detalleArticulos`, `editArticulo`, `delete_articulo`, `AddArticulo` | ~100 |
| Categorías | `listarCategorias`, `addCategoria`, `edit_categoria`, `delete_categoria` | ~52 |
| Comentarios | `add_comentario`, `edit_comentario`, `delete_comentario` | ~32 |

Además, los nombres mezclan snake_case y camelCase en el mismo archivo.

### 2.2 Alternativas consideradas

| Alternativa | Estructura | Ventajas | Desventajas |
|-------------|-----------|----------|-------------|
| **A. Paquete `views/` con 3 submódulos + `__init__.py` re-exportador** | `views/{__init__,articulos,categorias,comentarios}.py` | Separación clara por dominio, imports backward-compatibles, cada archivo <80 líneas | Un nivel más de directorio |
| B. Tres archivos sueltos: `views_articulos.py`, `views_categorias.py`, `views_comentarios.py` | Flat, sin subdirectorio | Sin cambios en imports | Contamina el namespace, no es idiomático en Django |
| C. Class-based views con herencia por dominio | Mixins + CBVs | Reutilización de lógica | Refactor masivo, las vistas actuales son FBVs, rompe todos los templates y URLs |

### 2.3 Decisión: **Alternativa A** — Paquete `views/` con submódulos

**Justificación técnica:**

1. **Separación por subdominio** sin romper imports existentes gracias a `__init__.py` re-exportador.
2. **Convención Django establecida**: `views/` como paquete es idiomático en proyectos Django medianos/grandes.
3. **No se migra a CBVs**: las vistas son function-based y el refactor mantiene FBVs. Esto minimiza el diff y el riesgo de regresión.

#### Estructura diseñada

```
apps/articulos/
├── __init__.py
├── admin.py
├── apps.py
├── forms.py                # se mantiene unificado (es pequeño: 21 líneas)
├── models.py
├── urls.py                 # se mantiene flat, imports desde views.*
├── views/
│   ├── __init__.py          # re-exporta TODAS las vistas
│   ├── articulos.py         # listar_articulos, detalle_articulos, crear_articulo,
│   │                        #   editar_articulo, eliminar_articulo
│   ├── categorias.py        # listar_categorias, crear_categoria,
│   │                        #   editar_categoria, eliminar_categoria
│   └── comentarios.py       # agregar_comentario, editar_comentario, eliminar_comentario
├── migrations/
├── templates/
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── factories.py
    ├── test_models.py
    ├── test_views/
    │   ├── __init__.py
    │   ├── test_articulos.py
    │   ├── test_categorias.py
    │   └── test_comentarios.py
    ├── test_forms.py
    └── test_integration.py
```

#### `__init__.py` re-exportador (backward compatibility)

```python
# apps/articulos/views/__init__.py
"""
Paquete de vistas de la app artículos.
Re-exporta todas las vistas para mantener compatibilidad con imports existentes
(tanto internos — desde urls.py — como externos).
"""

from .articulos import (
    listar_articulos,
    detalle_articulos,
    crear_articulo,
    editar_articulo,
    eliminar_articulo,
)
from .categorias import (
    listar_categorias,
    crear_categoria,
    editar_categoria,
    eliminar_categoria,
)
from .comentarios import (
    agregar_comentario,
    editar_comentario,
    eliminar_comentario,
)

__all__ = [
    # Artículos
    'listar_articulos', 'detalle_articulos', 'crear_articulo',
    'editar_articulo', 'eliminar_articulo',
    # Categorías
    'listar_categorias', 'crear_categoria',
    'editar_categoria', 'eliminar_categoria',
    # Comentarios
    'agregar_comentario', 'editar_comentario', 'eliminar_comentario',
]
```

#### `urls.py` usa `include()` con namespaces (opcional, pero recomendado)

El `urls.py` actual es plano y mezcla patrones. **Se mantiene un solo archivo** pero se organiza con comentarios de sección. No se usa `include()` con submódulos de URL porque el overhead no se justifica para 12 patrones:

```python
# apps/articulos/urls.py — DISEÑO FINAL
from django.urls import path
from . import views  # sigue funcionando gracias a __init__.py

app_name = 'articulos'

urlpatterns = [
    # ─── Artículos ───
    path('', views.listar_articulos, name='listar_articulos'),
    path('crear/', views.crear_articulo, name='crear_articulo'),
    path('<int:pk>/', views.detalle_articulos, name='detalle_articulos'),
    path('<int:pk>/editar/', views.editar_articulo, name='editar_articulo'),
    path('<int:pk>/eliminar/', views.eliminar_articulo, name='eliminar_articulo'),

    # ─── Categorías ───
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),

    # ─── Comentarios ───
    path('comentario/<int:articulo_id>/crear/', views.agregar_comentario, name='agregar_comentario'),
    path('comentario/<int:comentario_id>/editar/', views.editar_comentario, name='editar_comentario'),
    path('comentario/<int:comentario_id>/eliminar/', views.eliminar_comentario, name='eliminar_comentario'),
]
```

**Nota importante sobre cambio de URLs:** Los nombres de URL y patrones cambian (ej. `addArticulo/` → `crear/`). Para no romper bookmarks existentes (si los hay), se agregan **redirects 301 en la URLconf raíz** (`blog_cocina/urls.py`) de los patrones viejos a los nuevos:

```python
# blog_cocina/urls.py — redirects de compatibilidad (transitorios)
from django.views.generic import RedirectView

urlpatterns = [
    # ... patrones normales ...
    
    # Redirects temporarios de URLs viejas a nuevas (eliminar después de 3 meses)
    path('articulos/addArticulo/', RedirectView.as_view(
        pattern_name='articulos:crear_articulo', permanent=True)),
    path('articulos/detalleArticulos/<int:pk>', RedirectView.as_view(
        pattern_name='articulos:detalle_articulos', permanent=True)),
    path('articulos/articulos/<int:pk>/edit/', RedirectView.as_view(
        pattern_name='articulos:editar_articulo', permanent=True)),
    path('articulos/articulo/delete/<int:pk>/', RedirectView.as_view(
        pattern_name='articulos:eliminar_articulo', permanent=True)),
    # ... etc para cada URL renombrada
]
```

### 2.4 Trade-offs aceptados

| Trade-off | Impacto | Mitigación |
|-----------|---------|------------|
| Los redirects 301 quedan "para siempre" si nadie los limpia | URLs legacy en el código | Comentario `TODO:` con fecha de expiración a 3 meses |
| `urls.py` único pero vistas separadas: no hay `include()` por dominio | Menos modularidad de URLs | Para 12 patrones, `include()` no aporta; reevaluar si el proyecto crece a 30+ |
| Tests también se separan por dominio | Más archivos | Cada archivo de test es corto (<100 líneas) y enfocado |

---

## Decisión 3: Aislamiento de Settings

### 3.1 Diagnóstico del código actual

```python
# blog_cocina/settings/base.py — ESTADO ACTUAL
SECRET_KEY = 'django-insecure-gevj8ktd8*9mm$(^x4y&*ojl$mi)^2of(zdt)r5(*$ub9)vy8q'  # ❌ hardcodeada
BASE_DIR = Path(__file__).resolve().parent.parent
# blog_cocina/settings/base.py → parent = blog_cocina/ → parent.parent = raíz
# Pero el TEMPLATES DIR usa os.path.dirname(BASE_DIR) → un nivel MÁS arriba
# Esto crea inconsistencia: BASE_DIR ≠ raíz real para templates

LANGUAGE_CODE = 'en-ar'  # ❌ inválido; debería ser 'es-AR'
# Sin STATIC_ROOT, sin SECURE_* settings

# blog_cocina/settings/local.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'blog_cocina',      # ❌ hardcodeado
        'USER': 'root',             # ❌ hardcodeado
        'PASSWORD': 'root',         # ❌ hardcodeado + expuesto
        'HOST': 'localhost',
        'PORT': ''
    }
}

# blog_cocina/settings/production.py — VACÍO
# blog_cocina/settings/__init__.py — NO EXISTE ← CRÍTICO
```

**Hallazgo crítico adicional:** `blog_cocina/settings/__init__.py` **no existe**. Esto significa que `from .base import *` en `local.py` funciona por ejecución directa, pero `blog_cocina.settings` como paquete Python no es correctamente importable. `wsgi.py` y `asgi.py` referencian `'blog_cocina.settings'` — sin `__init__.py`, esto es frágil.

### 3.2 Alternativas consideradas

| Alternativa | Biblioteca | Ventajas | Desventajas |
|-------------|-----------|----------|-------------|
| **A. `python-decouple`** | `decouple` | Casting tipado (`Csv()`, `bool`), `UndefinedValueError` claro, `.env` nativo, battle-tested | Dependencia externa |
| B. `python-dotenv` + `os.environ.get()` | `dotenv` | Popular, carga `.env` temprano | Sin casting tipado, sin mensajes de error descriptivos |
| C. Solo `os.environ.get()` | Ninguna | Sin dependencias | Sin soporte `.env`; cada dev debe exportar vars manualmente |

### 3.3 Decisión: **Alternativa A** — `python-decouple`

**Justificación técnica:**

1. `decouple` maneja **casting de tipos** nativamente: `config('DEBUG', default=False, cast=bool)`, `config('ALLOWED_HOSTS', cast=Csv())`.
2. El `UndefinedValueError` incluye el nombre de la variable faltante — crítico para debugging.
3. **`.env` se busca automáticamente** en el directorio de trabajo (raíz del proyecto, donde está `manage.py`).
4. El spec ya asume `python-decouple`. Mantiene coherencia.

#### Flujo de carga diseñado

```
┌─────────────────────────────────────────────────────────┐
│  1. .env (raíz del proyecto)                             │
│     └─ python-decouple lo carga automáticamente          │
│                                                          │
│  2. base.py                                              │
│     └─ config('VAR', default=...) para CADA setting      │
│        sensible. Defaults SEGUROS para desarrollo.       │
│                                                          │
│  3. local.py                                             │
│     └─ from .base import *                               │
│     └─ Sobrescribe DEBUG=True (explícito)                │
│     └─ Sobrescribe DATABASES (usando config())           │
│                                                          │
│  4. production.py                                        │
│     └─ from .base import *                               │
│     └─ DEBUG = False (forzado, NO desde env)             │
│     └─ Sobrescribe ALLOWED_HOSTS desde env               │
│     └─ Agrega SECURE_* settings                         │
│     └─ Configura LOGGING, EMAIL, ADMINS                  │
└─────────────────────────────────────────────────────────┘
```

**Principio:** `base.py` define defaults seguros para desarrollo con `config()`. `local.py` y `production.py` sobreescriben lo necesario. `local.py` es para desarrollo, `production.py` es para deploy.

#### Estructura de `.env` / `.env.example`

```bash
# .env — NO VERSIONAR (está en .gitignore)
SECRET_KEY='django-insecure-clave-real-de-desarrollo'
DB_NAME='blog_cocina'
DB_USER='root'
DB_PASSWORD='root'
DB_HOST='localhost'
DB_PORT='3306'
```

```bash
# .env.example — SÍ VERSIONAR (template para otros devs)
# Copiar a .env y reemplazar con valores reales
SECRET_KEY='changeme-50-chars-minimum'
DB_NAME='blog_cocina'
DB_USER='root'
DB_PASSWORD='changeme'
DB_HOST='localhost'
DB_PORT='3306'
# Solo producción (no necesario en desarrollo):
# ALLOWED_HOSTS='midominio.com,www.midominio.com'
# EMAIL_HOST='smtp.mailgun.com'
# EMAIL_HOST_USER='postmaster@midominio.com'
# EMAIL_HOST_PASSWORD='changeme'
```

#### `base.py` — Diseño final

```python
# blog_cocina/settings/base.py — NUEVO DISEÑO
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # ← CORREGIDO: 3 niveles

SECRET_KEY = config('SECRET_KEY')  # ← REQUERIDO: lanza UndefinedValueError si falta

AUTH_USER_MODEL = 'usuarios.Usuario'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.usuarios',
    'apps.articulos',
    'apps.contacto',
]

# ... MIDDLEWARE, TEMPLATES, AUTH_PASSWORD_VALIDATORS sin cambios ...

LANGUAGE_CODE = 'es-AR'  # ← CORREGIDO
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']    # ← usa Path, más legible
STATIC_ROOT = BASE_DIR / 'staticfiles'      # ← NUEVO: para collectstatic

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'             # ← usa Path, más legible

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Database (defaults de desarrollo) ───
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='blog_cocina'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
    }
}

# ─── Email (console en desarrollo) ───
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Corrección de `BASE_DIR`**: Actualmente `Path(__file__).resolve().parent.parent` desde `blog_cocina/settings/base.py` da `blog_cocina/`, pero `TEMPLATES[0]['DIRS']` usa `os.path.dirname(BASE_DIR)` para compensar. **Con el nuevo diseño**: `parent.parent.parent` = raíz del proyecto. Todos los paths usan `BASE_DIR / 'subdir'` consistentemente.

#### `local.py` — Diseño final

```python
# blog_cocina/settings/local.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = []

# local.py hereda DATABASES de base.py (ya usa config() con defaults)
```

#### `production.py` — Diseño final

```python
# blog_cocina/settings/production.py
from .base import *
from decouple import config, Csv

DEBUG = False  # ← FORZADO, nunca desde variable de entorno

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# ─── Base de datos productiva ───
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# ─── Seguridad ───
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ─── Email productivo ───
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = True

# ─── Logging ───
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# ─── Admins ───
ADMINS = [('Admin', config('ADMIN_EMAIL', default='admin@example.com'))]
```

#### `__init__.py` — Crear el archivo faltante

```python
# blog_cocina/settings/__init__.py — NUEVO (actualmente NO existe)
# Paquete de settings. El módulo concreto se selecciona vía
# la variable de entorno DJANGO_SETTINGS_MODULE.
```

### 3.4 Trade-offs aceptados

| Trade-off | Impacto | Mitigación |
|-----------|---------|------------|
| `BASE_DIR` cambia de `parent.parent` (2 niveles) a `parent.parent.parent` (3 niveles) | Todos los paths relativos deben recalcularse | Se revisa cada `BASE_DIR / ...` y `os.path.dirname(BASE_DIR)` en el código |
| `DATABASES` se mueve de `local.py` a `base.py` | `base.py` ahora define DB defaults, `local.py` solo sobreescribe DEBUG | Si un dev no tiene `.env`, los defaults de `config()` proveen valores de desarrollo |
| `production.py` requiere `ADMIN_EMAIL`, `ALLOWED_HOSTS`, credenciales SMTP | Más variables de entorno para deploy | `.env.example` documenta todas. `check --deploy` alerta sobre faltantes |

---

## Decisión 4: Test Fixtures y Estrategia

### 4.1 Diagnóstico

- **0 tests** en todo el proyecto.
- `pytest` no está instalado.
- No existe directorio `tests/` en ninguna app.
- El proyecto tiene señales, forms con bugs conocidos, y autorización frágil — terreno fértil para regresiones.

### 4.2 Alternativas consideradas

| Alternativa | Descripción | Ventajas | Desventajas |
|-------------|-------------|----------|-------------|
| **A. pytest-django + factory_boy** | pytest como runner, factory_boy para fixtures | Fixtures declarativas, traits para variantes (roles), integración pytest nativa, `--cov` built-in | Dependencia extra (factory_boy) |
| B. pytest-django + fixtures manuales (setUp/tearDown) | pytest con funciones `@pytest.fixture` | Sin dependencias extra | Más código boilerplate, fixtures menos reutilizables |
| C. unittest built-in de Django | `django.test.TestCase` | Sin dependencias extra, conocido del curso "El Informatorio" | Menos expresivo, `--cov` requiere `coverage.py` aparte, comunidad migró a pytest |

### 4.3 Decisión: **Alternativa A** — `pytest-django` + `factory_boy`

**Justificación técnica:**

1. `factory_boy` permite definir **factories declarativas con traits** — ideal para este proyecto porque necesitamos crear usuarios con diferentes roles (Miembro, Colaborador, Administrador) de forma concisa.
2. `pytest-django` integra `--cov` directamente. `pytest --cov=apps --cov-report=term-missing` da cobertura sin configuración extra.
3. La combinación es el estándar de facto en la comunidad Django actual.

#### Estructura de directorios de tests

```
apps/
├── usuarios/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py          # fixtures compartidos: usuario_miembro, usuario_colaborador, etc.
│       ├── factories.py         # UsuarioFactory, con traits por rol
│       ├── test_models.py       # Creación, __str__, constraints
│       ├── test_signals.py      # post_save → asignación de grupo y tipo_usuario
│       ├── test_forms.py        # RegistroForm validación
│       └── test_views.py        # Login, logout, registro
│
├── articulos/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py          # fixtures: articulo, categoria, comentario
│       ├── factories.py         # ArticuloFactory, CategoriaFactory, ComentarioFactory
│       ├── test_models.py
│       ├── test_views/
│       │   ├── __init__.py
│       │   ├── test_articulos.py    # CRUD + autorización
│       │   ├── test_categorias.py   # CRUD + autorización
│       │   └── test_comentarios.py  # CRUD + autorización + validación
│       ├── test_forms.py
│       └── test_integration.py  # Flujos end-to-end por rol
│
├── contacto/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── factories.py         # ContactoFactory
│       ├── test_models.py
│       ├── test_forms.py
│       └── test_views.py        # msj_contacto, listarMensajes (protección)
│
└── (raíz)/
    └── pytest.ini               # Configuración global de pytest
```

#### `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = blog_cocina.settings.local
python_files = tests.py test_*.py *_tests.py
addopts =
    --strict-markers
    -v
    --tb=short
    --cov=apps
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=70
markers =
    slow: Tests que tocan DB o hacen requests (deselected por defecto en --fast)
```

#### Factories con traits para roles

```python
# apps/usuarios/tests/factories.py
import factory
from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario

class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario

    username = factory.Sequence(lambda n: f'usuario{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@test.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

    # ─── Traits por rol ───
    class Meta:
        model = Usuario
        exclude = ('_grupo',)

    _grupo = None  # overridden en traits

    @factory.post_generation
    def grupos(self, create, extracted, **kwargs):
        if not create or self._grupo is None:
            return
        grupo, _ = Group.objects.get_or_create(name=self._grupo)
        self.groups.add(grupo)
        # Sincronizar tipo_usuario
        mapa = {'Miembro': 'Miembro', 'Colaborador': 'Colaborador', 'Administrador': 'Administrador'}
        self.tipo_usuario = mapa.get(self._grupo, 'Miembro')
        Usuario.objects.filter(pk=self.pk).update(tipo_usuario=self.tipo_usuario)

    class Params:
        miembro = factory.Trait(_grupo='Miembro')
        colaborador = factory.Trait(_grupo='Colaborador', is_staff=True)
        administrador = factory.Trait(_grupo='Administrador', is_staff=True, is_superuser=True)


# apps/articulos/tests/factories.py
import factory
from apps.articulos.models import Articulo, Categoria, Comentario
from apps.usuarios.tests.factories import UsuarioFactory

class CategoriaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Categoria
    descripcion = factory.Sequence(lambda n: f'Categoría {n}')


class ArticuloFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Articulo
    titulo = factory.Sequence(lambda n: f'Artículo {n}')
    contenido_breve = factory.Faker('paragraph', nb_sentences=2)
    contenido_completo = factory.Faker('paragraph', nb_sentences=6)
    categoria_articulo = factory.SubFactory(CategoriaFactory)
    usuario_articulo = factory.SubFactory(UsuarioFactory)


class ComentarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comentario
    articulo_comentario = factory.SubFactory(ArticuloFactory)
    usuario_comentario = factory.SubFactory(UsuarioFactory)
    comentario = factory.Faker('sentence')
```

#### Estrategia para tests de autorización

```python
# apps/articulos/tests/conftest.py
import pytest
from apps.usuarios.tests.factories import UsuarioFactory
from apps.articulos.tests.factories import ArticuloFactory, CategoriaFactory

@pytest.fixture
def usuario_miembro(client, django_user_model):
    """Usuario con rol Miembro (solo lectura)."""
    user = UsuarioFactory(miembro=True)
    client.force_login(user)
    return user

@pytest.fixture
def usuario_colaborador(client):
    """Usuario con rol Colaborador (crea/edita artículos propios)."""
    user = UsuarioFactory(colaborador=True)
    client.force_login(user)
    return user

@pytest.fixture
def usuario_administrador(client):
    """Usuario con rol Administrador (control total)."""
    user = UsuarioFactory(administrador=True)
    client.force_login(user)
    return user

@pytest.fixture
def cliente_anonimo(client):
    """Cliente sin autenticación."""
    return client  # sin force_login

@pytest.fixture
def articulo():
    return ArticuloFactory()

@pytest.fixture
def categoria():
    return CategoriaFactory()
```

```python
# Ejemplo de test de autorización (apps/articulos/tests/test_views/test_articulos.py)
import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestEliminarArticulo:
    def test_anonimo_redirigido_a_login(self, cliente_anonimo, articulo):
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = cliente_anonimo.post(url)
        assert response.status_code == 302
        assert '/usuarios/login/' in response.url

    def test_miembro_recibe_403(self, usuario_miembro, articulo, client):
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = client.post(url)
        assert response.status_code == 403

    def test_colaborador_puede_eliminar_articulo_propio(self, usuario_colaborador, client):
        from apps.articulos.tests.factories import ArticuloFactory
        art = ArticuloFactory(usuario_articulo=usuario_colaborador)
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': art.pk})
        response = client.post(url)
        assert response.status_code == 302  # redirect exitoso

    def test_colaborador_no_puede_eliminar_articulo_ajeno(self, usuario_colaborador, articulo, client):
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = client.post(url)
        assert response.status_code == 403

    def test_administrador_puede_eliminar_cualquier_articulo(self, usuario_administrador, articulo, client):
        url = reverse('articulos:eliminar_articulo', kwargs={'pk': articulo.pk})
        response = client.post(url)
        assert response.status_code == 302
```

#### Cobertura mínima por módulo

| Módulo | Target | Archivos |
|--------|--------|----------|
| `apps/usuarios/models.py` | ≥85% | `test_models.py`, `test_signals.py` |
| `apps/usuarios/views.py` | ≥70% | `test_views.py` |
| `apps/articulos/models.py` | ≥85% | `test_models.py` |
| `apps/articulos/views/` | ≥70% | `test_views/test_*.py` |
| `apps/articulos/forms.py` | ≥80% | `test_forms.py` |
| `apps/contacto/models.py` | ≥80% | `test_models.py` |
| `apps/contacto/views.py` | ≥70% | `test_views.py` |
| `apps/contacto/forms.py` | ≥80% | `test_forms.py` |

### 4.4 Trade-offs aceptados

| Trade-off | Impacto | Mitigación |
|-----------|---------|------------|
| `factory_boy` es una dependencia extra | Mayor superficie de dependencias | Vale la pena: reduce 3-5x el boilerplate de fixtures. Sin factory_boy, cada test que crea usuarios necesitaría 10+ líneas de setup. |
| `force_login()` no prueba el flujo real de autenticación | Los tests de vistas no validan login/password | El flujo de login se prueba en `test_views.py` de usuarios. Los tests de autorización asumen sesión ya iniciada para aislar el permiso. |
| `--cov-fail-under=70` es agresivo al principio | CI "fallaría" hasta alcanzar cobertura | Se agrega al final de Ola 4, no antes. Durante Ola 4 se corre sin `--cov-fail-under`. |

---

## Decisión 5: Convenciones de Código

### 5.1 Diagnóstico del código actual

| Problema | Ejemplo real | Archivo |
|----------|-------------|---------|
| camelCase en funciones | `listarArticulos`, `editArticulo`, `AddArticulo`, `detalleArticulos` | `articulos/views.py` |
| camelCase en URLs | `'listarArticulos'`, `'addarticulo'`, `'addcategoria'` | `articulos/urls.py` |
| Mezcla de idiomas | `delete_articulo` (inglés) + `listarArticulos` (spanglish) | `articulos/views.py` |
| Bloques inconsistentes | `{% block titulo %}` en base, `{% block title %}` en otros | `templates/` |
| Sin docstrings | 0 docstrings en todo el proyecto | Todos los `.py` |
| `lang="en"` con contenido español | `<html lang="en">` en plantilla que dice "Artículos", "Cerrar Sesión" | `templates/base.html` |

### 5.2 Decisión: estándar unificado

#### Nombres: snake_case, nombres en español para dominio de negocio

**Regla:** Todas las funciones de vista, nombres de URL y funciones auxiliares usan `snake_case`. Los nombres reflejan la acción en **español** (coherente con el dominio de cocina y la interfaz en español).

| Actual (camelCase / mixto) | Nuevo (snake_case) |
|---------------------------|---------------------|
| `listarArticulos` | `listar_articulos` |
| `detalleArticulos` | `detalle_articulos` |
| `AddArticulo` | `crear_articulo` |
| `editArticulo` | `editar_articulo` |
| `delete_articulo` | `eliminar_articulo` ← consistente: español |
| `listarCategorias` | `listar_categorias` |
| `addCategoria` | `crear_categoria` |
| `edit_categoria` | `editar_categoria` |
| `delete_categoria` | `eliminar_categoria` |
| `add_comentario` | `agregar_comentario` |
| `edit_comentario` | `editar_comentario` |
| `delete_comentario` | `eliminar_comentario` |

**URL names (también snake_case):**

| Actual | Nuevo |
|--------|-------|
| `'listarArticulos'` | `'listar_articulos'` |
| `'addarticulo'` | `'crear_articulo'` |
| `'detalleArticulos'` | `'detalle_articulos'` |
| `'editArticulo'` | `'editar_articulo'` |
| `'delete_articulo'` | `'eliminar_articulo'` |
| `'listarCategorias'` | `'listar_categorias'` |
| `'addcategoria'` | `'crear_categoria'` |
| `'add_comentario'` | `'agregar_comentario'` |

**Regla para prefijos de acción:** `listar_`, `crear_`, `editar_`, `eliminar_`, `detalle_`, `agregar_`.

#### Docstrings: Google Style, en español

**Decisión:** Docstrings en **español** (dominio del proyecto), con términos técnicos en inglés (QuerySet, ForeignKey, post_save). Formato **Google Style** porque es legible, soportado por IDE (VSCode, PyCharm) y más limpio que Sphinx para proyectos de este tamaño.

```python
def puede_editar_articulo(self, articulo):
    """Verifica si el usuario tiene permiso para editar un artículo.

    Un usuario puede editar si es administrador o si es el autor
    del artículo.

    Args:
        articulo (Articulo): Instancia del artículo a verificar.

    Returns:
        bool: True si el usuario puede editar, False en caso contrario.
    """
    return self.es_administrador() or articulo.usuario_articulo == self
```

**Cobertura requerida:** docstrings en:
- Clases de modelo (descripción y propósito)
- Métodos `__str__`, `save()`, `get_absolute_url()` en modelos
- Funciones de vista (propósito, template, contexto)
- Métodos de `ModelForm` con lógica no trivial
- Señales (qué dispara, qué efecto tiene)
- Funciones auxiliares exportadas

#### Templates: convenciones

| Aspecto | Estado actual | Estado diseñado |
|--------|---------------|-----------------|
| `lang` | `lang="en"` | `lang="es"` |
| Bloque de título | `{% block titulo %}` en base | **Unificar a `{% block titulo %}`** en todos los templates (ya hay templates que usan `title`, otros `titulo`) |
| Meta description | Ausente | `<meta name="description" content="{% block meta_desc %}Blog de cocina con recetas,...{% endblock meta_desc %}">` |
| Nombres de bloque | `contenido` | Mantener `contenido` (ya está unificado) |
| Template tags | `{% url 'articulos:listar_articulos' %}` | Los nombres reflejan snake_case de las URLs |

---

## Resumen de Archivos Afectados

### Archivos nuevos (a crear)

| Archivo | Propósito |
|---------|-----------|
| `.env` | Variables de entorno para desarrollo |
| `.env.example` | Template documentado de variables |
| `blog_cocina/settings/__init__.py` | Paquete settings (ausente → crítico) |
| `apps/articulos/views/__init__.py` | Re-exportador de vistas |
| `apps/articulos/views/articulos.py` | Vistas de artículos |
| `apps/articulos/views/categorias.py` | Vistas de categorías |
| `apps/articulos/views/comentarios.py` | Vistas de comentarios |
| `apps/usuarios/tests/` | Suite de tests de usuarios |
| `apps/articulos/tests/` | Suite de tests de artículos |
| `apps/contacto/tests/` | Suite de tests de contacto |
| `pytest.ini` | Configuración de pytest |
| `apps/usuarios/management/commands/setup_groups.py` | Comando para crear/reconciliar grupos |
| `apps/usuarios/migrations/XXXX_populate_groups.py` | Data migration para usuarios existentes |

### Archivos modificados

| Archivo | Cambios principales |
|---------|---------------------|
| `blog_cocina/settings/base.py` | `SECRET_KEY`/DB vía `config()`, `LANGUAGE_CODE`, `BASE_DIR`, `STATIC_ROOT` |
| `blog_cocina/settings/local.py` | Simplificado: solo `DEBUG=True` |
| `blog_cocina/settings/production.py` | Completo: `SECURE_*`, logging, email, DB productiva |
| `apps/usuarios/models.py` | Señal unificada sin recursión, helpers de autorización, choices simplificados |
| `apps/articulos/models.py` | Corregir `default='Sin categoría'` en FK |
| `apps/contacto/models.py` | Corregir indentación de `__str__` |
| `apps/articulos/forms.py` | Corregir `usuario_comentario = user.username` → instancia User |
| `apps/articulos/views.py` → `views/*.py` | Separar en submódulos, renombrar snake_case, autorización con helpers |
| `apps/articulos/urls.py` | Renombrar URL patterns, quitar `+ static(...)` |
| `apps/usuarios/urls.py` | Quitar `+ static(...)` |
| `apps/usuarios/views.py` | Agregar docstrings |
| `apps/contacto/views.py` | `listarMensajes` protegido, docstrings |
| `apps/contacto/urls.py` | Sin cambios funcionales, docstrings |
| `blog_cocina/urls.py` | Agregar redirects 301 + quitar `+ static(...)` de producción |
| `blog_cocina/wsgi.py` | Verificar `DJANGO_SETTINGS_MODULE` (ya apunta a paquete) |
| `blog_cocina/asgi.py` | Verificar `DJANGO_SETTINGS_MODULE` (ya apunta a paquete) |
| `blog_cocina/views.py` | Eliminar vista huérfana `contacto` |
| `templates/base.html` | `lang="es"`, meta description, SRI hash actualizado, `{% block titulo %}` unificado |
| `templates/articulos/*.html` | Actualizar `{% url %}` con nuevos nombres, unificar `titulo` |
| `templates/usuarios/*.html` | Actualizar `{% url %}` con nuevos nombres |
| `templates/contacto/*.html` | Actualizar `{% url %}` con nuevos nombres |
| `.gitignore` | Poblar con entradas Python/Django |
| `requirements.txt` | Agregar `python-decouple`, `pytest`, `pytest-django`, `pytest-cov`, `factory-boy` |

### Archivos eliminados

| Archivo | Razón |
|---------|-------|
| `apps/articulos/views.py` | Reemplazado por paquete `views/` |
| `blog_cocina/views.py` | Si queda vacío después de eliminar `contacto` (verificar: `home` y `acerca_de` se mantienen) |

---

## Diagrama de Arquitectura Final

```
┌─────────────────────────────────────────────────────────────┐
│                    BLOG DE COCINA                             │
│                  Django 4.2.3 + MySQL                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │   usuarios   │  │  articulos   │  │    contacto      │    │
│  │              │  │              │  │                  │    │
│  │ Usuario      │  │ Articulo ─┐  │  │ Contacto         │    │
│  │ (Abstract)   │  │ Categoria◄┘  │  │                  │    │
│  │              │  │ Comentario   │  │                  │    │
│  │ helpers:     │  │              │  │                  │    │
│  │ es_miembro() │  │ views/       │  │                  │    │
│  │ es_colab()   │  │ ├─articulos  │  │                  │    │
│  │ es_admin()   │  │ ├─categorias │  │                  │    │
│  │ puede_editar │  │ └─comentarios│  │                  │    │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘    │
│         │                 │                                   │
│    ┌────▼─────────────────▼──────┐                            │
│    │     Django auth Groups      │                            │
│    │  ┌──────────┐ ┌───────────┐ │                            │
│    │  │ Miembro  │ │Colaborador│ │                            │
│    │  └──────────┘ └───────────┘ │                            │
│    │  ┌──────────────┐           │                            │
│    │  │ Administrador│           │                            │
│    │  └──────────────┘           │                            │
│    └─────────────────────────────┘                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                 Settings Layer                         │    │
│  │  .env ──► base.py(config) ──► local.py / production   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                 Test Layer                             │    │
│  │  pytest-django + factory_boy + pytest-cov              │    │
│  │  Estructura: tests/ por app con factories y conftest   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Validación del Diseño

Cada decisión se alinea con las specs del documento `spec.md`:

| Decisión de diseño | Specs cubiertas |
|--------------------|-----------------|
| D1: Autorización con grupos | SPEC-2.1, 2.2, 2.3, 2.4 |
| D2: Submódulos en views | SPEC-3.4 |
| D3: Settings con decouple | SPEC-1.1, 1.2, 2.5, 2.6, 2.7, 2.8, 2.9, 3.9 |
| D4: Tests con pytest + factory_boy | SPEC-4.1 a 4.7 |
| D5: Convenciones snake_case + docstrings | SPEC-3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.8, 3.10, 3.11 |

---

## Riesgos del Diseño

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| El cambio de `BASE_DIR` a 3 niveles rompe paths en Windows | Media | Alto | Verificar cada `BASE_DIR /` y `os.path.dirname(BASE_DIR)` con `python manage.py check` |
| La migración de datos de `tipo_usuario` → grupos asigna mal a algún usuario | Baja | Medio | La data migration tiene un `mapa` explícito. Si un `tipo_usuario` no está en el mapa, cae en `Miembro` (seguro por defecto). |
| `ComentarioForm.__init__` asigna `user.username` (string) a FK | Alta | Alto | Corregido en D5/SPEC-3.10: asignar `self.instance.usuario_comentario = user` (instancia). |
| Redirects 301 acumulados en `blog_cocina/urls.py` generan deuda | Baja | Bajo | Comentario `TODO: eliminar después de 3 meses` en cada redirect block. |
