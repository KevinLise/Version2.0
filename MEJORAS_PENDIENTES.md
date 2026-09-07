# Mejoras Pendientes - Academia AI Assistant

## Resumen Ejecutivo

| Prioridad | Cantidad | Estado |
|-----------|----------|--------|
| ALTO | 6 | Corregidos |
| MEDIO | 10 | Parcialmente corregidos |
| BAJO | 11 | Pendientes |

---

## ALTA PRIORIDAD - CORREGIDOS

### [ALTO-1] Dependencia incorrecta en requirements.txt
- **Archivo:** `requirements.txt:5`
- **Problema:** `google-generativeai` vs `google-genai` (SDK correcto)
- **Estado:** CORREGIDO - Se reemplazó por `google-genai>=0.3.0`

### [ALTO-2] README.md con conflictos de merge
- **Archivo:** `README.md`
- **Problema:** Marcadores `<<<<<<< HEAD` sin resolver
- **Estado:** CORREGIDO - Se mantuvo la versión completa

### [ALTO-3] Git rebase en estado roto
- **Archivo:** Repositorio raíz
- **Problema:** Rebase a medio camino, HEAD detached
- **Estado:** Pendiente - Ejecutar `git rebase --abort`

### [ALTO-4] llm/client.py - Historial nunca se usa
- **Archivo:** `llm/client.py:17`
- **Problema:** Parámetro `history` aceptado pero ignorado
- **Estado:** CORREGIDO - Se implementa el uso del historial en la llamada

### [ALTO-5] rag/retriever.py - Llamadas síncronas bloqueantes
- **Archivo:** `rag/retriever.py:33,35-38`
- **Problema:** Métodos `async` con operaciones síncronas
- **Estado:** CORREGIDO - Se usa `asyncio.to_thread()`

### [ALTO-6] Dependencias faltantes en requirements.txt
- **Archivo:** `requirements.txt`
- **Problema:** Faltan `pytest` y `pytest-asyncio`
- **Estado:** CORREGIDO - Se agregaron las dependencias

---

## MEDIA PRIORIDAD

### [MEDIO-1] .env - API key expuesta
- **Archivo:** `.env:1`
- **Problema:** API key real en archivo
- **Estado:** Pendiente - Rotar key y verificar historial de git

### [MEDIO-2] Tests async sin configuración
- **Archivo:** `tests/test_cache.py`
- **Problema:** Falta `pytest-asyncio` configurado
- **Estado:** CORREGIDO - Se creó `pytest.ini`

### [MEDIO-3] cache_service.py - Excepciones silenciadas
- **Archivo:** `services/cache_service.py:62-63,98-99,124-125`
- **Problema:** `except: pass` sin logging
- **Estado:** CORREGIDO - Se agregó logging

### [MEDIO-4] rag/ingest.py - Operaciones síncronas
- **Archivo:** `rag/ingest.py:100`
- **Problema:** Método `async` con operaciones síncronas
- **Estado:** CORREGIDO - Se usa `asyncio.to_thread()`

### [MEDIO-5] rag/reranker.py - Async innecesario
- **Archivo:** `rag/reranker.py:43`
- **Problema:** `async` sin I/O
- **Estado:** Pendiente - Cambiar a síncrono

### [MEDIO-6] llm/prompts.py - Template no usado
- **Archivo:** `llm/prompts.py:25-37`
- **Problema:** `HUMAN_ESCALATION_TEMPLATE` definido pero no utilizado
- **Estado:** Pendiente - Usar en chat_service.py

### [MEDIO-7] tests/test_api.py - Mock incompleto
- **Archivo:** `tests/test_api.py:67-73`
- **Problema:** Mock sin campos requeridos
- **Estado:** CORREGIDO - Se agregaron campos faltantes

### [MEDIO-8] index.html - Pestañas sin funcionalidad
- **Archivo:** `static/index.html:480-487`
- **Problema:** Pestañas "Historial" y "Base de conocimiento" muertas
- **Estado:** CORREGIDO - Se eliminaron las pestañas

### [MEDIO-9] venv creado en Linux
- **Archivo:** `venv/`
- **Problema:** Inutilizable en Windows
- **Estado:** Pendiente - Recrear venv

### [MEDIO-10] RAG_SCORE_THRESHOLD inconsistente
- **Archivo:** `.env:12` vs `.env.example:12` vs `README.md:333`
- **Problema:** Valores diferentes (0.20 vs 0.70)
- **Estado:** CORREGIDO - Sincronizado a 0.70

---

## BAJA PRIORIDAD

### [BAJO-1] No hay Dockerfile
### [BAJO-2] No hay pipeline CI/CD
### [BAJO-3] No hay pyproject.toml ni pytest.ini
- **Estado:** CORREGIDO - Se creó `pytest.ini`

### [BAJO-4] No hay rate limiting en /chat
### [BAJO-5] No hay max_length en ChatRequest.message
- **Estado:** CORREGIDO - Se agregó `max_length=2000`

### [BAJO-6] No hay timeout en llamadas a Gemini
### [BAJO-7] No hay separación por entorno
### [BAJO-8] test_threshold.py - Valor inconsistente
- **Estado:** CORREGIDO - Se sincronizó el valor

### [BAJO-9] f-string anidado en chat_service.py
- **Estado:** CORREGIDO - Se extrajo a variable

### [BAJO-10] user_memory.py - Guarda en cada operación
### [BAJO-11] Typo en precios_y_niveles.md
- **Estado:** CORREGIDO - "transfersencia" → "transferencia"

---

## Plan de Acción Inmediato

1. ✅ Corregir requirements.txt
2. ✅ Resolver README.md
3. ✅ Corregir llm/client.py (historial)
4. ✅ Corregir rag/retriever.py (async)
5. ✅ Corregir cache_service.py (logging)
6. ✅ Sincronizar RAG_SCORE_THRESHOLD
7. ✅ Eliminar pestañas muertas del sidebar
8. ✅ Corregir rag/ingest.py (async)
9. ✅ Crear pytest.ini
10. ✅ Corregir test_api.py (mock)
11. ✅ Corregir chat_service.py (f-string)
12. ✅ Corregir test_threshold.py
13. ✅ Corregir precios_y_niveles.md (typo)
14. ✅ Agregar max_length a ChatRequest

## Pendientes Manuales

- Ejecutar `git rebase --abort` para arreglar el repositorio
- Recrear `venv` en Windows: `python -m venv venv`
- Rotar API key de Gemini si fue comprometida
- Configurar rate limiting (slowapi)
- Crear Dockerfile
- Configurar CI/CD con GitHub Actions
