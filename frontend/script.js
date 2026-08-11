"use strict";

// URL's de las API especificadas.
const urlApiConsumo = "http://152.70.138.232:8080/api/analisis-energetico";
const urlApiArchivo = "http://152.70.138.232:8080/api/analisis-energetico/csv";

// Elementos del DOM.
const fc = document.getElementById("form-consumo"); // Fc = Formulario de consumo
const fa = document.getElementById("form-archivo"); // Fc = Formulario de archivo
let resultados = document.getElementById("resultados");

// 1. Cargar historial de localStorage al iniciar la aplicación.
document.addEventListener("DOMContentLoaded", displayHistorial);

// 2. Escuchar el envío del formulario.
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

//Función para validar número
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
    id: Date.now(),
    fecha: new Date().toLocaleDateString("es-ES"),
    peticion,
    respuesta,
  };

  historial.push(nuevoRegistro);
  localStorage.setItem("historialEnergetico", JSON.stringify(historial));
}

// Función para renderizar los elementos almacenados en el contenedor  ul con id=containerMovements
function displayHistorial() {
  const historial =
    JSON.parse(localStorage.getItem("historialEnergetico")) || [];
  containerMovements.innerHTML = "";

  if (historial.length === 0) {
    resultados.textContent = `${historial.length} resultado`;
    containerMovements.innerHTML = `
      <li class="row">
        <span class="">No hay consultas previas en el historial</span>
      </li>`;
    return;
  } else resultados.textContent = `${historial.length} resultados `;

  // Renderizar cada consulta almacenada
  historial
    .slice()
    .reverse()
    .forEach((item, index) => {
      const html = `
      <li class="row">
        <span class="tag ${item.respuesta.categoria}">${
        item.respuesta.categoria
      }</span>
        <span><span class="only-mobile">Probabilidad: </span>${
          item.respuesta.probabilidad * 100
        }%</span>
        <span><span class="only-mobile">Clase: </span>${
          item.respuesta.categoria
        }</span>
        <span><strong>${item.respuesta.costoEstimadoMensual}</strong></span>
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
      </li>`;
      containerMovements.insertAdjacentHTML("beforeend", html);
    });
}

/////////////////////////////////////////////////////////////////
///// Escucha del formulario de archivo fa = formulario de archivo
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
fa.addEventListener("submit", function (e) {
  e.preventDefault();
  var ok = setErr(fa, "archivo", validarCsv());
  ok =
    setErr(
      fa,
      "periodo",
      numeroValido(fa.elements["periodo"].value, {
        entero: true,
        min: 1,
        max: 120,
      })
    ) && ok;
});
