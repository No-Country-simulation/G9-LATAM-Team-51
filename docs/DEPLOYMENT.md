# Deployment

Guía breve para ejecutar el backend localmente y entender el proceso de despliegue en OCI.

---

## 1. Requisitos

Para ejecutar el backend localmente se necesita:

- Java 21 (LTS)
- Maven
- Git
- Acceso al repositorio del proyecto

El backend utiliza:

- Spring Boot
- ONNX Runtime
- Java 25
- Springdoc OpenAPI

---

## 2. Estructura necesaria

El backend se encuentra en:

```text
backend/
├── pom.xml
├── mvnw
├── mvnw.cmd
└── src/
    └── main/
        ├── java/
        └── resources/
            ├── application.properties
            └── models/
                └── energy_efficiency_classifier_v1.onnx
````

El modelo ONNX es cargado como recurso de la aplicación mediante:

```properties
model.path=models/energy_efficiency_classifier_v1.onnx
```

Por lo tanto, el archivo del modelo debe mantenerse dentro de:

```text
src/main/resources/models/
```

---

## 3. Ejecución local

Ingresar a la carpeta del backend:

```bash
cd backend
```

### Windows

```bash
mvnw.cmd spring-boot:run
```

### Linux / macOS

```bash
./mvnw spring-boot:run
```

También puede utilizarse Maven directamente:

```bash
mvn spring-boot:run
```

Si la aplicación inicia correctamente, Spring Boot levantará el servidor y mostrará en consola que la aplicación está ejecutándose.

---

## 4. Verificación de la API

El backend expone sus endpoints bajo el puerto `8080` con el prefijo:

```text
http://localhost:8080/api
```

El endpoint principal de análisis es:

```text
POST /api/analisis-energetico
```

También existe procesamiento de archivos CSV:

```text
POST /api/analisis-energetico/csv
```

La documentación interactiva de OpenAPI/Swagger está disponible cuando la aplicación está ejecutándose.

---

## 5. Despliegue en OCI

El backend se encuentra preparado para ejecutarse como una aplicación Spring Boot y utiliza el modelo ONNX incluido dentro de los recursos de la aplicación.

El flujo general de despliegue es:

```text
Código backend
      │
      ▼
Compilación con Maven
      │
      ▼
Aplicación Spring Boot
      │
      ▼
Servidor / instancia OCI
      │
      ▼
API disponible para el frontend
```

Antes de desplegar una nueva versión se recomienda:

1. Verificar que los cambios estén en la rama correspondiente.
2. Ejecutar la compilación del proyecto.
3. Ejecutar las pruebas disponibles.
4. Confirmar que el modelo ONNX esté incluido en los recursos.
5. Verificar los endpoints principales.
6. Desplegar la versión validada en OCI.
7. Comprobar nuevamente la API desde el entorno desplegado.

> **Nota:** La configuración concreta de la instancia, red, puertos, dominio, credenciales y comandos utilizados en OCI depende de la infraestructura configurada por el equipo. Esta documentación no fija valores que puedan cambiar entre entornos.

---

## 6. Checklist rápido

### Local

* [ ] Java 21 (LTS) instalado
* [ ] Proyecto actualizado
* [ ] Modelo ONNX presente
* [ ] Dependencias descargadas
* [ ] Aplicación inicia correctamente
* [ ] Endpoint JSON responde
* [ ] Endpoint CSV responde

### OCI

* [ ] Versión validada localmente
* [ ] Modelo incluido
* [ ] Aplicación compilada
* [ ] Nueva versión desplegada
* [ ] API accesible
* [ ] Endpoint principal verificado

---

## 7. Problemas comunes

### El modelo ONNX no se encuentra

Verificar que exista:

```text
src/main/resources/models/energy_efficiency_classifier_v1.onnx
```

y que `application.properties` contenga:

```properties
model.path=models/energy_efficiency_classifier_v1.onnx
```

### La aplicación no inicia

Revisar:

* versión de Java;
* dependencias Maven;
* errores mostrados durante el arranque;
* disponibilidad del archivo ONNX.

### La API responde con error

Revisar el formato del request y los valores permitidos por la API.

En particular:

* `consumoKwh` debe ser mayor que `0`.
* `usoHorarioPico` debe ser booleano.
* `cantidadEquipos` debe ser al menos `1`.
* `tipoInmueble` debe ser `Casa` o `Departamento`.
* `horasAltoConsumo` debe estar entre `0` y `24`.

---

## 8. Referencias

* `API_REFERENCE.md` — endpoints y formatos de entrada/salida.
* `architecture.md` — arquitectura y flujo de datos.
* `TESTING.md` — pruebas y validación.

```
