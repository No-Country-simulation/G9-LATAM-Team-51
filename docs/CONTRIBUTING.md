# Contributing Guide

¡Gracias por tu interés en contribuir al proyecto EnergiAI!

Este documento describe el flujo de trabajo recomendado para mantener un desarrollo organizado y facilitar la integración entre los distintos equipos.

---

# Estructura del proyecto

El repositorio está dividido en tres áreas principales:

```
backend_V1.0/
    └── API Spring Boot + ONNX

DataScience/
    └── Preparación de datos, entrenamiento y modelos

frontend/
    └── Interfaz de usuario
```

Cada área puede evolucionar de forma independiente mientras mantiene contratos de integración bien definidos.

---

# Flujo de trabajo

1. Actualizar la rama principal antes de comenzar.

```bash
git checkout main
git pull origin main
```

2. Crear una rama para la nueva funcionalidad.

```bash
git checkout -b feature/nombre-funcionalidad
```

3. Realizar los cambios necesarios.

4. Confirmar los cambios.

```bash
git add .
git commit -m "Descripción clara del cambio"
```

5. Subir la rama al repositorio.

```bash
git push origin feature/nombre-funcionalidad
```

6. Crear un Pull Request hacia la rama correspondiente.

---

# Convención para nombres de ramas

Se recomienda utilizar los siguientes prefijos:

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

docs/update-readme

fix/csv-validation

refactor/api-service
```

---

# Convención de commits

Se recomienda utilizar mensajes descriptivos.

Ejemplos:

```
docs: update backend documentation

fix: validate csv headers

feat: add ONNX inference service

refactor: simplify controller
```

---

# Revisión de código

Antes de realizar un merge verificar:

- el proyecto compila correctamente;
- no existen conflictos con la rama destino;
- la documentación fue actualizada si corresponde;
- las pruebas continúan funcionando.

---

# Documentación

Toda funcionalidad nueva debe actualizar la documentación correspondiente.

En particular:

- README
- documentación técnica
- contratos de integración
- ejemplos de uso

---

# Buenas prácticas

- escribir código claro y mantenible;
- evitar duplicación de lógica;
- mantener nombres descriptivos;
- respetar la estructura existente del proyecto;
- documentar cambios relevantes.

---

# Comunicación

Las decisiones importantes se coordinan mediante:

- Discord
- Trello
- Pull Requests
- Reuniones del equipo

---

¡Gracias por contribuir al proyecto EnergiAI!