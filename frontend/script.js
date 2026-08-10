'use strict';
/*
const express = require('express');
const cors = require('cors');
const app = express();

// Allow requests from your specific frontend origin
app.use(cors({ origin: 'http://127.0.0.1:5500' }));

app.post('/api/analisis-energetico', (req, res) => {
  res.json({ message: 'Success' });
});
*/
function setErr(form, name, msg) {
  var el = form.querySelector('[data-err="' + name + '"]');
  if (el) el.textContent = msg || "";
  var input = form.elements[name];
  if (input) input.setAttribute("aria-invalid", msg ? "true" : "false");
  return !msg;
}
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
/////////////////////////////////////////////////////////////////
///// Escucha del formulario de conumo fc = formulario de consumo 
var fc = document.getElementById("form-consumo");
fc.addEventListener("submit", async (e) => {
  e.preventDefault();
  var ok = true;
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

  try {
    const dataConsumo = {
      consumoKwh: Number(document.getElementById("consumoKwh").value),
      usoHorarioPico: document.getElementById("usoHorarioPico").value,
      cantidadEquipos: Number(document.getElementById("cantidadEquipos").value),
      tipoInmueble: document.getElementById("tipoInmueble").value,
      horasAltoConsumo: Number(document.getElementById("horasAltoConsumo").value)

    };
    // Enviar la consulta al serviddor 
    const respuestaServidor = await enviarPeticionApi(dataConsumo);


    alert('Análisis energetico procesado con éxito.');
  } catch (error) {
    console.error('Error en la API de análisis energetico:', error);
    alert('No se pudo conectar con el servicio de análisis energetico. Revisa la consola. ');
  }
});
/*
////////////////////////////////
/////////////////7 prueba con otra API

const apiUrl = "https://rickandmortyapi.com/api/character";

async function getCharacter() {
try {
 
const response = await fetch(apiUrl);
const { results } = await response.json();
 
console.log(results);
 
} catch (error) {
console.error(error.message);
 
 
}

}

getCharacter();

*/






/////////////////////////////////////////////////
///// Funcion fetch 
async function enviarPeticionApi(datos) {
  const URL_API = 'http://152.70.138.232:8080/api/analisis-energetico';
  const respuesta = await fetch(URL_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': 'http://127.0.0.1:5500',
      'Access-Control-Allow-Methods': 'POST',
      Accept: 'application/json',
      mode: "no-cors"
    },
    body: JSON.stringify(datos)
  });

  if (!respuesta.ok) throw new Error(`Error en el servidor: status ${respuesta.status}`);

  return await respuesta.json();
}


/////////////////////////////////////////////////////////////////
///// Escucha del formulario de archivo fa = formulario de archivo
var fa = document.getElementById("form-archivo");
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