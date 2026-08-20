"use strict";

// URL's de las API especificadas.
const urlApiConsumo = "http://152.70.138.232:8080/api/analisis-energetico";
const urlApiArchivo = "http://152.70.138.232:8080/api/analisis-energetico/csv";

// Elementos del DOM.
const fc = document.getElementById("form-consumo"); // Fc = Formulario de consumo
const fa = document.getElementById("form-archivo"); // Fc = Formulario de archivo
const inputArchivoCsv = document.getElementById("archivoCsv");
let resultados = document.getElementById("resultados");
let resultadosCsv = document.getElementById("resultadosCsv");

// 1. Cargar historial de localStorage al iniciar la aplicación.
let caja1 = document.addEventListener("DOMContentLoaded", displayHistorial);
let caja2 = document.addEventListener("DOMContentLoaded", displayHistorialCsv);

/////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////
// 2. Escuchar el envío del formulario de consumo .
fc.addEventListener("submit", async function (e) {
  e.preventDefault();
  // Validacion de datos del formulario.
  let ok = true;
  ok =
    setErr(
      fc,
      "consumo",
      numeroValido(fc.elements["consumoKwh"].value, { min: 0, max: 1000000 })
    ) && ok;
  ok =
    setErr(
      fc,
      "equipos",
      numeroValido(fc.elements["cantidadEquipos"].value, {
        entero: true,
        min: 1,
        max: 999,
      })
    ) && ok;
  ok =
    setErr(
      fc,
      "horas",
      numeroValido(fc.elements["horasAltoConsumo"].value, { min: 0, max: 24 })
    ) && ok;

  if (!ok) return;

  // Mapeo y conversión de datos exactos requeridos por la API
  const consumoData = {
    consumoKwh: Number(document.getElementById("consumoKwh").value),
    usoHorarioPico: document.getElementById("usoHorarioPico").value,
    cantidadEquipos: Number(document.getElementById("cantidadEquipos").value),
    tipoInmueble: document.getElementById("tipoInmueble").value,
    horasAltoConsumo: document.getElementById("horasAltoConsumo").value,
  };

  try {
    // categoria ,costoEstimadoMensual, probabilidad ,recomendaciones

    // Realizar consumo de la API mediante POST
    const apiResponse = await consumirApiAnalisis(consumoData);

    // Guardar en el historial de localStorage
    guardarEnLocalStorage(consumoData, apiResponse);

    // Actualizar la vista del historial en pantalla.
    displayHistorial();

    // Limpiar campos del formulario.
    fc.reset();
  } catch (error) {
    console.error("Error al realizar la consulta:", error);
    alert("Ocurrió un error al conectar con el servidor.");
  }
});

// Función para mostrar mensaje de error
function setErr(form, name, msg) {
  var el = form.querySelector('[data-err="' + name + '"]');
  if (el) el.textContent = msg || "";
  var input = form.elements[name];
  if (input) input.setAttribute("aria-invalid", msg ? "true" : "false");
  return !msg;
}

//Función para validar número en el formulario de consumo
function numeroValido(valor, opts) {
  opts = opts || {};
  var v = (valor || "").trim();
  if (!v) return "Este campo es obligatorio.";
  if (!/^\d+([.,]\d+)?$/.test(v)) return "Ingresa solo números positivos.";
  var n = Number(v.replace(",", "."));
  if (!isFinite(n)) return "Valor numérico inválido.";
  if (opts.entero && !Number.isInteger(n)) return "Debe ser un número entero.";
  if (opts.min != null && n < opts.min)
    return "El valor mínimo es " + opts.min + ".";
  if (opts.max != null && n > opts.max)
    return "El valor máximo es " + opts.max + ".";
  return "";
}

// Función para enviar la petición POST a la API
async function consumirApiAnalisis(datos) {
  const response = await fetch(urlApiConsumo, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST",
      Accept: "application/json",
    },
    body: JSON.stringify(datos),
  });

  if (!response.ok)
    throw new Error(`Error en el solicitud: status ${respuesta.status}`);

  return await response.json();
}

// Función para guardar datos de la consulta en localStorage
function guardarEnLocalStorage(peticion, respuesta) {
  const historial =
    JSON.parse(localStorage.getItem("historialEnergetico")) || [];

  const nuevoRegistro = {
    id: Date.now() + Math.random(),
    fecha: new Date().toLocaleDateString("es-ES"),
    peticion,
    respuesta,
  };
  console.log(peticion, respuesta);

  historial.push(nuevoRegistro);
  localStorage.setItem("historialEnergetico", JSON.stringify(historial));
}

// Función para renderizar los elementos almacenados en el contenedor  ul con id=containerMovements
function displayHistorial() {
  const historial =
    JSON.parse(localStorage.getItem("historialEnergetico")) || [];
  containerMovements.innerHTML = "";

  if (historial.length === 0) {
    resultados.textContent = `${historial.length} resultados`;
    containerMovements.innerHTML = `
      <li class="row">
        <span class="">No hay consultas previas en el historial</span>
      </li>`;
    return;
  } else
    historial.length === 1
      ? (resultados.textContent = `${historial.length} resultado `)
      : (resultados.textContent = `${historial.length} resultados `);

  // Renderizar las filas de resultados en orden inverso (más recientes primero)
  historial
    .slice()
    .reverse()
    .forEach((item, index) => {
      let categoria = item.respuesta.categoria;
      let horas = item.peticion.horasAltoConsumo;
      const html = `
      <li class="row">
        <span class="tag ${item.respuesta.categoria}">${
        item.respuesta.categoria
      }</span>
        <span><span class="only-mobile">Probabilidad: </span>${
          (item.respuesta.probabilidad * 100).toFixed(2) + "%"
        }</span>
        <span><span class="only-mobile">Consumo: </span>${
          categoria === "Ineficiente"
            ? "Alto"
            : categoria === "Moderado"
            ? "Medio"
            : "Bajo"
        }</span>
        <span><strong>${
          item.respuesta.costoEstimadoMensual.toFixed(2) + "$"
        }</strong></span>
        <label><span class="only-mobile">Recomendaciones:</span>
          <textarea
            name="${item.respuesta.categoria}"
            class="field"
            rows="3"
            readonly
            aria-label="Recomendaciones categoría Ineficiente"
          >${item.respuesta.recomendaciones}
          </textarea>
        </label>
        <p class="sub">Consumo (kWh): ${item.peticion.consumoKwh}</p>
        <p class="sub">Equipos: ${item.peticion.cantidadEquipos} </p>
        <p class="sub">Horario punta: ${horas === "true" ? "Si" : "No"} </p>
        <p class="sub">Horas de consumo: ${item.peticion.horasAltoConsumo}</p>
        <p class="sub">Tipo de inmueble: ${item.peticion.tipoInmueble}</p>
      </li>`;
      containerMovements.insertAdjacentHTML("beforeend", html);
    });
}

/////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////
/// Escucha del formulario de archivo fa = formulario de archivo

fa.addEventListener("submit", async function (e) {
  e.preventDefault();
  const ok = setErr(fa, "archivo", validarCsv());
  // ok =
  //   setErr(
  //     fa,
  //     "periodo",
  //     numeroValido(fa.elements["periodo"].value, {
  //       entero: true,
  //       min: 1,
  //       max: 120,
  //     })
  //   ) && ok;
  if (!ok) return;

  const archivo = inputArchivoCsv.files[0];

  // 1. Crear el objeto FormData y adjuntar el archivo
  // Nota: El primer parámetro ('file' o 'archivo') debe coincidir con el nombre
  // del parámetro que espera la API en el backend (ej: @RequestParam("file"))

  const formData = new FormData();
  formData.append("file", archivo);

  try {
    // 2. Enviar la petición a la API
    const respuestaApi = await consumirApiCsv(formData);

    // 3. Almacenar los resultados devueltos por la API en el historial de localStorage
    guardarEnLocalStorageCsv(respuestaApi, archivo.name);

    // 4. Actualizar la interfaz del historial y reiniciar el formulario
    displayHistorialCsv();

    // Limpiar campos del formulario
    fa.reset();
  } catch (error) {
    console.error("Error al subir el archivo CSV:", error);
    alert("Ocurrió un error al procesar el archivo CSV.");
  }
});

// Función para enviar FormData a la API mediante fetch
async function consumirApiCsv(formData) {
  const response = await fetch(urlApiArchivo, {
    method: "POST",
    // IMPORTANTE: Al enviar FormData, NO se debe definir 'Content-Type'.
    // El navegador asignará 'multipart/form-data' automáticamente.
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Error en la solicitud: status ${response.status}`);
  }

  return await response.json();
}

// Función para guardar cada resultado individual de la lista 'results' en localStorage del archivo.
function guardarEnLocalStorageCsv(dataApi, nombreArchivo) {
  const historial =
    JSON.parse(localStorage.getItem("historialEnergeticoCsv")) || [];

  // Iterar por cada resultado retornado en el arreglo "results"
  dataApi.results.forEach((item) => {
    const nuevoRegistro = {
      id: Date.now() + Math.random(),
      fecha: new Date().toLocaleDateString("es-ES"),
      origen: `CSV (${nombreArchivo})`,
      categoria: item.categoria,
      probabilidad: (item.probabilidad * 100).toFixed(2) + "%",
      costo: `${item.costoEstimadoMensual.toFixed(2)}`,
      recomendaciones: item.recomendaciones
        ? item.recomendaciones.join(" | ")
        : "Sin recomendaciones",
    };

    historial.push(nuevoRegistro);
    console.log(historial);
  });

  localStorage.setItem("historialEnergeticoCsv", JSON.stringify(historial));
}

// Función para renderizar los elementos almacenados en el contenedor  ul con id=containerMovementsCsv
function displayHistorialCsv() {
  const historial =
    JSON.parse(localStorage.getItem("historialEnergeticoCsv")) || [];
  containerMovementsCsv.innerHTML = "";

  if (historial.length === 0) {
    resultadosCsv.textContent = `${historial.length} resultados`;
    containerMovementsCsv.innerHTML = `
    <li class="row">
    <span class="">No hay archivos previos en el historial</span>
  </li>`;
    return;
  } else
    historial.length === 1
      ? (resultadosCsv.textContent = `${historial.length} resultado `)
      : (resultadosCsv.textContent = `${historial.length} resultados `);

  // Renderizar las filas de resultados en orden inverso (más recientes primero)
  historial
    .slice()
    .reverse()
    .forEach((item) => {
      let categoria = item.categoria;
      const html = `
      <li class="row">
        <span class="tag ${item.categoria}">${item.categoria}</span>
        <span><span class="only-mobile">Probabilidad: </span>${
          item.probabilidad
        }</span>
        <span><span class="only-mobile">Consumo: </span>${
          categoria === "Ineficiente"
            ? "Alto"
            : categoria === "Moderado"
            ? "Medio"
            : "Bajo"
        }</span>
        <span><strong>${item.costo}</strong></span>
        <label><span class="only-mobile">Recomendaciones:</span>
          <textarea
            name="${item.categoria}"
            class="field"
            rows="3"
            readonly
            aria-label="Recomendaciones categoría Ineficiente"
          >${item.recomendaciones}
          </textarea>
        </label>
      </li>`;
      containerMovementsCsv.insertAdjacentHTML("beforeend", html);
    });
}

// Función para validar archivo CSV

function validarCsv() {
  var f = fa.elements["archivo"].files[0];
  if (!f) return "Selecciona un archivo CSV.";
  if (!/\.csv$/i.test(f.name))
    return "Solo se permiten archivos con extensión .csv.";
  if (f.size > 5 * 1024 * 1024) return "El archivo no debe superar 5 MB.";
  return "";
}
fa.elements["archivo"].addEventListener("change", function () {
  var msg = validarCsv();
  if (msg && msg !== "Selecciona un archivo CSV.")
    fa.elements["archivo"].value = "";
  setErr(fa, "archivo", msg === "Selecciona un archivo CSV." ? "" : msg);
});
///////////////////////////////
///////////////////////////////
//funcion para borrar historial

function borrarHistorial() {
  localStorage.clear();
  displayHistorial();
  displayHistorialCsv();
}
/*
function mostrarPestana() {
  //Selecciona todas las pentañas
  const tabs = document.querySelectorAll('[role="tab"]');
  const panels = document.querySelectorAll('[role="tabpanel"]');

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      // 1. Deseleccionar todas las pestañas y bloquear su foco con teclado
      tabs.forEach((t) => {
        t.setAttribute("aria-selected", "false");
        t.setAttribute("tabindex", "-1");
      });

      // 2. Ocultar todos los paneles de las tablas
      panels.forEach((panel) => panel.setAttribute("hidden", ""));

      // 3. Activar la pestaña actual
      tab.setAttribute("aria-selected", "true");
      tab.removeAttribute("tabindex");

      // 4. Mostrar la tabla vinculada mediante el id en aria-controls
      const targetPanelId = tab.getAttribute("aria-controls");
      const targetPanel = document.getElementById(targetPanelId);
      targetPanel.removeAttribute("hidden");
    });
  });
}
*/
