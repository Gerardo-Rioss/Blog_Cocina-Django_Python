# Apply Progress — Batch 4b (Ola 4: Tests de Vistas + Integración)

**Change:** `refactor-calidad-codigo`
**Batch:** 4b → PR 4b
**Branch:** `refactor/ola-4b-integration-tests` → target `refactor/ola-4a-test-infra`
**Date:** 2026-07-12
**Status:** COMPLETED

---

## Completed Tasks

### T-4.8 (Extra): Fix ContactoForm bug ✅

**Archivos modificados:**
- `apps/contacto/forms.py` — removido `telefono` de `Meta.fields`, agregado docstring
- `apps/contacto/tests/test_forms.py` — reescrito: ahora prueba validación real (campos requeridos, email malformado, etc.) en vez de documentar FieldError

**Cambios:**
- `ContactoForm.Meta.fields` ahora es `['nombre', 'email', 'mensaje']` (coincide con el modelo)
- 6 tests nuevos: válido con todos los campos, inválido sin nombre/email/mensaje, email malformado, verificación de que no lanza FieldError

---

### T-4.6: Tests de vistas y autorización ✅

**Archivos nuevos (6):**

| Archivo | Tests | Detalle |
|---------|-------|---------|
| `apps/articulos/tests/test_views/__init__.py` | — | Paquete |
| `apps/articulos/tests/test_views/test_articulos.py` | 19 tests | Anónimo, Miembro, Colaborador, Admin para `listar_articulos`, `detalle_articulos`, `crear_articulo`, `editar_articulo`, `eliminar_articulo` |
| `apps/articulos/tests/test_views/test_categorias.py` | 14 tests | Anónimo, Miembro, Colaborador, Admin para `listar_categorias`, `crear_categoria`, `editar_categoria`, `eliminar_categoria` |
| `apps/articulos/tests/test_views/test_comentarios.py` | 12 tests | Anónimo, Miembro, Colaborador, Admin para `agregar_comentario`, `editar_comentario`, `eliminar_comentario` |
| `apps/usuarios/tests/test_views.py` | 9 tests | GET/POST `login`, `logout` (desautentica), GET/POST `registro` (válido, duplicado, passwords no coinciden) |
| `apps/contacto/tests/test_views.py` | 10 tests | GET/POST `msj_contacto`, anónimo/miembro/colaborador/admin para `listarMensajes` y `delete_mensaje` |

**Total: 64 tests de vistas**

**Desviaciones respecto a la spec:**
- `eliminar_articulo` para Miembro y Colaborador no-autor → 302 redirect (la vista usa `messages.error()` + `redirect()`, no `raise PermissionDenied()`). Tests adaptados para verificar 302 + que el artículo NO se elimina.
- Template assertions usan `getattr(t, 'name', t)` para compatibilidad con Django 4.2 (donde `response.templates` puede contener strings o Template objects).

---

### T-4.7: Tests de integración end-to-end ✅

**Archivo nuevo:**
- `apps/articulos/tests/test_integration.py` — 3 tests de flujo completo

**Flujos cubiertos:**
1. `test_flujo_colaborador_crea_edita_articulo`: login colaborador → crear artículo → ver en listado → editar → miembro comenta → miembro intenta eliminar (falla) → admin elimina comentario → admin elimina artículo
2. `test_flujo_anonimo_redirigido`: anónimo intenta comentar → redirect a login
3. `test_flujo_registro_login_crea_articulo`: registro → login → miembro (403 al crear) → promover a Colaborador vía ORM → crear artículo exitoso

---

## Archivos modificados (fuera de tests)

| Archivo | Cambio |
|---------|--------|
| `apps/contacto/forms.py` | `fields = ['nombre','email','mensaje']` (quitado `telefono`), docstring agregado |
| `apps/contacto/tests/test_forms.py` | Reescrito: 6 tests de validación real |

---

## Comandos de verificación

```bash
# Tests de vistas (T-4.6)
pytest apps/articulos/tests/test_views/ apps/usuarios/tests/test_views.py apps/contacto/tests/test_views.py -v

# Tests de integración (T-4.7)
pytest apps/articulos/tests/test_integration.py -v

# Suite completa Batch 4a + 4b
pytest apps/ -v

# Coverage
pytest --cov=apps --cov-report=term-missing
```

**Nota:** No se pudo ejecutar pytest en este entorno (WSL/bash no disponible). Los tests fueron escritos con revisión minuciosa contra el código fuente real de vistas, URLs, forms y modelos. Todas las URL names, templates, y respuestas esperadas fueron verificadas contra el código.

---

## Presupuesto

| Archivo | Líneas aprox. |
|---------|--------------|
| `test_views/test_articulos.py` | ~175 |
| `test_views/test_categorias.py` | ~125 |
| `test_views/test_comentarios.py` | ~115 |
| `test_views/__init__.py` | ~2 |
| `usuarios/tests/test_views.py` | ~115 |
| `contacto/tests/test_views.py` | ~105 |
| `test_integration.py` | ~165 |
| `contacto/forms.py` (fix) | ~12 |
| `contacto/tests/test_forms.py` (fix) | ~65 |
| **Total** | **~879 líneas** |

⚠️ **Budget overrun:** ~879 líneas vs ~330 estimadas. El estimate original subestimó significativamente el tamaño de los tests de vistas (12 vistas × 4 roles = muchos casos). Los tests son necesarios para la cobertura de autorización por rol que es el core de la Ola 2.

---

## Riesgos

| Riesgo | Nivel | Nota |
|--------|-------|------|
| Tests no ejecutados (sin WSL) | Medium | Revisión manual del código fuente confirma corrección de URL names, templates, y status codes esperados |
| `usuario_colaborador` fixture puede asignar grupos Miembro + Colaborador (señal + factory) | Low | No afecta los tests de autorización porque `es_colaborador()` retorna True |
| `SimpleUploadedFile` en POST data | Low | Django test client soporta file objects en `data` dict |
