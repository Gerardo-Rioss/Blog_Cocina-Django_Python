# Especificaciones: Refactor Integral de Calidad de Código y Seguridad

**Change ID:** `refactor-calidad-codigo`
**Date:** 2026-07-12
**Based on:** proposal.md (2026-07-12)

---

## Ola 1 — Parche de Emergencia (Critical Fixes)

**Objetivo:** Eliminar bugs que rompen la aplicación y detener filtraciones de datos sensibles.
**Dependencias:** Ninguna. Es la ola base y se puede comenzar inmediatamente.
**Criterio de completitud:** La aplicación debe iniciar sin errores de modelo/señales, las credenciales no deben estar hardcodeadas en el repositorio, y el `.gitignore` debe proteger artefactos sensibles.

---

### SPEC-1.1: Extraer SECRET_KEY y credenciales DB a variables de entorno

**Objetivo:** Eliminar la exposición hardcodeada de `SECRET_KEY`, `NAME`, `USER`, `PASSWORD`, `HOST` y `PORT` de la base de datos en `blog_cocina/settings/base.py`.

**Archivos afectados:**
- `blog_cocina/settings/base.py` (extraer valores)
- `.env` (crear con valores actuales como defaults de desarrollo)
- `.env.example` (crear template sin valores reales)
- `requirements.txt` (agregar `python-decouple`)

**Criterios de aceptación:**
- [ ] `SECRET_KEY` en `base.py` referencia `config('SECRET_KEY')` mediante `python-decouple`
- [ ] `DATABASES['default']` en `base.py` referencia `config('DB_NAME')`, `config('DB_USER')`, `config('DB_PASSWORD')`, `config('DB_HOST')`, `config('DB_PORT', default='3306')`
- [ ] `.env` existe con los valores actuales de desarrollo y NO está commiteado
- [ ] `.env.example` existe como template con claves sin valores reales (o valores placeholder `changeme`)
- [ ] `python-decouple` está declarado en `requirements.txt`
- [ ] `python manage.py check` no arroja errores de importación o configuración

**Edge cases:**
- ¿Qué pasa si `.env` no existe al iniciar? `decouple` debe arrojar `UndefinedValueError` con mensaje claro
- ¿Qué pasa en CI/CD sin `.env`? El template `.env.example` debe documentar cada variable requerida
- ¿Las configuraciones de `local.py`/`production.py` sobreescriben correctamente los defaults de `base.py`? Deben poder hacerlo

---

### SPEC-1.2: Poblar .gitignore con entradas completas para Python/Django

**Objetivo:** Proteger artefactos sensibles y de build que nunca deben versionarse.

**Archivos afectados:**
- `.gitignore` (poblar — actualmente vacío)

**Criterios de aceptación:**
- [ ] `.gitignore` incluye `__pycache__/`
- [ ] `.gitignore` incluye `*.py[cod]`
- [ ] `.gitignore` incluye `.env` (NO `.env.example`)
- [ ] `.gitignore` incluye `db.sqlite3`
- [ ] `.gitignore` incluye `media/`
- [ ] `.gitignore` incluye `staticfiles/` o `static_root/` (para `collectstatic`)
- [ ] `.gitignore` incluye `*.log`
- [ ] `.gitignore` incluye `.venv/`, `venv/`, `env/`
- [ ] `.gitignore` incluye `.vscode/` e `.idea/`
- [ ] `.gitignore` incluye `*.egg-info/`, `dist/`, `build/`
- [ ] `git status` no lista `__pycache__/` ni `.pyc` como untracked

**Edge cases:**
- ¿Archivos ya trackeados por git? Deben removerse del índice con `git rm --cached` para los patterns que apliquen
- ¿`.env.example` sigue trackeado? Sí, debe seguir siéndolo

---

### SPEC-1.3: Corregir señales post_save en usuarios/models.py

**Objetivo:** Eliminar la recursión infinita causada por `instance.save()` dentro del handler `post_save` y corregir la lógica invertida de asignación de `tipo_usuario`.

**Archivos afectados:**
- `usuarios/models.py` (señal `post_save`)
- `usuarios/apps.py` (registro de señales en `ready()`)

**Criterios de aceptación:**
- [ ] Ningún handler de señal Django en el proyecto llama a `instance.save()` sin condición de guarda que prevenga recursión
- [ ] La lógica de asignación de `tipo_usuario` refleja correctamente la intención de negocio (no invertida)
- [ ] La señal `post_save` de `Usuario` NO dispara un nuevo `post_save` en el mismo handler
- [ ] Al crear un `Usuario` nuevo, `tipo_usuario` se asigna correctamente según el rol esperado
- [ ] Al actualizar un `Usuario`, no se produce recursión ni doble asignación
- [ ] El chequeo de migraciones (`makemigrations --check`) no detecta cambios pendientes no intencionales

**Edge cases:**
- ¿Qué pasa si el handler se dispara desde fixtures o `loaddata`? Debe usar `raw=False` o un flag condicional
- ¿Qué pasa con `update()` del QuerySet (bypassea `save()`)? Debe documentarse que `update()` no dispara señales, como limitación conocida

---

### SPEC-1.4: Corregir indentación de Contacto.__str__

**Objetivo:** Mover el método `__str__` de la clase `Contacto` dentro de la definición de clase, donde pertenece.

**Archivos afectados:**
- `contacto/models.py`

**Criterios de aceptación:**
- [ ] `Contacto.__str__` está definido DENTRO de `class Contacto(models.Model):` con indentación de 4 espacios
- [ ] `Contacto.__str__` retorna el `nombre` o una representación útil en string del objeto
- [ ] `python manage.py shell -c "from contacto.models import Contacto; print(str(Contacto(nombre='Test')))"` funciona sin error

**Edge cases:**
- ¿Hay otros métodos fuera de clase en el mismo archivo? Revisar y corregir si aplica
- ¿El archivo termina con newline? Debe cumplir PEP 8

---

### SPEC-1.5: Corregir default='Sin categoría' en FK categoria_articulo

**Objetivo:** Eliminar `default='Sin categoría'` del campo `categoria_articulo` (ForeignKey), lo cual no es válido en Django porque un FK espera una instancia o ID, no un string.

**Archivos afectados:**
- `articulos/models.py` (modelo `Articulo`)

**Criterios de aceptación:**
- [ ] `categoria_articulo` ForeignKey NO tiene `default='Sin categoría'`
- [ ] Si se requiere una categoría por defecto, se usa `default=1` o `null=True, blank=True` con un manejo apropiado
- [ ] Las migraciones generadas (`makemigrations`) reflejan el cambio sin errores
- [ ] Los artículos existentes que dependían del default quedan en un estado válido (migración de datos si es necesario)
- [ ] Las vistas de creación/edición de artículos manejan correctamente el caso de categoría no seleccionada

**Edge cases:**
- ¿Artículos existentes sin categoría? La migración debe asignarlos a una categoría válida o permitir NULL
- ¿Restricción `on_delete` actual? Debe ser `models.SET_NULL` o `models.PROTECT` según el caso de negocio; documentar qué pasa al borrar una categoría con artículos

---

### SPEC-1.6: Proteger delete_articulo con verificación de ownership o staff

**Objetivo:** Evitar que cualquier usuario autenticado pueda eliminar artículos ajenos.

**Archivos afectados:**
- `articulos/views.py` (vista `delete_articulo` o equivalente)

**Criterios de aceptación:**
- [ ] La vista que maneja eliminación de artículos verifica que `request.user == articulo.autor` O `request.user.tipo_usuario == 'Administrador'`
- [ ] Un usuario NO autorizado (ni autor ni admin) recibe HTTP 403 Forbidden o redirect con mensaje de error
- [ ] Un usuario NO autenticado es redirigido al login (HTTP 302) antes de llegar a la verificación de ownership
- [ ] El template de confirmación de eliminación (`articulo_confirm_delete.html` o similar) también está protegido
- [ ] La acción de eliminar usa método POST (no GET)

**Edge cases:**
- ¿Superuser de Django? Debe poder eliminar cualquier artículo
- ¿Usuario staff de Django (is_staff=True)? Debe tratarse como admin
- ¿Double-submit prevention? Usar redirect después de POST exitoso (Post/Redirect/Get)
- ¿Artículo con comentarios asociados? `on_delete=models.CASCADE` debe limpiarlos

---

### SPEC-1.7: Reemplazar request.POST.get() en add_comentario por ComentarioForm

**Objetivo:** Sustituir el acceso directo a `request.POST` en la vista de comentarios por un Django Form con validación completa.

**Archivos afectados:**
- `articulos/views.py` (vista `add_comentario` o equivalente)
- `articulos/forms.py` (crear o modificar `ComentarioForm`)
- `articulos/models.py` (modelo `Comentario` — referencia para campos)

**Criterios de aceptación:**
- [ ] Existe `ComentarioForm(forms.ModelForm)` en `articulos/forms.py` con `model = Comentario` y `fields = ['contenido']`
- [ ] La vista `add_comentario` instancia `ComentarioForm(request.POST)` y llama a `form.is_valid()` antes de guardar
- [ ] La vista maneja `form.save(commit=False)` para asignar `usuario_comentario` y `articulo_comentario` antes del save final
- [ ] Errores de validación se muestran al usuario en el template (no en blanco ni 500)
- [ ] `contenido` vacío es rechazado con mensaje de validación apropiado
- [ ] `contenido` excesivamente largo (ej. >10000 caracteres) es rechazado con mensaje claro
- [ ] XSS básico: `<script>alert('xss')</script>` en contenido se escapa al renderizar (Django auto-escapa templates, pero verificar)

**Edge cases:**
- ¿Usuario no autenticado? La vista debe requerir `@login_required`
- ¿Artículo inexistente? Retornar 404 si el ID del artículo no existe
- ¿POST a artículo inexistente? Mismo manejo que GET — 404
- ¿Método GET? Mostrar formulario vacío (o no mostrar nada si se renderiza inline)

---

## Ola 2 — Seguridad y Configuración (Security Hardening)

**Objetivo:** Implementar autorización robusta con grupos Django y preparar la configuración para despliegue productivo.
**Dependencias:** Ola 1 completada (necesita modelos corregidos y `.env` funcionando).
**Criterio de completitud:** Ningún endpoint debe ser accesible sin autorización apropiada; settings de producción deben aplicar hardening razonable; `wsgi.py`/`asgi.py` deben funcionar.

---

### SPEC-2.1: Implementar sistema de autorización con grupos Django y UserPassesTestMixin

**Objetivo:** Reemplazar las verificaciones ad-hoc basadas en `tipo_usuario` (string en CharField) por un sistema que use grupos nativos de Django (`auth.Group`) y `UserPassesTestMixin` para proteger vistas basadas en clases, y `@user_passes_test` para vistas basadas en funciones.

**Archivos afectados:**
- `usuarios/models.py` (agregar lógica de asignación a grupos en señal `post_save`)
- `articulos/views.py` (aplicar mixins/decorators)
- `usuarios/management/commands/` (nuevo: comando de gestión `setup_groups` para crear grupos iniciales)
- Migración de datos (nuevo: `usuarios/migrations/XXXX_populate_groups.py`)

**Criterios de aceptación:**
- [ ] Existen grupos Django: `Colaborador`, `Administrador` (creados por migración de datos o comando `setup_groups`)
- [ ] La señal `post_save` de `Usuario` asigna el grupo correspondiente según el valor de `tipo_usuario` en cada save
- [ ] El comando `python manage.py setup_groups` crea los grupos y asigna usuarios existentes
- [ ] Las vistas que requieren permisos usan `UserPassesTestMixin` con un `test_func` que verifica membresía a grupo, NO `tipo_usuario == 'string'`
- [ ] Los tests existentes (si los hay) o los nuevos de Ola 4 validan que cada rol solo accede a lo que debe

**Edge cases:**
- ¿Usuario sin grupo? Debe asignarse a un grupo default (ej. `Colaborador`) en el `post_save`
- ¿Superuser sin `tipo_usuario`? No debe romper la señal; asignar `Administrador` por defecto
- ¿Migración de datos en DB con datos existentes? La data migration debe mapear `tipo_usuario` actual a grupo sin pérdida
- ¿`tipo_usuario` con valor desconocido? Log warning y asignar grupo más restrictivo (`Colaborador`)

---

### SPEC-2.2: Migrar verificaciones tipo_usuario == 'Miembro' por checks de permisos reales

**Objetivo:** Reemplazar TODAS las ocurrencias de comparación directa de strings `tipo_usuario == 'Miembro'`, `tipo_usuario == 'Administrador'` por verificaciones basadas en grupos Django.

**Archivos afectados:**
- `articulos/views.py` (todas las vistas con verificación de rol)
- `articulos/templates/` (condicionales que muestran botones de admin/colaborador)
- `usuarios/views.py` (si existen vistas administrativas)
- Cualquier otro archivo que compare `tipo_usuario` como string

**Criterios de aceptación:**
- [ ] `grep -r "tipo_usuario =="` en el código fuente retorna 0 resultados (excepto en migraciones, señales, o definición del modelo)
- [ ] Las vistas usan `request.user.groups.filter(name='Administrador').exists()` o equivalentes
- [ ] Los templates usan `{% if user.groups.all.0.name == 'Administrador' %}` o un context processor que inyecte flags
- [ ] Las vistas de edición/eliminación de artículos verifican ownership O pertenencia al grupo `Administrador`
- [ ] Las vistas de creación de artículos verifican pertenencia a `Colaborador` O `Administrador`

**Edge cases:**
- ¿Vistas basadas en funciones sin decorator? Agregar `@user_passes_test`
- ¿Templates que muestran UI administrativa sin verificación de backend? El backend sigue siendo la fuente de verdad; el template es solo conveniencia visual
- ¿Referencias en `manage.py` commands custom? Revisar y migrar si existen

---

### SPEC-2.3: Proteger listarMensajes con login_required y restricción de staff

**Objetivo:** Evitar que usuarios no autenticados o no autorizados accedan a la lista de mensajes de contacto.

**Archivos afectados:**
- `contacto/views.py` (vista `listarMensajes` o equivalente)
- `contacto/urls.py` (si la URL está expuesta sin protección)

**Criterios de aceptación:**
- [ ] `listarMensajes` requiere `@login_required` (o `LoginRequiredMixin` si es CBV)
- [ ] `listarMensajes` verifica que `request.user.groups.filter(name='Administrador').exists()` o `request.user.is_staff`
- [ ] Usuario no autenticado es redirigido al login
- [ ] Usuario autenticado pero no admin recibe HTTP 403
- [ ] Solo se listan mensajes en la vista; las acciones (eliminar, responder) también están protegidas

**Edge cases:**
- ¿Hay acciones de eliminación de mensajes? Deben estar igualmente protegidas
- ¿Qué pasa si no hay mensajes? Mostrar template con mensaje "No hay mensajes" — no 404 ni 500

---

### SPEC-2.4: Descomentar y corregir verificación de ownership en edit_comentario

**Objetivo:** Activar la verificación de ownership en la edición de comentarios que actualmente está comentada, permitiendo que solo el autor del comentario o un administrador puedan editarlo.

**Archivos afectados:**
- `articulos/views.py` (vista `edit_comentario` o equivalente)

**Criterios de aceptación:**
- [ ] La vista `edit_comentario` verifica que `request.user == comentario.usuario_comentario` O `request.user.groups.filter(name='Administrador').exists()`
- [ ] La verificación NO está comentada
- [ ] Usuario no autorizado recibe HTTP 403
- [ ] El formulario de edición solo permite modificar `contenido` (no `usuario_comentario` ni `articulo_comentario`)
- [ ] La vista usa POST para guardar cambios y redirect al detalle del artículo después

**Edge cases:**
- ¿Comentario inexistente? Retornar 404
- ¿Artículo asociado al comentario fue eliminado? El comentario debería haberse eliminado en cascada (verificar `on_delete`)
- ¿Usuario intenta modificar `usuario_comentario` vía POST manipulado? El form debe usar `fields=['contenido']` exclusivamente

---

### SPEC-2.5: Corregir LANGUAGE_CODE a 'es-AR'

**Objetivo:** Corregir el valor inválido de `LANGUAGE_CODE` en settings.

**Archivos afectados:**
- `blog_cocina/settings/base.py`

**Criterios de aceptación:**
- [ ] `LANGUAGE_CODE = 'es-AR'` (o `'es-ar'` — Django normaliza)
- [ ] `python manage.py check` no arroja warnings sobre LANGUAGE_CODE
- [ ] Los templates que usan `{% language %}` o `{% get_current_language %}` obtienen `es-ar`
- [ ] La interfaz de admin de Django se muestra en español (si `USE_I18N=True`)

**Edge cases:**
- ¿El locale `es-AR` está instalado en el sistema? No es necesario; Django incluye traducciones para español
- ¿Otros settings regionales (`TIME_ZONE`, `USE_TZ`)? Verificar que `TIME_ZONE` sea correcto para Argentina (`'America/Argentina/Buenos_Aires'`)

---

### SPEC-2.6: Agregar SECURE_* settings en production.py

**Objetivo:** Configurar headers de seguridad HTTP para despliegue productivo con HTTPS.

**Archivos afectados:**
- `blog_cocina/settings/production.py`

**Criterios de aceptación:**
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SECURE_HSTS_SECONDS = 31536000` (1 año)
- [ ] `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- [ ] `SECURE_HSTS_PRELOAD = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_BROWSER_XSS_FILTER = True`
- [ ] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [ ] `X_FRAME_OPTIONS = 'DENY'`
- [ ] Estos settings NO están en `base.py` ni `local.py` (solo producción)

**Edge cases:**
- ¿Desarrollo local sin HTTPS? `local.py` NO debe activar estos settings; el desarrollador local usa HTTP
- ¿Proxy inverso (nginx) que termina TLS? Configurar `SECURE_PROXY_SSL_HEADER` correctamente
- Documentar en `production.py` que estos settings requieren HTTPS configurado en el servidor

---

### SPEC-2.7: Rellenar production.py con configuración real para deploy

**Objetivo:** Completar `production.py` para que esté listo para un deploy real.

**Archivos afectados:**
- `blog_cocina/settings/production.py`

**Criterios de aceptación:**
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` se lee de variable de entorno: `config('ALLOWED_HOSTS', cast=Csv())`
- [ ] `DATABASES['default']` usa variables de entorno para host, puerto, credenciales (no hardcodea valores)
- [ ] `STATIC_ROOT` está definido (apunta a un directorio fuera del proyecto, ej. `/var/www/static/` o configurable por variable)
- [ ] `MEDIA_ROOT` está definido (apunta a un directorio fuera del proyecto, ej. `/var/www/media/` o configurable por variable)
- [ ] Logging está configurado con file handler para errores (no solo console)
- [ ] `ADMINS` se lee de variable de entorno
- [ ] `EMAIL_BACKEND` usa SMTP real (no console)
- [ ] `python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='blog_cocina.settings.production'; import django; django.setup()"` no arroja errores

**Edge cases:**
- ¿`production.py` importa de `base.py`? Debe hacerlo: `from .base import *`
- ¿Settings sensibles que difieren de `local.py`? Cada setting debe ser revisado para no heredar configuraciones de desarrollo
- ¿`SECRET_KEY` en producción? Debe venir de variable de entorno, nunca hardcodeado

---

### SPEC-2.8: Corregir wsgi.py y asgi.py para apuntar a blog_cocina.settings (package)

**Objetivo:** Corregir `wsgi.py` y `asgi.py` para que referencien el paquete `blog_cocina.settings` en lugar del módulo roto actual.

**Archivos afectados:**
- `blog_cocina/wsgi.py`
- `blog_cocina/asgi.py`

**Criterios de aceptación:**
- [ ] `wsgi.py` contiene: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_cocina.settings')`
- [ ] `asgi.py` contiene: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_cocina.settings')`
- [ ] `wsgi.py` expone `application = get_wsgi_application()`
- [ ] `asgi.py` expone `application = get_asgi_application()`
- [ ] `python -c "from blog_cocina.wsgi import application"` no arroja error
- [ ] `python -c "from blog_cocina.asgi import application"` no arroja error

**Edge cases:**
- ¿El paquete `blog_cocina/settings/` tiene `__init__.py`? Verificar; si no, crearlo
- ¿El archivo `blog_cocina/settings.py` (módulo viejo) sigue existiendo? Debe eliminarse o renombrarse para evitar ambigüedad con el paquete

---

### SPEC-2.9: Agregar STATIC_ROOT para collectstatic

**Objetivo:** Definir `STATIC_ROOT` en settings para que `collectstatic` funcione correctamente en producción.

**Archivos afectados:**
- `blog_cocina/settings/base.py` (definición base)
- `blog_cocina/settings/production.py` (override de producción si es diferente)

**Criterios de aceptación:**
- [ ] `STATIC_ROOT = BASE_DIR / 'staticfiles'` está definido en `base.py`
- [ ] El directorio `staticfiles/` está en `.gitignore`
- [ ] `python manage.py collectstatic --dry-run` lista los archivos sin errores
- [ ] `python manage.py collectstatic` copia archivos a `staticfiles/` exitosamente

**Edge cases:**
- ¿Conflictos con archivos del mismo nombre en diferentes apps? Django resuelve por orden de `INSTALLED_APPS`; documentar
- ¿Archivos estáticos de admin? `django.contrib.staticfiles` debe estar en `INSTALLED_APPS`

---

## Ola 3 — Calidad de Código y Mantenibilidad

**Objetivo:** Elevar la calidad del código para que refleje estándares profesionales (PEP 8, docstrings, estructura modular).
**Dependencias:** Olas 1 y 2 completadas (necesita autorización funcional antes de refactorizar vistas).
**Criterio de completitud:** Código PEP 8 compliant, nombres en snake_case, docstrings en ≥80% de módulos clave, templates semánticamente correctos, sin código muerto.

---

### SPEC-3.1: Unificar convención de nombres a snake_case en vistas, URLs y funciones

**Objetivo:** Renombrar TODAS las vistas, funciones, y nombres de URL que usen camelCase o mixedCase a snake_case (PEP 8).

**Archivos afectados:**
- `articulos/views.py` (todas las funciones de vista)
- `articulos/urls.py` (names de URL patterns)
- `usuarios/views.py` (si existen funciones afectadas)
- `usuarios/urls.py`
- `contacto/views.py`
- `contacto/urls.py`
- `blog_cocina/urls.py` (URLconf raíz)
- Todos los templates que referencien URLs (`{% url 'nombre_url' %}`)
- Todos los `reverse()` y `redirect()` en código Python

**Criterios de aceptación:**
- [ ] TODAS las funciones de vista usan snake_case (ej. `crear_articulo`, no `crearArticulo`)
- [ ] TODOS los `name='...'` en `urls.py` usan snake_case con guiones bajos como separadores
- [ ] `grep -rP '(def [a-z]+[A-Z])' --include='*.py'` no encuentra funciones con camelCase en módulos de vistas
- [ ] `grep -rP "name='[a-z]+[A-Z]" --include='*.py'` no encuentra URL names con camelCase
- [ ] Templates actualizan `{% url %}` tags para usar nuevos nombres
- [ ] Navegación manual: todas las URLs del sitio cargan sin errores de reverse match

**Edge cases:**
- ¿URLs externas o bookmarks? Si hay riesgo, agregar redirects 301 de viejos nombres a nuevos en la URLconf raíz
- ¿`@login_url` en decorators? Verificar que los nombres de login URL estén actualizados
- ¿Nombres de modelo/clase? NO se renombran (usar `CamelCase` para clases es PEP 8)
- ¿Variables de template? Mantener consistencia con el contexto pasado desde la vista

---

### SPEC-3.2: Agregar select_related / prefetch_related en queries N+1

**Objetivo:** Optimizar queries en vistas que disparan múltiples consultas a la base de datos por iteración (problema N+1).

**Archivos afectados:**
- `articulos/views.py` (vista de listado de artículos, vista de detalle)
- Cualquier vista que itere sobre un QuerySet y acceda a ForeignKeys

**Criterios de aceptación:**
- [ ] Vista de listado de artículos usa `Articulo.objects.select_related('categoria_articulo', 'autor').all()`
- [ ] Vista de detalle de artículo usa `Articulo.objects.select_related('categoria_articulo', 'autor').prefetch_related('comentario_set__usuario_comentario').get(pk=...)`
- [ ] El número de queries SQL para cargar una página de listado (20 artículos) se reduce en al menos 40% respecto al código original
- [ ] `django.db.connection.queries` (o django-debug-toolbar) confirma que no hay queries adicionales por iteración

**Edge cases:**
- ¿QuerySet filtrado por `request.user`? Mantener filtros existentes, solo agregar `select_related`/`prefetch_related`
- ¿Paginación? `select_related`/`prefetch_related` son compatibles con el paginator de Django
- ¿Depth de relaciones? Solo un nivel de profundidad (FK directa o reverse FK); no aplicar select_related en relaciones que no se usan

---

### SPEC-3.3: Agregar docstrings a modelos, vistas principales y forms

**Objetivo:** Documentar la intención y comportamiento de los módulos clave del proyecto.

**Archivos afectados:**
- `usuarios/models.py`
- `articulos/models.py`
- `contacto/models.py`
- `articulos/views.py`
- `articulos/forms.py`
- `usuarios/views.py` (si existen)
- `contacto/views.py`
- `contacto/forms.py`

**Criterios de aceptación:**
- [ ] Cada clase de modelo tiene docstring explicando su propósito y relaciones clave
- [ ] Cada método `__str__`, `save()`, `get_absolute_url()` en modelos tiene docstring
- [ ] Cada función de vista tiene docstring con: propósito, args de URL si aplica, template que renderiza, y contexto que pasa
- [ ] Cada `ModelForm` tiene docstring explicando validaciones custom si las tiene
- [ ] Los docstrings usan formato Google style o reStructuredText de manera consistente en todo el proyecto
- [ ] `python -c "import ast; ..."` o tool de linting puede extraer docstrings sin error de sintaxis

**Edge cases:**
- ¿Métodos heredados de Django? No documentar métodos que son override trivial (ej. `Meta` interna)
- ¿Docstrings en inglés o español? Consistente en todo el proyecto; preferentemente español por ser el dominio del proyecto, con términos técnicos en inglés

---

### SPEC-3.4: Separar vistas de articulos/views.py en submódulos

**Objetivo:** Modularizar el archivo `articulos/views.py` que contiene vistas de artículos, categorías y comentarios en un paquete `articulos/views/`.

**Archivos afectados:**
- `articulos/views.py` → eliminar
- `articulos/views/__init__.py` (nuevo: importa todas las vistas para mantener compatibilidad)
- `articulos/views/articulos.py` (nuevo: vistas CRUD de artículos)
- `articulos/views/categorias.py` (nuevo: vistas de categorías)
- `articulos/views/comentarios.py` (nuevo: vistas de comentarios)
- `articulos/urls.py` (actualizar imports)

**Criterios de aceptación:**
- [ ] `articulos/views/` es un paquete Python con `__init__.py`
- [ ] `articulos/views/__init__.py` importa y re-exporta todas las vistas con `from .articulos import *`, etc.
- [ ] `articulos/urls.py` puede seguir importando desde `articulos.views` sin cambios (o cambios mínimos)
- [ ] `python manage.py check` no detecta errores de importación
- [ ] Todas las URLs de artículos, categorías y comentarios cargan sin error
- [ ] El archivo `articulos/views.py` original ya no existe

**Edge cases:**
- ¿Import circular? La estructura `__init__.py → submódulo → models` no debe crear ciclos; verificar
- ¿Views que dependen de otras views? Asegurar que los imports entre submódulos no generen dependencias circulares
- ¿Backward compatibility? Si hay código externo que importa `from articulos.views import X`, debe seguir funcionando

---

### SPEC-3.5: Eliminar código muerto

**Objetivo:** Remover código que nunca se ejecuta: imports no usados, variables no referenciadas, código comentado, y referencias a valores de `tipo_usuario` que no existen en el dominio.

**Archivos afectados:**
- Todos los archivos `.py` del proyecto (scope completo)
- Templates con bloques comentados que no se usarán

**Criterios de aceptación:**
- [ ] `grep -r "tipo_usuario == 'publico'"` retorna 0 resultados
- [ ] `grep -r "tipo_usuario == 'Publico'"` retorna 0 resultados
- [ ] Bloques de código comentado (no docstrings ni comentarios explicativos) son eliminados
- [ ] Imports no usados son eliminados (verificable con `flake8` o `autoflake --check`)
- [ ] Variables asignadas pero nunca leídas son eliminadas
- [ ] `python manage.py check` sigue pasando sin errores

**Edge cases:**
- ¿Código comentado que es documentación intencional? Evaluar caso por caso: si explica un edge case o bug conocido, mantener como comentario
- ¿Signals importados en `apps.py`? No marcarlos como no usados; son side-effect imports
- ¿`__init__.py` imports? Son intencionales para re-export; no eliminar

---

### SPEC-3.6: Corregir templates: lang, bloques title, meta description

**Objetivo:** Corregir atributos semánticos incorrectos en templates (lang, title, meta tags).

**Archivos afectados:**
- `templates/base.html` (layout base)
- `templates/articulos/` (todos los templates de artículos)
- `templates/usuarios/` (templates de login, registro, perfil)
- `templates/contacto/` (templates de contacto)

**Criterios de aceptación:**
- [ ] `<html lang="es">` en TODOS los templates base (no `lang="en"`)
- [ ] `<meta name="description" content="...">` presente en `base.html` con valor apropiado (o bloque para override)
- [ ] Todos los templates definen `{% block title %}` o `{% block titulo %}` de manera consistente
- [ ] No hay mezcla de `title` y `titulo` como nombres de bloque — unificar a uno solo en todos los templates
- [ ] El `<title>` en `<head>` usa el bloque unificado
- [ ] `<meta charset="UTF-8">` presente en `base.html`

**Edge cases:**
- ¿Templates de terceros (admin, allauth)? No modificar
- ¿Templates con múltiples bloques `title` anidados? Unificar a un solo bloque
- ¿Templates que heredan de `base.html` y sobreescriben title? Verificar que todos funcionen

---

### SPEC-3.7: Remover {% static %} de urls.py de apps

**Objetivo:** Eliminar patrones de URL que sirven archivos estáticos desde `urls.py` de aplicaciones individuales. Esto solo debe configurarse en la URLconf raíz y solo en desarrollo.

**Archivos afectados:**
- `articulos/urls.py`
- `usuarios/urls.py`
- `contacto/urls.py`
- `blog_cocina/urls.py` (URLconf raíz — verificar que tenga `+ static(...)` condicional)

**Criterios de aceptación:**
- [ ] Ningún `urls.py` de app contiene `static(settings.STATIC_URL, ...)` o `static(settings.MEDIA_URL, ...)`
- [ ] La URLconf raíz (`blog_cocina/urls.py`) sirve estáticos SOLO cuando `settings.DEBUG = True`
- [ ] `python manage.py check` no detecta errores de URLconf
- [ ] Archivos estáticos y media files se sirven correctamente en desarrollo

**Edge cases:**
- ¿MEDIA files en desarrollo? Deben servirse solo en DEBUG=True desde la URLconf raíz
- ¿Producción? No se sirven estáticos desde Django; se espera que nginx/apache lo haga

---

### SPEC-3.8: Agregar SRI hash al CDN de Bootstrap

**Objetivo:** Agregar atributo `integrity` con hash SRI (Subresource Integrity) a las tags `<link>` y `<script>` que cargan Bootstrap desde CDN, para prevenir ataques de supply chain si el CDN es comprometido.

**Archivos afectados:**
- `templates/base.html`

**Criterios de aceptación:**
- [ ] Tags de Bootstrap CSS incluyen `integrity="sha384-..."` y `crossorigin="anonymous"`
- [ ] Tags de Bootstrap JS incluyen `integrity="sha384-..."` y `crossorigin="anonymous"`
- [ ] Los hashes corresponden exactamente a la versión de Bootstrap usada
- [ ] La página carga sin errores de SRI en el navegador (verificar en DevTools Console)

**Edge cases:**
- ¿Actualización de Bootstrap? Si se cambia la versión, se deben recalcular los hashes
- ¿Fallback si CDN falla? Considerar proveer un fallback local, pero fuera del scope de esta spec

---

### SPEC-3.9: Corregir BASE_DIR para que apunte a la raíz del proyecto

**Objetivo:** Corregir `BASE_DIR` en settings para que apunte al directorio raíz del proyecto (donde está `manage.py`), no al directorio `blog_cocina/`.

**Archivos afectados:**
- `blog_cocina/settings/base.py`

**Criterios de aceptación:**
- [ ] `BASE_DIR = Path(__file__).resolve().parent.parent` apunta a la raíz del proyecto (un nivel arriba de `blog_cocina/`)
- [ ] `BASE_DIR / 'templates'` resuelve correctamente a `C:\...\Blog_Cocina-Django_Python\templates\`
- [ ] `BASE_DIR / 'media'` resuelve correctamente
- [ ] `STATICFILES_DIRS` y `TEMPLATES[0]['DIRS']` referencian directorios existentes usando `BASE_DIR`
- [ ] `python manage.py check` no arroja warnings sobre directorios de templates o static

**Edge cases:**
- ¿Settings en diferentes niveles? Verificar que local.py y production.py hereden el BASE_DIR correcto de base.py
- ¿Cambios en estructura de directorios? Si `BASE_DIR` cambia, todos los paths relativos deben recalcularse
- ¿El valor anterior de `BASE_DIR` estaba causando path resolution issues? Verificar explícitamente que `TEMPLATES[0]['DIRS']` existe

---

### SPEC-3.10: Corregir asignación de FK usuario_comentario como string en forms

**Objetivo:** Corregir cualquier asignación de ForeignKey como string en formularios (ej. `comentario.usuario_comentario = request.user.username`) por la asignación correcta de instancia (`comentario.usuario_comentario = request.user`).

**Archivos afectados:**
- `articulos/views.py` (vista de creación/edición de comentarios)
- `articulos/forms.py` (si el form incluye el FK)

**Criterios de aceptación:**
- [ ] `usuario_comentario` se asigna como instancia de `User` (no como string, ID, o username)
- [ ] `articulo_comentario` se asigna como instancia de `Articulo`
- [ ] Al guardar el comentario, no se arroja `ValueError: Cannot assign "'string'": "Comentario.usuario_comentario" must be a "User" instance`
- [ ] Los comentarios creados tienen la FK correcta (verificable en admin o shell)

**Edge cases:**
- ¿El form incluye `usuario_comentario` en `fields`? Si es así, debe excluirse y asignarse en la vista con `commit=False`
- ¿Request.user es AnonymousUser? La vista debe requerir `@login_required`

---

### SPEC-3.11: Eliminar vista huérfana contacto en blog_cocina/views.py

**Objetivo:** Eliminar la vista `contacto` definida en `blog_cocina/views.py` (directorio del proyecto, no la app `contacto`) que no está conectada a ninguna URL y duplica funcionalidad.

**Archivos afectados:**
- `blog_cocina/views.py` (eliminar vista huérfana o el archivo completo si solo tiene esa vista)
- `blog_cocina/urls.py` (verificar que no haya URL pattern apuntando a esta vista)

**Criterios de aceptación:**
- [ ] La vista duplicada/huérfana `contacto` ya no existe en `blog_cocina/views.py`
- [ ] Si `blog_cocina/views.py` queda vacío, eliminar el archivo y su referencia en `blog_cocina/urls.py`
- [ ] La funcionalidad de contacto (app `contacto`) sigue funcionando normalmente
- [ ] `python manage.py check` no detecta imports rotos

**Edge cases:**
- ¿Otras vistas huérfanas en `blog_cocina/views.py`? Revisar y eliminar si no están conectadas a URL patterns
- ¿Vistas genéricas (`TemplateView`) usadas para páginas estáticas? Evaluar si deben moverse a una app o mantenerse

---

## Ola 4 — Cobertura de Tests

**Objetivo:** Establecer una suite de tests con ≥70% de cobertura en modelos, vistas y forms, garantizando que los refactors de Olas 1-3 no introduzcan regresiones.
**Dependencias:** Puede comenzar en paralelo con Ola 1 (tests de caracterización). Requiere Ola 2 completada para tests de autorización. El test final de integración requiere Ola 3 completada.
**Criterio de completitud:** ≥70% de cobertura en modelos, vistas y forms; todos los tests pasan; flujo de integración end-to-end cubierto.

---

### SPEC-4.1: Configurar pytest-django como test runner

**Objetivo:** Instalar y configurar `pytest-django` como el test runner del proyecto.

**Archivos afectados:**
- `requirements.txt` (agregar `pytest`, `pytest-django`, `pytest-cov`)
- `pytest.ini` o `pyproject.toml` (nuevo: configuración de pytest)

**Criterios de aceptación:**
- [ ] `pytest`, `pytest-django` y `pytest-cov` están en `requirements.txt`
- [ ] Archivo de configuración (`pytest.ini` o `[tool.pytest.ini_options]` en `pyproject.toml`) existe con:
  - `DJANGO_SETTINGS_MODULE = blog_cocina.settings.local`
  - `python_files = tests.py test_*.py *_tests.py`
  - `addopts = --strict-markers -v`
- [ ] `pytest --collect-only` descubre tests sin errores
- [ ] `pytest` ejecuta al menos 1 test dummy y reporta resultado

**Edge cases:**
- ¿Conflicto con unittest existente? No hay tests existentes, así que no hay conflicto
- ¿Base de datos de test? `pytest-django` usa `--reuse-db` por defecto; documentar para el equipo
- ¿Settings de test separados? No necesario por ahora; usar `local.py`

---

### SPEC-4.2: Tests unitarios de modelos

**Objetivo:** Probar la creación, validación y métodos de cada modelo.

**Archivos afectados:**
- `usuarios/tests/test_models.py` (nuevo)
- `articulos/tests/test_models.py` (nuevo)
- `contacto/tests/test_models.py` (nuevo)

**Criterios de aceptación:**
- [ ] `Usuario`: test de creación con `create_user()`, `tipo_usuario` default, `__str__`, username único
- [ ] `Articulo`: test de creación con FK a `Categoria` y `Usuario`, `__str__`, slug único, `get_absolute_url()`
- [ ] `Categoria`: test de creación, `__str__`, nombre único
- [ ] `Comentario`: test de creación con FK a `Articulo` y `Usuario`, `__str__`
- [ ] `Contacto`: test de creación, `__str__`, campos requeridos
- [ ] Cada modelo: test de constraint de unique, test de required fields (blank=False)
- [ ] Cada modelo: test de `on_delete` behavior (qué pasa al borrar el objeto referenciado)

**Edge cases:**
- ¿Slug con caracteres especiales? Verificar `slugify`
- ¿Usuario con `tipo_usuario` inválido? El modelo actual usa CharField sin choices; el test debe documentar este gap
- ¿Artículo sin categoría (si nullable)? Verificar comportamiento

---

### SPEC-4.3: Tests de señales

**Objetivo:** Verificar que las señales `post_save` de `Usuario` asignan correctamente `tipo_usuario` y los grupos Django correspondientes.

**Archivos afectados:**
- `usuarios/tests/test_signals.py` (nuevo)

**Criterios de aceptación:**
- [ ] Al crear un `Usuario` nuevo sin `tipo_usuario`, la señal asigna el valor default correcto
- [ ] Al crear un `Usuario` con `tipo_usuario='Administrador'`, se asigna al grupo `Administrador`
- [ ] Al crear un `Usuario` con `tipo_usuario='Colaborador'`, se asigna al grupo `Colaborador`
- [ ] Al actualizar un `Usuario` sin cambiar `tipo_usuario`, NO se dispara recursión
- [ ] La señal NO asigna grupo a usuarios que ya tienen grupo (evitar doble asignación)
- [ ] `Usuario.objects.update(tipo_usuario='Administrador')` (QuerySet.update) NO dispara la señal (documentar como limitación)

**Edge cases:**
- ¿Superuser creation? `createsuperuser` dispara `post_save`; verificar que no rompe
- ¿Usuario creado vía `loaddata`? La señal debe manejar `raw=True`

---

### SPEC-4.4: Tests de forms

**Objetivo:** Validar el comportamiento de cada formulario con datos válidos, inválidos y edge cases.

**Archivos afectados:**
- `articulos/tests/test_forms.py` (nuevo)
- `contacto/tests/test_forms.py` (nuevo)
- `usuarios/tests/test_forms.py` (nuevo)

**Criterios de aceptación:**
- [ ] `ComentarioForm`: válido con `contenido='Buen artículo'`; inválido con `contenido=''`; inválido con `contenido` > longitud máxima
- [ ] `ContactoForm`: válido con todos los campos llenos; inválido con campos requeridos vacíos; inválido con email malformado
- [ ] Formularios de registro/login (si existen): validación de username duplicado, validación de contraseñas no coincidentes
- [ ] Formularios de artículo: válido con campos requeridos; inválido sin título o contenido

**Edge cases:**
- ¿XSS en contenido? El form debe aceptar HTML pero el template debe escaparlo (test de integración)
- ¿Campos con `max_length`? Probar exactamente en el límite y un carácter más
- ¿Email con formatos RFC válidos pero inusuales? Aceptar según validación de Django

---

### SPEC-4.5: Tests de vistas: acceso anónimo, autorización por rol, métodos HTTP

**Objetivo:** Probar que cada vista responde correctamente según el estado de autenticación y rol del usuario.

**Archivos afectados:**
- `articulos/tests/test_views.py` (nuevo)
- `usuarios/tests/test_views.py` (nuevo)
- `contacto/tests/test_views.py` (nuevo)

**Criterios de aceptación:**
- [ ] Usuario ANÓNIMO:
  - Puede ver listado de artículos (HTTP 200)
  - Puede ver detalle de artículo (HTTP 200)
  - Puede ver listado de categorías (HTTP 200)
  - Es redirigido al login al intentar crear artículo (HTTP 302 → login)
  - Es redirigido al login al intentar comentar (HTTP 302 → login)
  - Es redirigido al login al intentar acceder a `listarMensajes` (HTTP 302 → login)
  - Recibe 404 o 403 al intentar eliminar un artículo
- [ ] Usuario COLABORADOR:
  - Puede crear artículos (HTTP 200 en GET, redirect en POST exitoso)
  - Puede editar sus propios artículos (HTTP 200)
  - NO puede editar artículos de otros (HTTP 403)
  - Puede comentar en cualquier artículo
  - NO puede eliminar artículos ajenos (HTTP 403)
  - NO puede acceder a `listarMensajes` (HTTP 403)
- [ ] Usuario ADMINISTRADOR:
  - Puede crear, editar y eliminar cualquier artículo
  - Puede acceder a `listarMensajes` (HTTP 200)
  - Puede eliminar comentarios de otros usuarios
- [ ] Métodos HTTP inválidos: POST a vista que solo acepta GET retorna 405 Method Not Allowed (o redirect apropiado)

**Edge cases:**
- ¿Usuario autenticado sin grupo? Debe tener comportamiento de Colaborador (o el rol más restrictivo)
- ¿`next` parameter en redirect de login? Debe preservarse para redirigir de vuelta después del login
- ¿CSRF token? Requests POST sin CSRF token deben ser rechazados

---

### SPEC-4.6: Tests de integración: flujo completo con roles

**Objetivo:** Probar el flujo end-to-end de la aplicación simulando el recorrido de un usuario real.

**Archivos afectados:**
- `tests/test_integration.py` o `articulos/tests/test_integration.py` (nuevo)

**Criterios de aceptación:**
- [ ] Flujo Colaborador:
  1. Login como colaborador
  2. Crear artículo con categoría existente
  3. Ver artículo en listado
  4. Editar el artículo (cambiar título)
  5. Ver cambios reflejados en detalle
  6. Comentar en artículo propio
  7. Intentar eliminar artículo de otro → 403
  8. Eliminar artículo propio → exitoso, redirigido a listado
- [ ] Flujo Administrador:
  1. Login como admin
  2. Eliminar artículo de otro usuario → exitoso
  3. Acceder a listado de mensajes de contacto → 200
- [ ] Flujo Anónimo:
  1. Navegar listado → artículos visibles
  2. Intentar comentar → redirigido a login
  3. Login → redirigido de vuelta al artículo
  4. Comentar → exitoso

**Edge cases:**
- ¿Sesión expirada durante el flujo? El test de integración puede no cubrir esto
- ¿DB transaction rollback entre tests? `pytest-django` con `-- transactional-db` o `django_db` marker
- ¿Artículo con slug duplicado? El sistema debe generar slug único; test debe verificar que no hay 500

---

### SPEC-4.7: Alcanzar ≥70% de cobertura en modelos, vistas y forms

**Objetivo:** Medir y garantizar que la suite de tests cubre al menos el 70% de las líneas de código en modelos, vistas y forms.

**Archivos afectados:**
- `pytest.ini` o `pyproject.toml` (configurar `--cov` targets)
- Cualquier archivo de código que requiera tests adicionales para alcanzar la meta

**Criterios de aceptación:**
- [ ] `pytest --cov=usuarios --cov=articulos --cov=contacto --cov-report=term-missing` muestra ≥70% en modelos
- [ ] `pytest --cov=usuarios --cov=articulos --cov=contacto --cov-report=term-missing` muestra ≥70% en vistas
- [ ] `pytest --cov=usuarios --cov=articulos --cov=contacto --cov-report=term-missing` muestra ≥70% en forms
- [ ] El reporte de coverage muestra explícitamente qué líneas NO están cubiertas
- [ ] Archivos de `settings/`, `urls.py`, `admin.py`, `wsgi.py`, `asgi.py` están excluidos del cálculo de cobertura (o documentados como fuera de scope)
- [ ] Todos los tests pasan en verde (0 failures, 0 errors)

**Edge cases:**
- ¿Cobertura incluye ramas (branch coverage)? `--cov-branch` es deseable pero no obligatorio para el 70%
- ¿Archivos de migraciones? Excluir del reporte de coverage
- ¿Líneas de `if __name__ == '__main__':`? Excluir o cubrir con test trivial

---

## Consideraciones Cross-Cutting

### Validación de no regresión

1. **Smoke test manual después de cada ola:**
   - Login con usuario colaborador → crear artículo → ver en listado → editar → comentar
   - Login con admin → eliminar artículo ajeno → ver mensajes de contacto
   - Anónimo → navegar listado → intentar comentar → login → comentar

2. **Verificaciones automáticas:**
   - `python manage.py check --deploy` después de Ola 2 (verifica settings de producción)
   - `python manage.py makemigrations --check --dry-run` después de cada cambio en modelos
   - `pytest` después de cada ola (Ola 4 incremental)

3. **Git diff review:** cada commit debe ser revisado para asegurar que no hay cambios accidentales fuera de scope.

### Orden de aplicación dentro de cada ola

- **Ola 1:** 1.1 → 1.2 → 1.4 → 1.5 → 1.3 → 1.7 → 1.6 (modelos y settings primero, luego señales, luego forms/vistas)
- **Ola 2:** 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.9 → 2.8 → 2.6 → 2.7 (grupos y migración primero, luego vistas protegidas, luego settings)
- **Ola 3:** 3.5 → 3.9 → 3.4 → 3.1 → 3.2 → 3.10 → 3.3 → 3.7 → 3.6 → 3.8 → 3.11 (limpieza primero, luego estructura, luego nombres, luego optimización, luego documentación y templates)
- **Ola 4:** 4.1 → 4.2 → 4.3 → 4.4 → 4.5 → 4.6 → 4.7 (configuración, unitarios, integración, cobertura)

### Puntos de verificación manual (smoke tests)

| Momento | Acción | Resultado esperado |
|---------|--------|--------------------|
| Post-Ola 1 | `python manage.py runserver` | Sin errores de modelo/señales |
| Post-Ola 1 | Login + crear artículo | Artículo creado sin errores |
| Post-Ola 1 | Comentar en artículo | Comentario creado con validación |
| Post-Ola 2 | Login como admin → eliminar artículo ajeno | Permitido |
| Post-Ola 2 | Login como colaborador → eliminar artículo ajeno | 403 Forbidden |
| Post-Ola 2 | Anónimo → `/contacto/mensajes/` | Redirect a login |
| Post-Ola 2 | `check --deploy` | Sin warnings de seguridad |
| Post-Ola 3 | Navegar todas las URLs | Sin errores de reverse match |
| Post-Ola 3 | Inspeccionar HTML → View Source | `lang="es"`, meta description |
| Post-Ola 4 | `pytest --cov` | ≥70%, todos verdes |

---

## Riesgos y Suposiciones

| Riesgo | Specs afectadas | Mitigación |
|--------|----------------|------------|
| Migración `tipo_usuario` → grupos Django rompe datos | 2.1, 2.2 | Data migration explícita + backup previo. Test de migración en Ola 4. |
| Renombrar URLs (3.1) rompe bookmarks | 3.1 | Redirects 301 de nombres viejos a nuevos si hay tráfico real. |
| Agregar autorización (2.1-2.4) bloquea usuarios legítimos | 2.2, 2.3, 2.4 | Tests por rol en Ola 4.5 + smoke test manual. |
| `production.py` causa 500 en staging | 2.6, 2.7 | Probar con `DJANGO_SETTINGS_MODULE` local antes de deploy. |
| Corregir `BASE_DIR` (3.9) rompe paths de templates/static | 3.9 | Verificar todos los `TEMPLATES[0]['DIRS']` y `STATICFILES_DIRS`. |
| Separar views (3.4) rompe imports | 3.4 | `__init__.py` re-exporta todo; test de humo de cada URL. |

---

## Suposiciones para el desarrollo

1. La base de datos actual contiene solo datos de prueba/demostración (no producción real).
2. El proyecto se seguirá desarrollando en Windows (lo que afecta paths y encoding).
3. Se usará `python-decouple` (no `python-dotenv`) para variables de entorno.
4. Se usará `pytest-django` (no `unittest`) como test runner.
5. Los nombres de URL se documentan pero no se proveen redirects 301 automáticos a menos que haya tráfico real.
6. No hay CI/CD pipeline; todas las verificaciones son manuales o locales.
7. El `AUTH_USER_MODEL` actual (`usuarios.Usuario`) se mantiene; solo se agregan grupos de Django.
8. MySQL sigue siendo la base de datos; no se migra a SQLite para tests (`pytest-django` lo maneja con `--reuse-db`).
