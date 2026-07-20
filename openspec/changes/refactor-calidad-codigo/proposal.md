# Proposal: Refactor Integral de Calidad de Código y Seguridad

**Change ID:** `refactor-calidad-codigo`
**Status:** Draft
**Date:** 2026-07-12
**Author:** SDD Orchestrator (basado en exploración previa)

---

## 1. Problem Statement

El proyecto "Blog de Cocina" fue desarrollado como trabajo final del curso "El Informatorio" y opera como un blog de recetas interactivo con tres roles de usuario. Sin embargo, el código presenta vulnerabilidades de seguridad graves, bugs funcionales que impiden su correcta operación, y deudas técnicas que lo hacen inadecuado como proyecto portfolio profesional o como base para un despliegue productivo.

La exploración del código reveló **7 hallazgos críticos** (que rompen funcionalidad o exponen datos sensibles) y más de **12 hallazgos altos** (que degradan seguridad, mantenibilidad o performance). El proyecto tiene 0% de cobertura de tests y carece de las protecciones básicas esperadas en una aplicación Django profesional.

**Dolor concreto:** el proyecto no es seguro para desplegar, tiene bugs que rompen features existentes (ej. recursión infinita en señales), y su código no refleja el nivel de un desarrollador listo para producción.

---

## 2. Target Users & Situations

- **Desarrollador (dueño del portfolio):** necesita que el proyecto refleje competencia profesional ante empleadores/clientes. El código actual transmite lo contrario.
- **Usuario final del blog:** actualmente expuesto a riesgos de seguridad (cualquier usuario logueado puede borrar artículos ajenos, formularios sin validación, credenciales expuestas).
- **Futuro colaborador:** heredaría una codebase sin docstrings, con convenciones inconsistentes y sin tests.

---

## 3. Current-State Gap Summary

| Área | Estado actual | Estado deseado |
|------|--------------|----------------|
| Secretos | `SECRET_KEY` y credenciales DB hardcodeadas | Variables de entorno, `.env` excluido de git |
| Modelos | `__str__` fuera de clase, `default` inválido en FK | Modelos correctos, migraciones limpias |
| Señales | Recursión infinita + lógica invertida | Señales corregidas sin `save()` recursivo |
| Autorización | String-based (`tipo_usuario == 'Miembro'`), bypasses | Permisos robustos (Django groups/permissions o decoradores custom con verificación real) |
| Formularios | `request.POST.get()` directo sin validación en comentarios | Uso correcto de Django Forms con validación |
| Tests | 0% cobertura, imports boilerplate | Cobertura significativa en capas críticas |
| Settings | `LANGUAGE_CODE` inválido, sin `SECURE_*`, `wsgi.py`/`asgi.py` rotos | Settings correctos, producción preparada |
| Templates | `lang="en"` con contenido español, bloques inconsistentes | Templates semánticamente correctos |
| Git hygiene | `.gitignore` vacío | `.gitignore` completo (pycache, .env, media, db) |

---

## 4. Scope

### 4.1 IN SCOPE

1. **Seguridad de secretos:** migración de `SECRET_KEY` y credenciales DB a variables de entorno con `python-decouple` o `python-dotenv`
2. **Corrección de bugs críticos:** señales con recursión infinita, `__str__` fuera de clase, `default='Sin categoría'` en FK
3. **Autorización:** reemplazo de verificaciones por `tipo_usuario` string con un sistema robusto (groups + permisos Django), protegiendo vistas de edición, eliminación y listados administrativos
4. **Validación de formularios:** `add_comentario` debe usar `ComentarioForm` con validación completa
5. **Configuración de settings:** corrección de `LANGUAGE_CODE`, agregado de `SECURE_*` settings, `STATIC_ROOT`, `wsgi.py`/`asgi.py`, relleno de `production.py`
6. **`.gitignore`:** cobertura completa de artefactos Python/Django
7. **N+1 queries:** `select_related`/`prefetch_related` en listados y vistas de detalle
8. **Convenciones de nombres:** unificación a snake_case (PEP 8) en funciones, vistas, URLs
9. **Docstrings:** cobertura en modelos, vistas principales y forms
10. **Código muerto:** eliminación de referencias a `tipo_usuario == 'publico'` y código comentado que no aporta
11. **Template fixes:** `lang="es"`, bloques `title` vs `titulo` consistentes, `meta description`
12. **Tests:** tests unitarios para modelos, forms, vistas críticas y señales; tests de integración para flujos de autorización

### 4.2 OUT OF SCOPE (Non-Goals)

- Nuevas features funcionales (ej. sistema de likes, favoritos, búsqueda avanzada)
- Rediseño visual o cambio de framework CSS
- Migración de MySQL a PostgreSQL/SQLite
- Internacionalización completa (i18n) multi-idioma
- Implementación de CI/CD pipelines
- Containerización (Docker)
- API REST / GraphQL
- Refactor completo de frontend (solo correcciones de accesibilidad y markup semántico)
- Cambio de `AbstractUser` a otro modelo de autenticación
- Migración del custom user model a un sistema completamente nuevo

---

## 5. Implementation Slices (Olas)

### Ola 1 — Parche de Emergencia (Critical Fixes)
**Prioridad:** CRÍTICA. Esto arregla bugs que rompen la app y filtraciones de datos.

| # | Tarea | Severidad |
|---|-------|-----------|
| 1.1 | Extraer `SECRET_KEY` y credenciales DB a `.env` + `python-decouple` | CRÍTICA |
| 1.2 | Poblar `.gitignore` con `__pycache__/`, `.env`, `db.sqlite3`, `media/`, `*.pyc` | CRÍTICA |
| 1.3 | Corregir señales `post_save` en `usuarios/models.py`: eliminar `instance.save()` y lógica invertida | CRÍTICA |
| 1.4 | Corregir indentación de `Contacto.__str__` en `contacto/models.py` | CRÍTICA |
| 1.5 | Corregir `default='Sin categoría'` en FK `categoria_articulo` | CRÍTICA |
| 1.6 | Proteger `delete_articulo`: verificar ownership o staff antes de eliminar | CRÍTICA |
| 1.7 | Reemplazar `request.POST.get()` en `add_comentario` por `ComentarioForm` con validación | CRÍTICA |

**Esfuerzo estimado:** 2-3 horas

---

### Ola 2 — Seguridad y Configuración (Security Hardening)
**Prioridad:** ALTA. Sin esto, la app no es segura para producción.

| # | Tarea | Severidad |
|---|-------|-----------|
| 2.1 | Implementar sistema de autorización con grupos Django (`Colaborador`, `Administrador`) y `UserPassesTestMixin` | ALTA |
| 2.2 | Migrar verificaciones `tipo_usuario == 'Miembro'` por checks de permisos reales | ALTA |
| 2.3 | Proteger `listarMensajes` con `@login_required` y restricción de staff | ALTA |
| 2.4 | Descomentar y corregir verificación de ownership en `edit_comentario` | ALTA |
| 2.5 | Corregir `LANGUAGE_CODE = 'es-AR'` | ALTA |
| 2.6 | Agregar `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` en `production.py` | ALTA |
| 2.7 | Rellenar `production.py` con configuración real para deploy | ALTA |
| 2.8 | Corregir `wsgi.py` y `asgi.py`: apuntar a `blog_cocina.settings` (package) | ALTA |
| 2.9 | Agregar `STATIC_ROOT` para collectstatic | ALTA |

**Esfuerzo estimado:** 3-4 horas

---

### Ola 3 — Calidad de Código y Mantenibilidad
**Prioridad:** MEDIA. Mejora la impresión del portfolio y la mantenibilidad a largo plazo.

| # | Tarea | Severidad |
|---|-------|-----------|
| 3.1 | Unificar convención de nombres a snake_case en vistas, URLs y funciones | MEDIA |
| 3.2 | Agregar `select_related`/`prefetch_related` en queries N+1 (listado de artículos, detalle con comentarios) | MEDIA |
| 3.3 | Agregar docstrings a modelos, vistas principales y forms | MEDIA |
| 3.4 | Separar vistas de `articulos/views.py` en submódulos (`articulos/`, `categorias/`, `comentarios/`) | MEDIA |
| 3.5 | Eliminar código muerto: `tipo_usuario == 'publico'`, imports no usados | MEDIA |
| 3.6 | Corregir templates: `lang="es"`, bloques `title` vs `titulo`, agregar `meta description` | MEDIA |
| 3.7 | Remover `{% static %}` de `urls.py` de apps (solo en URLconf raíz) | MEDIA |
| 3.8 | Agregar SRI hash al CDN de Bootstrap | MEDIA |
| 3.9 | Corregir `BASE_DIR` para que apunte a raíz del proyecto | MEDIA |
| 3.10 | Corregir asignación de FK `usuario_comentario` como string en forms | MEDIA |
| 3.11 | Eliminar vista huérfana `contacto` en `blog_cocina/views.py` | MEDIA |

**Esfuerzo estimado:** 4-5 horas

---

### Ola 4 — Cobertura de Tests
**Prioridad:** ALTA para portfolio. Sin tests, el refactor anterior no tiene red de seguridad.

| # | Tarea | Severidad |
|---|-------|-----------|
| 4.1 | Configurar `pytest-django` como test runner | ALTA |
| 4.2 | Tests unitarios de modelos: `Usuario`, `Articulo`, `Categoria`, `Comentario`, `Contacto` | ALTA |
| 4.3 | Tests de señales: verificar asignación correcta de `tipo_usuario` | ALTA |
| 4.4 | Tests de forms: validación, edge cases | ALTA |
| 4.5 | Tests de vistas: acceso anónimo, autorización por rol, métodos HTTP | ALTA |
| 4.6 | Tests de integración: flujo completo crear artículo → comentar → editar → eliminar con roles | ALTA |
| 4.7 | Alcanzar ≥70% de cobertura en modelos, vistas y forms | ALTA |

**Esfuerzo estimado:** 5-7 horas

---

## 6. Success Criteria (Outcome esperado)

Al completar las 4 olas, el proyecto debe cumplir:

| Métrica | Estado inicial | Meta |
|---------|---------------|------|
| Vulnerabilidades de exposición de secretos | 2 (hardcodeadas) | 0 |
| Bugs que rompen funcionalidad (recursión, modelos rotos) | 4 | 0 |
| Endpoints sin protección de autorización | 4 | 0 |
| Convención de nombres PEP 8 | ~40% | 100% |
| Docstrings en módulos clave | 0% | ≥80% |
| Cobertura de tests | 0% | ≥70% |
| N+1 queries en vistas principales | 2+ | 0 |
| `.gitignore` protege artefactos sensibles | No | Sí |
| `production.py` listo para deploy | No | Sí |
| Templates semánticamente correctos (lang, meta) | No | Sí |

---

## 7. Risks & Mitigations

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Cambio de `tipo_usuario` CharField → grupos Django rompe datos existentes | Media | Alto | Crear migración de datos que mapee valores actuales a grupos; ejecutar Ola 2 con backup de DB |
| Renombrar vistas/URLs rompe bookmarks y referencias en templates | Media | Medio | Mantener compatibilidad con redirects 301 donde sea necesario; grep exhaustivo de referencias |
| Agregar autorización rompe flujos existentes para usuarios legítimos | Baja | Alto | Tests de integración en Ola 4 cubren todos los roles; test manual de cada flujo post-Ola 2 |
| Refactor de settings (production.py) causa comportamiento inesperado en staging | Media | Medio | Probar con `DJANGO_SETTINGS_MODULE=blog_cocina.settings.production` localmente antes de deploy |
| Migraciones pendientes o conflictos al corregir modelos | Baja | Medio | Generar migraciones con `makemigrations` después de cada fix; revisar diff |
| Sin tests antes del refactor → regresiones no detectadas | Alta | Alto | **Hacer Ola 4 en paralelo incremental**: escribir tests de caracterización ANTES de tocar cada módulo cuando sea posible. Esto mitiga pero no elimina el riesgo; priorizar tests de señales y autorización en la primera iteración |

---

## 8. Dependencies Between Slices

```
Ola 1 (Critical Fixes) ───── no tiene dependencias, se puede empezar ya
        │
        ▼
Ola 2 (Security Hardening) ─ depende de Ola 1 (necesita modelos corregidos y .env)
        │
        ▼
Ola 3 (Code Quality) ─────── depende de Ola 1 y Ola 2 (necesita autorización correcta para refactorizar vistas)
        │
        ▼
Ola 4 (Tests) ────────────── idealmente en paralelo con Ola 1-3, pero el test final de integración requiere Ola 2 completa
```

**Estrategia:** La Ola 1 es independiente. Las Olas 2 y 3 pueden overlap parcialmente. La Ola 4 (tests) debe empezar lo antes posible con tests de caracterización, y completarse después de Ola 3 para validar el refactor completo.

---

## 9. Total Effort Estimate

| Ola | Horas estimadas |
|-----|----------------|
| Ola 1 — Parche de Emergencia | 2-3h |
| Ola 2 — Seguridad y Configuración | 3-4h |
| Ola 3 — Calidad de Código | 4-5h |
| Ola 4 — Tests | 5-7h |
| **Total** | **14-19h** |

---

## 10. Rollback Strategy

Cada ola se implementa en commits atómicos. Si una ola introduce regresiones:

1. **Pre-ola:** crear branch `refactor/calidad-codigo` desde `main` y branch `refactor/ola-N` por cada ola
2. **Durante:** commits pequeños con mensajes descriptivos (Conventional Commits: `fix:`, `refactor:`, `security:`, `test:`)
3. **Rollback:** revertir el merge del branch de la ola problemática. Las olas son autocontenidas: revertir Ola 2 no deshace los fixes de Ola 1
4. **Validación post-ola:** checklist de smoke test manual (login, crear artículo, comentar, borrar como admin, ver categorías) antes de mergear a main

---

## 11. Open Questions (para resolver antes de empezar)

1. **¿Hay datos reales en la DB que deban preservarse?** La migración de `tipo_usuario` → grupos requiere saber si los usuarios actuales son datos de prueba o datos reales.
2. **¿Hay un deploy existente o planificado?** Esto determina qué tan agresivas deben ser las configuraciones de `production.py` y si se necesita un staging environment.
3. **¿El portfolio será evaluado con el código fuente o con una demo viva?** Si es código fuente, la calidad del código y tests pesan más. Si es demo viva, la seguridad y los bugs visibles son prioridad.
4. **¿Hay preferencia por `pytest-django` o el unittest runner built-in de Django?** La propuesta asume pytest por ser estándar de industria, pero si el curso usó unittest, puede ser más familiar.
5. **¿El `AUTH_USER_MODEL` custom se mantiene o se quiere migrar al sistema nativo de grupos/permisos?** La Ola 2 propone usar grupos de Django sobre el modelo actual; no se migra el modelo.

---

## 12. Next Steps

1. **Responder open questions** (Sección 11)
2. **Aprobar/revisar slices y prioridades** → ajustar si es necesario
3. **Iniciar Ola 1** con el primer batch de fixes críticos
4. **Paralelamente, comenzar tests de caracterización** para tener red antes de refactors más invasivos
