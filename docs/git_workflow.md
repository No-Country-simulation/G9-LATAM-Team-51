# Git Workflow

## Objetivo

Este documento describe la estrategia de ramas utilizada en el proyecto EnergiAI.

Su propósito es mantener un flujo de trabajo organizado entre los equipos de Data Science, Backend y Frontend, evitando conflictos durante el desarrollo e integración.

---

# Flujo general

```
                 main
                  │
        ┌─────────┴─────────┐
        │                   │
   backend1.0         futuras versiones
        │
 ┌──────┼─────────┐
 │      │         │
fix/  feature/  docs/
```

Las ramas temporales deben integrarse mediante Pull Request una vez revisadas y aprobadas.

---

# Ramas principales

## main

Estado:

```
Producción
```

Descripción:

Contiene la versión estable e integrada del proyecto.

Solo debe recibir cambios revisados y aprobados.

---

## backend1.0

Estado:

```
Desarrollo principal del Backend
```

Incluye:

- API Spring Boot
- Integración ONNX
- Validaciones
- Endpoints
- Contrato con Data Science

Esta rama constituye la base para la versión 1.0 del backend.

---

# Ramas históricas

## backen0.5

Propósito:

Primera versión funcional del backend.

Se conserva únicamente como referencia histórica y respaldo de desarrollos anteriores.

No debe utilizarse para nuevos desarrollos.

---

## model-training-tomas

Propósito:

Desarrollo del pipeline de Machine Learning.

Incluye:

- limpieza;
- entrenamiento;
- notebooks;
- modelos;
- reportes;
- documentación técnica.

Una vez integrado, su contenido forma parte de la versión oficial del proyecto.

---

## sol-methodology

Propósito:

Desarrollo de la metodología de construcción de etiquetas.

Incluye:

- definición de categorías;
- documentación metodológica;
- experimentos de etiquetado.

Su contenido fue integrado al pipeline final.

---

## data-cleaning

Propósito:

Preparación inicial del conjunto de datos.

Incluye:

- limpieza;
- normalización;
- transformación;
- generación de datasets procesados.

Una vez consolidado, dejó de recibir cambios.

---

# Flujo recomendado

Para desarrollar una nueva funcionalidad:

```bash
git checkout main

git pull origin main

git checkout -b feature/nueva-funcionalidad
```

Realizar los cambios.

Guardar.

Commit.

```bash
git add .

git commit -m "feat: descripción del cambio"
```

Subir la rama.

```bash
git push origin feature/nueva-funcionalidad
```

Crear Pull Request.

Esperar revisión.

Realizar Merge.

Eliminar la rama temporal.

---

# Convención de ramas

Se recomienda utilizar:

```
feature/

fix/

docs/

refactor/

test/

hotfix/
```

Ejemplos:

```
feature/frontend-dashboard

feature/swagger-documentation

fix/csv-validation

docs/readme-update

refactor/service-layer
```

---

# Buenas prácticas

Antes de crear una rama:

- actualizar la rama principal;
- verificar conflictos pendientes;
- revisar Pull Requests abiertos.

Antes de hacer Merge:

- proyecto compila correctamente;
- documentación actualizada;
- pruebas ejecutadas;
- revisión por otro integrante.

---

# Ciclo de integración

```
Feature Branch
        │
        ▼
Pull Request
        │
        ▼
Code Review
        │
        ▼
Merge
        │
        ▼
main
```

---

# Estado actual del proyecto

| Rama | Estado | Observación |
|-------|--------|-------------|
| main | Estable | Rama oficial del proyecto |
| backend1.0 | Activa | Desarrollo principal del backend |
| model-training-tomas | Integrada | Pipeline de Machine Learning |
| sol-methodology | Integrada | Metodología de etiquetado |
| data-cleaning | Integrada | Preparación del dataset |
| backen0.5 | Histórica | Referencia de versiones anteriores |

---

# Recomendaciones

- Evitar desarrollar directamente sobre `main`.
- Utilizar ramas temporales para nuevas funcionalidades.
- Documentar cambios importantes.
- Eliminar ramas obsoletas una vez integradas.
- Mantener actualizado este documento cuando se incorpore una nueva estrategia de ramas.