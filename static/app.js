
const form = document.getElementById("reportForm");
const result = document.getElementById("result");
const submitButton = document.getElementById("submitButton");
const gpsStatus = document.getElementById("gpsStatus");
const photoInput = document.getElementById("foto");
const preview = document.getElementById("preview");
const aiStatus = document.getElementById("aiStatus");

const WHATSAPP_NUMBER = "525650506533";

let imagenValida = false;
let enviando = false;
let revision = 0;
let previewURL = null;

submitButton.disabled = true;

// Actualizar estado del boton
function actualizarBoton() {
  submitButton.disabled = !imagenValida || enviando;
}

// Mostrar resultado de la inteligencia artificial
function mostrarEstado(tipo, mensaje) {
  aiStatus.className = "ai-status " + tipo;
  aiStatus.textContent = mensaje;
}

// Limpiar vista previa
function limpiarVista() {
  preview.hidden = true;
  preview.removeAttribute("src");

  if (previewURL) {
    URL.revokeObjectURL(previewURL);
    previewURL = null;
  }
}

// Obtener ubicacion GPS
document.getElementById("gpsButton")
  .addEventListener("click", () => {

  if (!navigator.geolocation) {
    gpsStatus.textContent =
      "Este navegador no permite obtener la ubicación.";
    return;
  }

  gpsStatus.textContent =
    "Solicitando permiso de ubicación...";

  navigator.geolocation.getCurrentPosition(
    (position) => {

      document.getElementById("latitud").value =
        position.coords.latitude;

      document.getElementById("longitud").value =
        position.coords.longitude;

      gpsStatus.textContent =
        `Ubicación agregada: ${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`;

    },
    () => {
      gpsStatus.textContent =
        "No se obtuvo la ubicación. Puedes enviar sin GPS.";
    },
    {
      enableHighAccuracy: true,
      timeout: 12000
    }
  );
});

// Analizar automaticamente la fotografia
photoInput.addEventListener("change", async () => {

  const revisionActual = ++revision;

  imagenValida = false;
  actualizarBoton();

  result.textContent = "";
  limpiarVista();

  const archivo = photoInput.files[0];

  if (!archivo) {

    mostrarEstado(
      "",
      "🤖 Selecciona una fotografía para analizarla."
    );

    return;
  }

  if (archivo.size > 8 * 1024 * 1024) {

    mostrarEstado(
      "rechazada",
      "❌ La fotografía supera los 8 MB."
    );

    return;
  }

  previewURL = URL.createObjectURL(archivo);
  preview.src = previewURL;
  preview.hidden = false;

  mostrarEstado(
    "analizando",
    "⏳ Analizando fotografía con inteligencia artificial..."
  );

  const datos = new FormData();
  datos.append("foto", archivo);

  try {

    const response = await fetch("/api/validar-foto", {
      method: "POST",
      body: datos
    });

    const data = await response.json();

    // Ignorar resultados de una fotografia anterior
    if (revisionActual !== revision) {
      return;
    }

    if (!response.ok) {
      throw new Error(
        data.detail || "No se pudo analizar la imagen."
      );
    }

    if (data.aceptada) {

      imagenValida = true;

      mostrarEstado(
        "aceptada",
        `✅ Basura detectada. Puntuación: ${data.basura}%. Puedes enviar el reporte.`
      );

    } else {

      imagenValida = false;

      mostrarEstado(
        "rechazada",
        `❌ Imagen rechazada. No se confirma basura acumulada. Puntuación: ${data.basura}%. Selecciona otra fotografía.`
      );

    }

  } catch (error) {

    if (revisionActual !== revision) {
      return;
    }

    imagenValida = false;

    mostrarEstado(
      "rechazada",
      "❌ " + error.message
    );

  } finally {

    if (revisionActual === revision) {
      actualizarBoton();
    }

  }

});

// Enviar reporte
form.addEventListener("submit", async (event) => {

  event.preventDefault();

  if (!imagenValida || enviando) {
    return;
  }

  const datos = new FormData(form);

  enviando = true;
  photoInput.disabled = true;
  actualizarBoton();

  result.className = "result";
  result.textContent = "";

  submitButton.textContent = "Guardando reporte...";

  const obtener = (nombre) => {
    const valor = datos.get(nombre);

    return typeof valor === "string" && valor.trim()
      ? valor.trim()
      : "No especificado";
  };

  const calle = obtener("calle");
  const referencia = obtener("referencia");
  const descripcion = obtener("descripcion");
  const latitud = obtener("latitud");
  const longitud = obtener("longitud");

  let mapa = "No se proporcionó ubicación GPS";

  if (
    latitud !== "No especificado" &&
    longitud !== "No especificado"
  ) {
    mapa = `https://www.google.com/maps?q=${latitud},${longitud}`;
  }

  const mensaje = [
    "🌱 *TLALTELULCO LIMPIO*",
    "📋 *NUEVO REPORTE CIUDADANO*",
    "",
    "📍 *Municipio:* La Magdalena Tlaltelulco",
    `*Calle o colonia:* ${calle}`,
    `*Referencia:* ${referencia}`,
    `*Descripción:* ${descripcion}`,
    "",
    `📍 *Ubicación:* ${mapa}`,
    "",
    "🤖 Fotografía validada por inteligencia artificial.",
    "📷 Adjuntar manualmente la fotografía seleccionada.",
    "",
    "Reporte generado desde Tlaltelulco Limpio."
  ].join("\n");

  const whatsappURL =
    `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(mensaje)}`;

  const ventanaWhatsApp =
    window.open("about:blank", "_blank");

  try {

    const response = await fetch("/api/reportar", {
      method: "POST",
      body: datos
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "No se pudo guardar el reporte."
      );
    }

    result.className = "result success";

    result.textContent =
      "Reporte guardado correctamente. Confirma el envío en WhatsApp y adjunta la fotografía.";

    if (ventanaWhatsApp && !ventanaWhatsApp.closed) {

      ventanaWhatsApp.location.href = whatsappURL;

    } else {

      const enlace = document.createElement("a");

      enlace.href = whatsappURL;
      enlace.target = "_blank";
      enlace.rel = "noopener noreferrer";
      enlace.textContent = "Abrir WhatsApp";

      result.appendChild(document.createElement("br"));
      result.appendChild(enlace);

    }

    form.reset();

    revision++;
    imagenValida = false;

    limpiarVista();

    document.getElementById("latitud").value = "";
    document.getElementById("longitud").value = "";

    gpsStatus.textContent =
      "Puedes compartir tu ubicación para señalar el sitio del reporte.";

    mostrarEstado(
      "",
      "🤖 Selecciona una fotografía para analizarla."
    );

  } catch (error) {

    if (ventanaWhatsApp && !ventanaWhatsApp.closed) {
      ventanaWhatsApp.close();
    }

    imagenValida = false;

    result.className = "result error";
    result.textContent = error.message;

    mostrarEstado(
      "rechazada",
      "Selecciona nuevamente una fotografía para validarla."
    );

  } finally {

    enviando = false;
    photoInput.disabled = false;

    submitButton.textContent = "Enviar reporte";

    actualizarBoton();

  }

});
