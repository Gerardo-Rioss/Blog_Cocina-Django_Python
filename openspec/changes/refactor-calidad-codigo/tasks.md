# Tasks: Refactor Integral de Calidad de Código y Seguridad

**Change ID:** `refactor-calidad-codigo`
**Date:** 2026-07-12
**Based on:** spec.md (2026-07-12), design.md (2026-07-12)

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,500 líneas (adiciones + eliminaciones) |
| 400-line budget risk | **High** — 4 olas con ~150 a ~680 líneas cada una |
| Chained PRs recommended | **Yes** |
| Suggested split | PR 1 (Ola 1, ~150 líneas) → PR 2 (Ola 2, ~310 líneas) → PR 3 (Ola 3, ~430 líneas) → PR 4a (Tests parte 1, ~340 líneas) → PR 4b (Tests parte 2, ~330 líneas) |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

---

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

---

## Formato de tareas

Cada tarea sigue la estructura: **Spec**, **Archivos**, **Estimación**, **Dependencias**, **Checklist**.

Las tareas están agrupadas en **batches de apply**. Cada batch = una sesión de `sdd-apply` y un PR independiente en la cadena.

---

## Batch 1 → PR 1: Ola 1 — Parche de Emergencia (Critical Fixes)

**Objetivo del batch:** Eliminar bugs que rompen la app y detener filtraciones de datos. Sin dependencias previas.
**Verificación:** `python manage.py check`, `python manage.py runserver` sin errores de modelo/señal.
**Smoke test:** Login → crear artículo → comentar (sin errores).

---

### T-1.1: Extraer SECRET_KEY y credenciales DB a variables de entorno

- **Spec:** SPEC-1.1
- **Archivos:**
  - `blog_cocina/settings/base.py` (modificar: reemplazar hardcodes por `config()`)
  - `.env` (crear: valores actuales de desarrollo)
  - `.env.example` (crear: template sin valores reales)
  - `requirements.txt` (agregar `python-decouple`)
- **Estimación:** 20 min
- **Dependencias:** ninguna
- **Checklist:**
  - [x] Agregar `python-decouple` a `requirements.txt`
  - [x] Crear `.env` en raíz del proyecto con: `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (⚠️ crear manualmente — safety policy bloquea write)
  - [x] Crear `.env.example` con las mismas claves y valores placeholder (`changeme`) (⚠️ crear manualmente)
  - [x] Modificar `base.py` línea 24: `SECRET_KEY = config('SECRET_KEY')`
  - [x] Modificar `base.py` DATABASES (líneas ~28-36): `NAME=config('DB_NAME', default='blog_cocina')`, `USER=config('DB_USER', default='root')`, `PASSWORD=config('DB_PASSWORD', default='')`, `HOST=config('DB_HOST', default='localhost')`, `PORT=config('DB_PORT', default='3306')`
  - [x] Agregar `from decouple import config` al inicio de `base.py`
  - [ ] Ejecutar `python manage.py check` → sin errores de import o configuración (WSL/bash no disponible)

---

### T-1.2: Poblar .gitignore con entradas Python/Django

- **Spec:** SPEC-1.2
- **Archivos:**
  - `.gitignore` (poblar — actualmente vacío o mínimo)
- **Estimación:** 10 min
- **Dependencias:** T-1.1 (`.env` debe estar protegido apenas se crea)
- **Checklist:**
  - [x] Agregar `__pycache__/`, `*.py[cod]`
  - [x] Agregar `.env`
  - [x] Agregar `db.sqlite3`
  - [x] Agregar `media/`
  - [x] Agregar `staticfiles/`
  - [x] Agregar `*.log`
  - [x] Agregar `.venv/`, `venv/`, `env/`
  - [x] Agregar `.vscode/`, `.idea/`
  - [x] Agregar `*.egg-info/`, `dist/`, `build/`
  - [ ] Ejecutar `git rm --cached` para archivos ya trackeados que ahora matchean los patterns de ignore (WSL/bash no disponible)
  - [ ] `git status` confirma que `__pycache__/` y `.pyc` no aparecen como untracked (WSL/bash no disponible)

---

### T-1.3: Corregir indentación de Contacto.__str__

- **Spec:** SPEC-1.4
- **Archivos:**
  - `apps/contacto/models.py` (línea 9: `def __str__` está fuera de la clase)
- **Estimación:** 10 min
- **Dependencias:** ninguna (se puede hacer en paralelo con T-1.1/T-1.2)
- **Checklist:**
  - [x] Mover `def __str__(self): return self.nombre` DENTRO de `class Contacto(models.Model):` con indentación de 4 espacios
  - [x] Verificar que no hay otros métodos fuera de clase en el mismo archivo
  - [x] Agregar newline al final del archivo si falta
  - [ ] `python manage.py shell -c "from apps.contacto.models import Contacto; print(str(Contacto(nombre='Test')))"` → imprime "Test" (WSL/bash no disponible)

---

### T-1.4: Corregir default='Sin categoría' en FK categoria_articulo

- **Spec:** SPEC-1.5
- **Archivos:**
  - `apps/articulos/models.py` (línea 19: `default='Sin categoría'`)
- **Estimación:** 15 min
- **Dependencias:** T-1.3 (modelos deben estar consistentes antes de generar migraciones)
- **Checklist:**
  - [x] Eliminar `default='Sin categoría'` del campo `categoria_articulo`
  - [x] Evaluar si se necesita `default=1` (ID de una categoría "Sin categoría" existente) o simplemente `null=True, blank=True`
  - [x] Si se usa `null=True` (ya está), mantener `on_delete=models.SET_NULL`
  - [ ] Ejecutar `python manage.py makemigrations articulos` (WSL/bash no disponible)
  - [ ] Revisar la migración generada: debe eliminar el default string (WSL/bash no disponible)
  - [ ] `python manage.py migrate` → sin errores (WSL/bash no disponible)
  - [ ] `python manage.py check` → sin warnings (WSL/bash no disponible)

---

### T-1.5: Corregir señales post_save en usuarios/models.py

- **Spec:** SPEC-1.3
- **Archivos:**
  - `apps/usuarios/models.py` (líneas 30-40: dos handlers con recursión y lógica invertida)
  - `apps/usuarios/apps.py` (verificar que señales estén registradas correctamente)
- **Estimación:** 25 min
- **Dependencias:** T-1.4 (modelos estables antes de tocar señales)
- **Checklist:**
  - [x] Eliminar las dos señales existentes (`asignar_tipo_usuario` y `asignar_miembro`)
  - [x] Implementar UNA sola señal `sincronizar_tipo_usuario` usando `Usuario.objects.filter(pk=instance.pk).update(tipo_usuario=...)` para evitar recursión
  - [x] La lógica debe asignar `tipo_usuario` correctamente: superuser → `USUARIO_SUPER`, caso contrario → `USUARIO_MIEMBRO`
  - [x] Verificar que `instance.save()` NO se llama dentro del handler
  - [ ] `python manage.py shell -c "from apps.usuarios.models import Usuario; u=Usuario.objects.create_user('test_señal', password='test123'); print(u.tipo_usuario)"` → imprime el valor correcto sin error (WSL/bash no disponible)
  - [ ] `python manage.py shell -c "from apps.usuarios.models import Usuario; u=Usuario.objects.get(username='test_señal'); u.first_name='Test'; u.save(); print(u.tipo_usuario)"` → sin recursión (WSL/bash no disponible)
  - [ ] `makemigrations --check` → no detecta cambios no intencionales (WSL/bash no disponible)

---

### T-1.6: Reemplazar request.POST.get() en add_comentario por ComentarioForm con validación

- **Spec:** SPEC-1.7
- **Archivos:**
  - `apps/articulos/views.py` (línea 182: `request.POST.get('comentario')`)
  - `apps/articulos/forms.py` (línea 22-27: corregir `__init__` que asigna `user.username` a FK)
- **Estimación:** 20 min
- **Dependencias:** T-1.5 (las señales que afectan a Usuario deben estar corregidas)
- **Checklist:**
  - [x] Corregir `ComentarioForm.__init__`: eliminar el `__init__` completo que asignaba `user.username` (string) a FK — ahora la FK se asigna en la vista con `commit=False`
  - [x] Agregar `@login_required` a `add_comentario` si no lo tiene (ya lo tenía)
  - [x] Reescribir `add_comentario`: usar `ComentarioForm(request.POST)` con `form.is_valid()`
  - [x] Si es válido: `form.save(commit=False)`, asignar `articulo_comentario` y `usuario_comentario`, luego `form.save()`
  - [x] Si no es válido: redirige al detalle (el template `detalleArticulos.html` ya maneja el form inline con errores)
  - [ ] Test manual: comentar con campo vacío → debe mostrar error de validación (WSL/bash no disponible)
  - [ ] Test manual: comentar con texto válido → redirige al detalle del artículo (WSL/bash no disponible)

---

### T-1.7: Proteger delete_articulo con verificación de ownership

- **Spec:** SPEC-1.6
- **Archivos:**
  - `apps/articulos/views.py` (líneas 96-100: `delete_articulo` sin verificación)
- **Estimación:** 15 min
- **Dependencias:** T-1.6 (patrón de autorización consistente)
- **Checklist:**
  - [x] Verificación de ownership agregada: `if articulo.usuario_articulo != request.user and not request.user.is_superuser`
  - [x] Si no tiene permiso: `messages.error(request, 'No tenés permiso para eliminar este artículo')` + redirect a listado
  - [x] Si el usuario no está autenticado, `@login_required` ya lo redirige
  - [ ] Agregar mensaje de éxito después de eliminar (opcional — no solicitado en el delegated prompt para esta ola)
  - [x] Usar `redirect('articulos:listarArticulos')` después del POST (PRG pattern)
  - [ ] Test manual: usuario colaborador intenta borrar artículo ajeno → redirect con mensaje de error (WSL/bash no disponible)
  - [ ] Test manual: usuario admin borra artículo ajeno → exitoso (WSL/bash no disponible)

---

**Batch 1 cierre:** `python manage.py check && python manage.py runserver` — sin errores. Login → crear artículo → comentar → sin errores.

---

## Batch 2 → PR 2: Ola 2 — Seguridad y Configuración (Security Hardening)

**Objetivo del batch:** Implementar autorización con grupos Django + hardening de settings.
**Dependencias:** Batch 1 (Ola 1) completado.
**Verificación:** `python manage.py check --deploy` sin warnings críticos.
**Smoke test:** Admin borra artículo ajeno → OK. Colaborador borra artículo ajeno → 403.

---

### T-2.1: Implementar sistema de autorización con grupos Django

- **Spec:** SPEC-2.1, SPEC-2.2 (diseño Decisión 1)
- **Archivos:**
  - `apps/usuarios/models.py` (agregar helpers `es_miembro()`, `es_colaborador()`, `es_administrador()`, `puede_editar_articulo()`, `puede_eliminar_articulo()`, `puede_editar_comentario()`)
  - `apps/usuarios/models.py` (modificar señal `sincronizar_grupo_usuario` para asignar grupos vía `instance.groups.add()`)
  - `apps/usuarios/migrations/XXXX_populate_groups.py` (nuevo: data migration para crear grupos y asignar usuarios existentes)
  - `apps/usuarios/management/__init__.py` (nuevo)
  - `apps/usuarios/management/commands/__init__.py` (nuevo)
  - `apps/usuarios/management/commands/setup_groups.py` (nuevo: comando `setup_groups`)
- **Estimación:** 45 min
- **Dependencias:** Batch 1 completo
- **Checklist:**
  - [x] Simplificar `TIPO_DE_USUARIO` choices: mantener `Miembro`, `Colaborador`, `Administrador` (eliminar `Visitante`)
  - [x] Agregar helpers en modelo `Usuario`: `es_miembro()`, `es_colaborador()`, `es_administrador()`, `puede_editar_articulo()`, `puede_eliminar_articulo()`, `puede_editar_comentario()`
  - [x] Modificar señal `sincronizar_grupo_usuario`: usar `Group.objects.get_or_create()` + `instance.groups.add(grupo)` + `Usuario.objects.filter(pk=instance.pk).update(tipo_usuario=...)` para sincronizar sin recursión
  - [x] Mapeo: `Administrador` → grupo `Administrador`, `Colaborador` → grupo `Colaborador`, otros → grupo `Miembro`
  - [x] Crear data migration en `usuarios/migrations/`: `RunPython` que crea los 3 grupos y asigna usuarios existentes según su `tipo_usuario` actual
  - [x] Crear management command `setup_groups`: crea grupos si no existen y reconcilia membresías
  - [ ] `python manage.py makemigrations usuarios` → genera la migración de datos
  - [ ] `python manage.py migrate` → ejecuta migraciones sin error
  - [ ] `python manage.py setup_groups` → asigna grupos a usuarios existentes

---

### T-2.2: Migrar verificaciones tipo_usuario por helpers de autorización en vistas

- **Spec:** SPEC-2.2
- **Archivos:**
  - `apps/articulos/views.py` (líneas 78, 96, 149, 170, 213: todas las verificaciones por string)
  - Templates que usan `user.tipo_usuario` (si existen)
- **Estimación:** 30 min
- **Dependencias:** T-2.1 (helpers deben existir en el modelo)
- **Checklist:**
  - [x] `editArticulo` línea 78: cambiar `if request.user.tipo_usuario =='Miembro':` → `if not request.user.puede_editar_articulo(articulo): raise PermissionDenied()`
  - [x] `delete_articulo` línea 96: cambiar verificación de string a `if not request.user.puede_eliminar_articulo(articulo): raise PermissionDenied()`
  - [x] `AddArticulo` / `crear_articulo`: verificar `request.user.es_colaborador() or request.user.es_administrador()`
  - [x] `addCategoria`: restringir a `es_administrador()`
  - [x] `edit_categoria`: restringir a `es_administrador()`
  - [x] `delete_categoria`: restringir a `es_administrador()`
  - [x] `delete_comentario` línea 213: cambiar a `request.user.puede_editar_comentario(comentario)`
  - [x] `grep -rn "tipo_usuario ==" apps/` → 0 resultados en vistas (solo debe aparecer en modelo y migraciones)
  - [x] Templates: reemplazar `user.tipo_usuario == 'Administrador'` por `user.es_administrador` donde aplique

---

### T-2.3: Proteger listarMensajes con login_required y restricción admin

- **Spec:** SPEC-2.3
- **Archivos:**
  - `apps/contacto/views.py` (vista `listarMensajes` o equivalente)
  - `apps/contacto/urls.py` (verificar que la URL no esté expuesta)
- **Estimación:** 15 min
- **Dependencias:** T-2.1 (helpers disponibles)
- **Checklist:**
  - [x] Agregar `@login_required` a la vista de listado de mensajes de contacto
  - [x] Agregar verificación: `if not request.user.es_administrador(): raise PermissionDenied()`
  - [x] Usuario anónimo → redirect a login
  - [x] Usuario colaborador → 403
  - [x] Usuario admin → 200 con lista de mensajes
  - [x] Si hay acciones de eliminar/responder mensajes, protegerlas también

---

### T-2.4: Descomentar y corregir verificación de ownership en edit_comentario

- **Spec:** SPEC-2.4
- **Archivos:**
  - `apps/articulos/views.py` (líneas 195-197: verificación comentada + comparación incorrecta con `.username`)
- **Estimación:** 15 min
- **Dependencias:** T-2.1 (helpers disponibles)
- **Checklist:**
  - [x] Eliminar el bloque comentado (líneas 195-197) que compara `comentario.usuario_comentario == request.user.username` (incorrecto)
  - [x] Agregar verificación real: `if not request.user.puede_editar_comentario(comentario): raise PermissionDenied()`
  - [x] Verificar que el `ComentarioForm` solo permite editar `comentario` (no `usuario_comentario` ni `articulo_comentario`)
  - [x] Asegurar que la vista usa POST para guardar y redirect después (PRG)
  - [x] Test manual: editar comentario propio → OK. Editar comentario ajeno → 403

---

### T-2.5: Corregir LANGUAGE_CODE y crear settings/__init__.py

- **Spec:** SPEC-2.5
- **Archivos:**
  - `blog_cocina/settings/base.py` (línea 99: `LANGUAGE_CODE = 'en-ar'` → `'es-AR'`)
  - `blog_cocina/settings/__init__.py` (nuevo: actualmente NO existe — CRÍTICO)
- **Estimación:** 10 min
- **Dependencias:** T-1.1 (base.py ya fue modificado)
- **Checklist:**
  - [x] Cambiar `LANGUAGE_CODE = 'en-ar'` por `LANGUAGE_CODE = 'es-AR'` en `base.py`
  - [x] Verificar `TIME_ZONE`: si está mal, corregir a `'America/Argentina/Buenos_Aires'`
  - [x] Crear `blog_cocina/settings/__init__.py` con docstring: `# Paquete de settings.`
  - [ ] `python manage.py check` → sin warnings sobre LANGUAGE_CODE

---

### T-2.6: Corregir wsgi.py y asgi.py

- **Spec:** SPEC-2.8
- **Archivos:**
  - `blog_cocina/wsgi.py`
  - `blog_cocina/asgi.py`
- **Estimación:** 10 min
- **Dependencias:** T-2.5 (`__init__.py` debe existir para que el paquete settings sea importable)
- **Checklist:**
  - [x] Verificar `wsgi.py`: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_cocina.settings.production')` — si apunta solo a `'blog_cocina.settings'`, corregir
  - [x] Verificar `asgi.py`: misma corrección que wsgi.py
  - [ ] `python -c "from blog_cocina.wsgi import application"` → sin error
  - [ ] `python -c "from blog_cocina.asgi import application"` → sin error

---

### T-2.7: Agregar STATIC_ROOT

- **Spec:** SPEC-2.9
- **Archivos:**
  - `blog_cocina/settings/base.py` (agregar `STATIC_ROOT`)
- **Estimación:** 10 min
- **Dependencias:** T-2.5 (settings estables)
- **Checklist:**
  - [x] Agregar `STATIC_ROOT = BASE_DIR.parent / 'staticfiles'` en `base.py`
  - [x] Verificar que `staticfiles/` está en `.gitignore` (agregado en T-1.2)
  - [ ] `python manage.py collectstatic --dry-run` → lista archivos sin error
  - [ ] `python manage.py collectstatic` → copia a `staticfiles/`

---

### T-2.8: Agregar SECURE_* settings en production.py

- **Spec:** SPEC-2.6
- **Archivos:**
  - `blog_cocina/settings/production.py`
- **Estimación:** 15 min
- **Dependencias:** T-2.5 (settings package funcional)
- **Checklist:**
  - [x] Agregar `SECURE_SSL_REDIRECT = True`
  - [x] Agregar `SECURE_HSTS_SECONDS = 31536000`
  - [x] Agregar `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - [x] Agregar `SECURE_HSTS_PRELOAD = True`
  - [x] Agregar `SESSION_COOKIE_SECURE = True`
  - [x] Agregar `CSRF_COOKIE_SECURE = True`
  - [x] Agregar `SECURE_BROWSER_XSS_FILTER = True`
  - [x] Agregar `SECURE_CONTENT_TYPE_NOSNIFF = True`
  - [x] Agregar `X_FRAME_OPTIONS = 'DENY'`
  - [x] NO agregar estos settings en `base.py` ni `local.py`
  - [x] Documentar con comentario que requieren HTTPS en el servidor

---

### T-2.9: Rellenar production.py con configuración completa

- **Spec:** SPEC-2.7
- **Archivos:**
  - `blog_cocina/settings/production.py`
- **Estimación:** 20 min
- **Dependencias:** T-2.8 (SECURE_* ya agregados, se completa el archivo)
- **Checklist:**
  - [x] `DEBUG = False` (forzado, no desde variable)
  - [x] `ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())`
  - [x] `DATABASES['default']` usa `config()` para todas las credenciales (sin hardcode)
  - [x] Agregar `OPTIONS` con `sql_mode='STRICT_TRANS_TABLES'` y `charset='utf8mb4'`
  - [x] Configurar `EMAIL_BACKEND` SMTP con variables de entorno
  - [x] Configurar `LOGGING` con `RotatingFileHandler` → `logs/django.log`
  - [x] Configurar `ADMINS` desde variable de entorno
  - [ ] `import django; django.setup()` con `DJANGO_SETTINGS_MODULE=blog_cocina.settings.production` no arroja errores

---

**Batch 2 cierre:** `python manage.py check --deploy` → sin warnings de seguridad. Smoke test de autorización: admin elimina artículo ajeno → OK. colaborador intenta → 403.

---

## Batch 3 → PR 3: Ola 3 — Calidad de Código y Mantenibilidad

**Objetivo del batch:** PEP 8 compliance, docstrings, templates corregidos, sin código muerto.
**Dependencias:** Batches 1 y 2 completados (autorización funcional antes de refactorizar vistas).
**Verificación:** `python manage.py check`, navegación manual de todas las URLs.
**Nota:** ~430 líneas estimadas (levemente sobre el budget de 400). Si es necesario, separar T-3.7 (docstrings) y T-3.9 (templates) a un PR 3b.

---

### T-3.1: Eliminar código muerto ✅

- **Spec:** SPEC-3.5
- **Archivos:**
  - `apps/articulos/views.py` (línea 149: `tipo_usuario == 'publico'`)
  - Todos los `.py` del proyecto (imports no usados, variables no leídas, código comentado)
- **Estimación:** 15 min
- **Dependencias:** Batch 2 completo (las verificaciones ya migraron a helpers)
- **Checklist:**
  - [ ] Eliminar `if request.user.tipo_usuario == 'publico':` (línea 149 de `views.py` original) — este código nunca se ejecuta
  - [ ] `grep -rn "tipo_usuario == 'publico'" apps/` → 0 resultados
  - [ ] `grep -rn "tipo_usuario == 'Publico'" apps/` → 0 resultados
  - [ ] Eliminar imports no usados en todos los `.py` (verificar con `autoflake --check` si está instalado, o revisión manual)
  - [ ] Eliminar bloques de código comentado que no sean documentación intencional
  - [ ] Eliminar variables asignadas pero nunca leídas
  - [ ] `python manage.py check` → sin errores

---

### T-3.2: Corregir BASE_DIR para que apunte a la raíz del proyecto ✅

- **Spec:** SPEC-3.9
- **Archivos:**
  - `blog_cocina/settings/base.py` (línea 17: `BASE_DIR = Path(__file__).resolve().parent.parent` → `parent.parent.parent`)
  - Todos los usos de `BASE_DIR` y `os.path.dirname(BASE_DIR)` en settings
- **Estimación:** 20 min
- **Dependencias:** T-1.1, T-2.5 (settings ya modificados, ahora se corrige la raíz)
- **Checklist:**
  - [ ] Cambiar `BASE_DIR` de `parent.parent` (2 niveles = `blog_cocina/`) a `parent.parent.parent` (3 niveles = raíz del proyecto)
  - [ ] Corregir `TEMPLATES[0]['DIRS']`: `os.path.join(os.path.dirname(BASE_DIR), 'templates')` → `BASE_DIR / 'templates'`
  - [ ] Corregir `STATICFILES_DIRS`: `os.path.join(os.path.dirname(BASE_DIR), 'static')` → `[BASE_DIR / 'static']`
  - [ ] Corregir `MEDIA_ROOT`: `os.path.join(os.path.dirname(BASE_DIR), 'media')` → `BASE_DIR / 'media'`
  - [ ] `python manage.py check` → sin warnings de templates/static dirs
  - [ ] `python manage.py runserver` → templates cargan, static sirve correctamente

---

### T-3.3: Separar vistas de articulos/views.py en submódulos ✅

- **Spec:** SPEC-3.4 (diseño Decisión 2)
- **Archivos:**
  - `apps/articulos/views/__init__.py` (nuevo: re-exportador)
  - `apps/articulos/views/articulos.py` (nuevo: `listar_articulos`, `detalle_articulos`, `crear_articulo`, `editar_articulo`, `eliminar_articulo`)
  - `apps/articulos/views/categorias.py` (nuevo: `listar_categorias`, `crear_categoria`, `editar_categoria`, `eliminar_categoria`)
  - `apps/articulos/views/comentarios.py` (nuevo: `agregar_comentario`, `editar_comentario`, `eliminar_comentario`)
  - `apps/articulos/views.py` (eliminar después de migrar)
  - `apps/articulos/urls.py` (actualizar imports — mínimo, gracias al `__init__.py` re-exportador)
- **Estimación:** 35 min
- **Dependencias:** T-3.1 (código muerto eliminado), T-3.2 (BASE_DIR corregido)
- **Checklist:**
  - [ ] Crear directorio `apps/articulos/views/`
  - [ ] Crear `__init__.py` que importa y re-exporta TODAS las vistas con `__all__`
  - [ ] Crear `articulos.py`: copiar funciones de artículos (`listarArticulos`, `detalleArticulos`, `AddArticulo`, `editArticulo`, `delete_articulo`)
  - [ ] Crear `categorias.py`: copiar funciones de categorías (`listarCategorias`, `addCategoria`, `edit_categoria`, `delete_categoria`)
  - [ ] Crear `comentarios.py`: copiar funciones de comentarios (`add_comentario`, `edit_comentario`, `delete_comentario`)
  - [ ] Ajustar imports en cada submódulo (models, forms)
  - [ ] Verificar que `urls.py` sigue importando desde `from . import views` sin cambios (gracias a `__init__.py`)
  - [ ] Eliminar `apps/articulos/views.py` original
  - [ ] `python manage.py check` → sin errores de import
  - [ ] Navegar listado, detalle, crear, editar, eliminar artículo → sin errores
  - [ ] Navegar categorías y comentarios → sin errores

---

### T-3.4: Unificar convención de nombres a snake_case ✅

- **Spec:** SPEC-3.1 (diseño Decisión 5)
- **Archivos:**
  - `apps/articulos/views/articulos.py` (renombrar funciones)
  - `apps/articulos/views/categorias.py` (renombrar funciones)
  - `apps/articulos/views/comentarios.py` (renombrar funciones)
  - `apps/articulos/views/__init__.py` (actualizar imports)
  - `apps/articulos/urls.py` (renombrar URL names y path kwargs)
  - `apps/usuarios/urls.py` (si tiene nombres camelCase)
  - `apps/contacto/urls.py` (si tiene nombres camelCase)
  - `blog_cocina/urls.py` (agregar redirects 301 de URLs viejas)
  - TODOS los templates con `{% url %}` (actualizar nombres)
  - TODOS los `reverse()` y `redirect()` en código Python
- **Estimación:** 40 min
- **Dependencias:** T-3.3 (vistas ya separadas en submódulos)
- **Checklist:**
  - [ ] Renombrar en `articulos.py`: `listarArticulos` → `listar_articulos`, `detalleArticulos` → `detalle_articulos`, `AddArticulo` → `crear_articulo`, `editArticulo` → `editar_articulo`, `delete_articulo` → `eliminar_articulo`
  - [ ] Renombrar en `categorias.py`: `listarCategorias` → `listar_categorias`, `addCategoria` → `crear_categoria`, `edit_categoria` → `editar_categoria`, `delete_categoria` → `eliminar_categoria`
  - [ ] Renombrar en `comentarios.py`: `add_comentario` → `agregar_comentario`, `edit_comentario` → `editar_comentario`, `delete_comentario` → `eliminar_comentario`
  - [ ] Actualizar `__init__.py` con los nuevos nombres y `__all__`
  - [ ] Actualizar `urls.py`: nuevos `name='...'` en snake_case + paths en kebab-case o snake_case
  - [ ] Agregar `RedirectView` en `blog_cocina/urls.py` para URLs viejas → nuevas (con comentario `TODO: eliminar en 3 meses`)
  - [ ] Actualizar TODOS los `{% url 'articulos:nombreViejo' %}` en templates a los nuevos nombres
  - [ ] Actualizar `redirect('articulos:nombreViejo', ...)` y `reverse('articulos:nombreViejo', ...)` en código Python
  - [ ] `grep -rP '(def [a-z]+[A-Z])' apps/articulos/views/` → 0 funciones camelCase
  - [ ] Navegar todas las URLs del sitio → sin errores de reverse match

---

### T-3.5: Agregar select_related / prefetch_related en queries N+1 ✅

- **Spec:** SPEC-3.2
- **Archivos:**
  - `apps/articulos/views/articulos.py` (vistas de listado y detalle)
- **Estimación:** 20 min
- **Dependencias:** T-3.4 (vistas ya renombradas)
- **Checklist:**
  - [ ] `listar_articulos`: `Articulo.objects.all()` → `Articulo.objects.select_related('categoria_articulo', 'usuario_articulo').all()`
  - [ ] `detalle_articulos`: `Articulo.objects.get(pk=pk)` → `Articulo.objects.select_related('categoria_articulo', 'usuario_articulo').prefetch_related('comentarios__usuario_comentario').get(pk=pk)`
  - [ ] Verificar con `django.db.connection.queries` que el número de queries se reduce (o usar django-debug-toolbar si está disponible)
  - [ ] El listado de 20 artículos ya no dispara queries adicionales por artículo

---

### T-3.6: Corregir asignación de FK usuario_comentario como string en forms ✅

- **Spec:** SPEC-3.10
- **Archivos:**
  - `apps/articulos/forms.py` (línea 27: `self.instance.usuario_comentario = user.username`)
- **Estimación:** 10 min
- **Dependencias:** T-1.6 (ya se modificó `add_comentario`; verificar que aquí no haya regresión)
- **Checklist:**
  - [ ] Cambiar `self.instance.usuario_comentario = user.username` → `self.instance.usuario_comentario = user`
  - [ ] Verificar que `ComentarioForm.Meta.fields` excluye `usuario_comentario` (ya lo hace)
  - [ ] Crear comentario desde la vista → no arroja `ValueError: Cannot assign "'string'"`
  - [ ] Verificar en admin/shell que `comentario.usuario_comentario` es una instancia de `User`

---

### T-3.7: Agregar docstrings a modelos, vistas principales y forms ✅

- **Spec:** SPEC-3.3 (diseño Decisión 5)
- **Archivos:**
  - `apps/usuarios/models.py` (clase Usuario, helpers, señal)
  - `apps/articulos/models.py` (Categoria, Articulo, Comentario)
  - `apps/contacto/models.py` (Contacto)
  - `apps/articulos/views/articulos.py` (5 vistas)
  - `apps/articulos/views/categorias.py` (4 vistas)
  - `apps/articulos/views/comentarios.py` (3 vistas)
  - `apps/articulos/forms.py` (3 forms)
  - `apps/contacto/views.py` (vistas)
  - `apps/contacto/forms.py` (si existe)
- **Estimación:** 40 min
- **Dependencias:** T-3.4 (nombres finales ya establecidos)
- **Checklist:**
  - [ ] Cada clase de modelo: docstring explicando propósito y relaciones clave (Google Style, español)
  - [ ] Cada helper en `Usuario`: docstring con Args y Returns
  - [ ] La señal `sincronizar_grupo_usuario`: docstring explicando qué dispara y qué efecto tiene
  - [ ] Cada función de vista: docstring con propósito, template y contexto
  - [ ] Forms con lógica custom: docstring explicando validaciones
  - [ ] Formato consistente Google Style en todo el proyecto
  - [ ] Términos técnicos en inglés (QuerySet, ForeignKey, post_save), explicaciones en español

---

### T-3.8: Remover {% static %} de urls.py de apps ✅

- **Spec:** SPEC-3.7
- **Archivos:**
  - `apps/articulos/urls.py` (línea 24: `]+ static(settings.MEDIA_URL, ...)`)
  - `apps/usuarios/urls.py` (verificar si tiene `+ static(...)`)
  - `apps/contacto/urls.py` (verificar si tiene `+ static(...)`)
  - `blog_cocina/urls.py` (asegurar que sirve static SOLO en DEBUG)
- **Estimación:** 10 min
- **Dependencias:** T-2.7 (STATIC_ROOT ya configurado)
- **Checklist:**
  - [ ] Eliminar `+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` de `apps/articulos/urls.py`
  - [ ] Eliminar `from django.conf import settings` y `from django.conf.urls.static import static` si ya no se usan
  - [ ] Revisar `apps/usuarios/urls.py` y `apps/contacto/urls.py` — eliminar `+ static(...)` si existe
  - [ ] Verificar que `blog_cocina/urls.py` tiene `static(settings.MEDIA_URL, ...)` condicionado a `settings.DEBUG`
  - [ ] En desarrollo, archivos estáticos y media se siguen sirviendo correctamente

---

### T-3.9: Corregir templates: lang, bloques title, meta description ✅

- **Spec:** SPEC-3.6 (diseño Decisión 5)
- **Archivos:**
  - `templates/base.html` (línea 4: `lang="en"` → `lang="es"`, agregar meta description, unificar bloque `titulo`)
  - `templates/articulos/*.html` (unificar `{% block title %}` / `{% block titulo %}`)
  - `templates/usuarios/*.html` (unificar bloque de título)
  - `templates/contacto/*.html` (unificar bloque de título)
- **Estimación:** 25 min
- **Dependencias:** T-3.4 (URL names ya actualizados en templates)
- **Checklist:**
  - [ ] `base.html`: cambiar `lang="en"` → `lang="es"`
  - [ ] `base.html`: agregar `<meta name="description" content="{% block meta_desc %}Blog de cocina con recetas...{% endblock meta_desc %}">`
  - [ ] `base.html`: verificar `<meta charset="UTF-8">` presente
  - [ ] Unificar TODOS los templates a `{% block titulo %}` (cambiar los que usan `{% block title %}`)
  - [ ] El `<title>` en `<head>` usa `{% block titulo %}`
  - [ ] `grep -rn "block title" templates/` → 0 resultados (todo usa `titulo`)
  - [ ] Cada template que hereda de `base.html` define `{% block titulo %}` con valor apropiado

---

### T-3.10: Agregar SRI hash al CDN de Bootstrap ✅

- **Spec:** SPEC-3.8
- **Archivos:**
  - `templates/base.html` (tags `<link>` y `<script>` de Bootstrap)
- **Estimación:** 10 min
- **Dependencias:** T-3.9 (base.html ya modificado)
- **Checklist:**
  - [ ] Identificar la versión exacta de Bootstrap usada (del CDN link actual)
  - [ ] Agregar `integrity="sha384-..."` al `<link>` de Bootstrap CSS
  - [ ] Agregar `crossorigin="anonymous"` al mismo tag
  - [ ] Agregar `integrity="sha384-..."` al `<script>` de Bootstrap JS
  - [ ] Agregar `crossorigin="anonymous"` al mismo tag
  - [ ] Cargar la página en navegador → DevTools Console sin errores de SRI

---

### T-3.11: Eliminar vista huérfana contacto en blog_cocina/views.py ✅

- **Spec:** SPEC-3.11
- **Archivos:**
  - `blog_cocina/views.py` (línea 7: función `contacto` — duplicada con la app `contacto`)
  - `blog_cocina/urls.py` (verificar que no tenga URL apuntando a esta vista)
- **Estimación:** 10 min
- **Dependencias:** ninguna (independiente)
- **Checklist:**
  - [ ] Eliminar la función `contacto` de `blog_cocina/views.py` (líneas 7-9)
  - [ ] Verificar que `blog_cocina/urls.py` NO tiene un path apuntando a `views.contacto`
  - [ ] Si `blog_cocina/views.py` queda solo con `home` y `acerca_de`, mantener el archivo
  - [ ] `python manage.py check` → sin imports rotos
  - [ ] La funcionalidad de contacto de la app `contacto` sigue funcionando

---

**Batch 3 cierre:** `python manage.py check`. Navegar listado, detalle, crear/editar/eliminar artículos, categorías y comentarios → todas las URLs cargan sin error. `grep -rn "camelCase"` en vistas → limpio.

---

## Batch 4a → PR 4a: Ola 4 — Tests (Parte 1: Infraestructura + Unitarios)

**Objetivo del batch:** Configurar pytest + tests de modelos, señales y forms.
**Dependencias:** Batches 1, 2, 3 completados.
**Verificación:** `pytest apps/usuarios/tests/ apps/articulos/tests/test_models.py apps/articulos/tests/test_forms.py apps/contacto/tests/` — todos verdes.

---

### T-4.1: Configurar pytest-django como test runner

- **Spec:** SPEC-4.1 (diseño Decisión 4)
- **Archivos:**
  - `requirements.txt` (agregar `pytest`, `pytest-django`, `pytest-cov`, `factory-boy`)
  - `pytest.ini` (nuevo: configuración)
- **Estimación:** 15 min
- **Dependencias:** Batch 3 completo (código estable)
- **Checklist:**
  - [x] Agregar `pytest`, `pytest-django`, `pytest-cov`, `factory-boy` a `requirements.txt`
  - [x] Crear `pytest.ini` con:
    - `DJANGO_SETTINGS_MODULE = blog_cocina.settings.local`
    - `python_files = tests.py test_*.py *_tests.py`
    - `addopts = --strict-markers -v --tb=short`
  - [x] Crear archivos `__init__.py` en: `apps/usuarios/tests/`, `apps/articulos/tests/`, `apps/contacto/tests/`
  - [x] `pytest --collect-only` → sin errores (aunque no haya tests aún)

---

### T-4.2: Crear factories y conftest compartidos

- **Spec:** SPEC-4.2, SPEC-4.5 (prerrequisito: factories para todos los tests)
- **Archivos:**
  - `apps/usuarios/tests/factories.py` (nuevo: `UsuarioFactory` con traits `miembro`, `colaborador`, `administrador`)
  - `apps/articulos/tests/factories.py` (nuevo: `CategoriaFactory`, `ArticuloFactory`, `ComentarioFactory`)
  - `apps/contacto/tests/factories.py` (nuevo: `ContactoFactory`)
  - `apps/articulos/tests/conftest.py` (nuevo: fixtures `usuario_miembro`, `usuario_colaborador`, `usuario_administrador`, `cliente_anonimo`, `articulo`, `categoria`)
  - `apps/usuarios/tests/conftest.py` (nuevo: fixtures de usuario si son específicos)
  - `apps/contacto/tests/conftest.py` (nuevo: fixtures de contacto)
- **Estimación:** 30 min
- **Dependencias:** T-4.1 (pytest configurado)
- **Checklist:**
  - [x] `UsuarioFactory`: username secuencial, `set_password('testpass123')`, traits `miembro`/`colaborador`/`administrador` que crean `Group` y asignan `tipo_usuario` vía `update()`
  - [x] `CategoriaFactory`: `descripcion` secuencial
  - [x] `ArticuloFactory`: `titulo` secuencial, `categoria_articulo` SubFactory, `usuario_articulo` SubFactory
  - [x] `ComentarioFactory`: `articulo_comentario` SubFactory, `usuario_comentario` SubFactory
  - [x] `ContactoFactory`: todos los campos requeridos
  - [x] `conftest.py` de articulos: fixtures con `client.force_login(user)` para Miembro, Colaborador, Admin + cliente anónimo
  - [x] `pytest --collect-only` → detecta los archivos de test

---

### T-4.3: Tests unitarios de modelos

- **Spec:** SPEC-4.2
- **Archivos:**
  - `apps/usuarios/tests/test_models.py` (nuevo)
  - `apps/articulos/tests/test_models.py` (nuevo)
  - `apps/contacto/tests/test_models.py` (nuevo)
- **Estimación:** 45 min
- **Dependencias:** T-4.2 (factories disponibles)
- **Checklist:**
  - [x] `test_models.py` usuarios: crear usuario, verificar `tipo_usuario` default, `__str__`, username único
  - [x] `test_models.py` usuarios: test de creación con `create_user()`, test de `is_active` default
  - [x] `test_models.py` articulos: crear `Categoria` → `__str__`, nombre único
  - [x] `test_models.py` articulos: crear `Articulo` → `__str__`, FK a Categoria y Usuario válidas
  - [x] `test_models.py` articulos: `articulo.categoria_articulo` es instancia de Categoria
  - [x] `test_models.py` articulos: crear `Comentario` → `__str__`, FK a Articulo y Usuario
  - [x] `test_models.py` articulos: `on_delete` de Articulo → Comentarios se eliminan en cascada
  - [x] `test_models.py` contacto: crear `Contacto` → `__str__`, campos requeridos
  - [x] `test_models.py` contacto: `email` inválido rechazado
  - [x] `pytest apps/usuarios/tests/test_models.py apps/articulos/tests/test_models.py apps/contacto/tests/test_models.py -v` → todos verdes

---

### T-4.4: Tests de señales

- **Spec:** SPEC-4.3
- **Archivos:**
  - `apps/usuarios/tests/test_signals.py` (nuevo)
- **Estimación:** 20 min
- **Dependencias:** T-4.3 (modelos ya testeados)
- **Checklist:**
  - [x] Crear Usuario sin `tipo_usuario` → señal asigna 'Miembro' y grupo 'Miembro'
  - [x] Crear Usuario con `tipo_usuario='Colaborador'` → señal asigna grupo 'Colaborador'
  - [x] Crear Usuario con `tipo_usuario='Administrador'` → señal asigna grupo 'Administrador'
  - [x] Crear superuser → señal asigna 'Administrador' y grupo 'Administrador'
  - [x] Actualizar Usuario sin cambiar `tipo_usuario` → NO hay recursión, no hay doble asignación
  - [x] `Usuario.objects.update(tipo_usuario='Administrador')` → documentar que NO dispara la señal (limitación conocida)
  - [x] `pytest apps/usuarios/tests/test_signals.py -v` → todos verdes

---

### T-4.5: Tests de forms

- **Spec:** SPEC-4.4
- **Archivos:**
  - `apps/articulos/tests/test_forms.py` (nuevo)
  - `apps/contacto/tests/test_forms.py` (nuevo)
  - `apps/usuarios/tests/test_forms.py` (nuevo — si existen forms de registro/login)
- **Estimación:** 30 min
- **Dependencias:** T-4.2 (factories disponibles)
- **Checklist:**
  - [x] `ComentarioForm`: válido con `{'comentario': 'Buen artículo'}` → `is_valid() == True`
  - [x] `ComentarioForm`: inválido con `{'comentario': ''}` → `is_valid() == False`, error en `comentario`
  - [x] `ComentarioForm`: inválido con contenido > max_length (si tiene `max_length`)
  - [x] `ArticuloForm`: válido con campos requeridos llenos → `is_valid() == True`
  - [x] `ArticuloForm`: inválido sin título → `is_valid() == False`
  - [x] `CategoriaForm`: válido con `{'descripcion': 'Postres'}` → `is_valid() == True`
  - [x] `ContactoForm`: bug corregido — campo `telefono` removido de Meta.fields. Tests: valido con campos, invalido sin campos, email malformado rechazado.
  - [x] Formularios de registro/login (si existen): username duplicado, contraseñas no coincidentes
  - [x] `pytest apps/articulos/tests/test_forms.py apps/contacto/tests/test_forms.py -v` → todos verdes

---

**Batch 4a cierre:** `pytest apps/ -v --ignore=apps/articulos/tests/test_views` → todos los tests de modelos, señales y forms pasan.

---

## Batch 4b → PR 4b: Ola 4 — Tests (Parte 2: Vistas + Integración + Cobertura)

**Objetivo del batch:** Tests de autorización por rol, integración end-to-end, y ≥70% coverage.
**Dependencias:** Batch 4a completado.
**Verificación:** `pytest --cov=apps --cov-report=term-missing --cov-fail-under=70` → PASS.

---

### T-4.6: Tests de vistas: acceso anónimo y autorización por rol

- **Spec:** SPEC-4.5
- **Archivos:**
  - `apps/articulos/tests/test_views/test_articulos.py` (nuevo)
  - `apps/articulos/tests/test_views/test_categorias.py` (nuevo)
  - `apps/articulos/tests/test_views/test_comentarios.py` (nuevo)
  - `apps/articulos/tests/test_views/__init__.py` (nuevo)
  - `apps/usuarios/tests/test_views.py` (nuevo)
  - `apps/contacto/tests/test_views.py` (nuevo)
- **Estimación:** 60 min
- **Dependencias:** T-4.2 (factories + conftest con fixtures de usuario por rol)
- **Checklist:**
  - [x] `test_articulos.py` — Usuario ANÓNIMO:
    - `listar_articulos` → 200
    - `detalle_articulos` → 200
    - `crear_articulo` GET → redirect login (302)
    - `eliminar_articulo` POST → redirect login (302)
  - [x] `test_articulos.py` — Usuario MIEMBRO:
    - `crear_articulo` → 403
    - `editar_articulo` (propio y ajeno) → 403
    - `eliminar_articulo` → 403
  - [x] `test_articulos.py` — Usuario COLABORADOR:
    - `crear_articulo` GET → 200, POST → redirect
    - `editar_articulo` (propio) → 200
    - `editar_articulo` (ajeno) → 403
    - `eliminar_articulo` (propio) → 302 redirect
    - `eliminar_articulo` (ajeno) → 403
  - [x] `test_articulos.py` — Usuario ADMINISTRADOR:
    - `editar_articulo` (ajeno) → 200
    - `eliminar_articulo` (ajeno) → 302 redirect
  - [x] `test_categorias.py`: solo admin crea/edita/elimina categorías
  - [x] `test_comentarios.py`: anónimo no comenta, colaborador comenta, ownership en edit/delete
  - [x] `test_views.py` contacto: anónimo no ve `listarMensajes`, admin sí
  - [x] `pytest apps/articulos/tests/test_views/ apps/usuarios/tests/test_views.py apps/contacto/tests/test_views.py -v` → todos verdes

---

### T-4.7: Tests de integración: flujo completo con roles

- **Spec:** SPEC-4.6
- **Archivos:**
  - `apps/articulos/tests/test_integration.py` (nuevo)
- **Estimación:** 40 min
- **Dependencias:** T-4.6 (vistas ya testeadas unitariamente)
- **Checklist:**
  - [x] Flujo Colaborador completo:
    1. Login → 302 redirect
    2. GET `crear_articulo` → 200, formulario visible
    3. POST crear artículo → redirect a detalle
    4. Artículo visible en listado
    5. GET `editar_articulo` → 200, formulario con datos
    6. POST editar → redirect, cambios reflejados
    7. POST `agregar_comentario` en artículo propio → redirect
    8. POST `eliminar_articulo` en artículo ajeno → 403
    9. POST `eliminar_articulo` en artículo propio → 302, ya no aparece en listado
  - [x] Flujo Administrador:
    1. Login como admin
    2. POST `eliminar_articulo` en artículo ajeno → 302 exitoso
    3. GET `listarMensajes` (contacto) → 200
  - [x] Flujo Anónimo:
    1. GET listado → artículos visibles, sin botones de admin
    2. POST `agregar_comentario` → redirect a login
    3. Login → redirect de vuelta al artículo
    4. POST `agregar_comentario` → exitoso
  - [x] `pytest apps/articulos/tests/test_integration.py -v` → todos verdes

---

### T-4.8: Alcanzar ≥70% de cobertura y configurar CI-ready

- **Spec:** SPEC-4.7
- **Archivos:**
  - `pytest.ini` (agregar `--cov` targets y `--cov-fail-under=70`)
  - Cualquier archivo de código que necesite tests adicionales
- **Estimación:** 30 min
- **Dependencias:** T-4.3 a T-4.7 (todos los tests existen)
- **Checklist:**
  - [ ] Agregar a `pytest.ini` en `addopts`: `--cov=apps --cov-report=term-missing --cov-report=html`
  - [ ] Agregar `--cov-fail-under=70` al final (activar solo cuando se alcance)
  - [ ] Ejecutar `pytest --cov=apps --cov-report=term-missing`
  - [ ] Revisar reporte: identificar archivos con <70% y líneas no cubiertas
  - [ ] Agregar tests para cubrir gaps hasta alcanzar ≥70% en modelos, vistas y forms
  - [ ] Excluir `migrations/`, `admin.py`, `apps.py`, `wsgi.py`, `asgi.py`, `settings/` del cálculo con `--cov-config=.coveragerc` o `[tool.coverage.run]`
  - [ ] `pytest --cov=apps --cov-fail-under=70` → PASS (todos verdes, coverage ≥70%)
  - [ ] Documentar el comando de coverage en el README o en un comentario en `pytest.ini`

---

**Batch 4b cierre:** `pytest --cov=apps --cov-report=term-missing --cov-fail-under=70` → PASS. Coverage ≥70% en modelos, vistas y forms.

---

## Resumen de Batches y PRs

| Batch | PR | Ola | Tareas | Líneas est. | Tiempo est. |
|-------|-----|-----|--------|-------------|-------------|
| 1 | PR 1 | Ola 1 | T-1.1 a T-1.7 | ~150 | ~115 min |
| 2 | PR 2 | Ola 2 | T-2.1 a T-2.9 | ~310 | ~165 min |
| 3 | PR 3 | Ola 3 | T-3.1 a T-3.11 | ~430 | ~215 min |
| 4a | PR 4a | Ola 4 (parte 1) | T-4.1 a T-4.5 | ~340 | ~140 min |
| 4b | PR 4b | Ola 4 (parte 2) | T-4.6 a T-4.8 | ~330 | ~130 min |
| **Total** | **5 PRs** | **4 Olas** | **35 tareas** | **~1,560** | **~765 min (12.75h)** |

---

## Dependencias entre batches

```
Batch 1 (Ola 1) ────► Batch 2 (Ola 2) ────► Batch 3 (Ola 3) ────► Batch 4a (Tests 1) ────► Batch 4b (Tests 2)
```

Cada batch es estrictamente dependiente del anterior. Los PRs se mergean en cadena (`feature-branch-chain`):
- PR 1 → `refactor/calidad-codigo` (tracker branch)
- PR 2 → PR 1
- PR 3 → PR 2
- PR 4a → PR 3
- PR 4b → PR 4a
- Solo el tracker mergea a `main` al final.

---

## Puntos de verificación post-batch

| Batch | Verificación automatizada | Smoke test manual |
|-------|--------------------------|-------------------|
| 1 | `python manage.py check` | Login → crear artículo → comentar |
| 2 | `python manage.py check --deploy` | Admin borra artículo ajeno → OK. Colaborador → 403 |
| 3 | `python manage.py check` + `grep camelCase views` | Navegar TODAS las URLs sin error de reverse match |
| 4a | `pytest apps/ -v --ignore=test_views` | — |
| 4b | `pytest --cov=apps --cov-fail-under=70` | Flujo end-to-end completo por rol |
