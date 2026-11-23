
const form = document.getElementById("reportForm");
const result = document.getElementById("result");
const submitButton = document.getElementById("submitButton");
const gpsStatus = document.getElementById("gpsStatus");
const photoInput = document.getElementById("foto");
const preview = document.getElementById("preview");

// WhatsApp que recibirá los reportes
const WHATSAPP_NUMBER = "525650506533";

// Obtener ubicación GPS
document.getElementById("gpsButton").addEventListener("click", () => {
  if (!navigator.geolocation) {
    gpsStatus.textContent = "Este navegador no permite obtener la ubicación.";
    return;
  }

  gpsStatus.textContent = "Solicitando permiso de ubicación...";

  navigator.geolocation.getCurrentPosition(
    (position) => {
      document.getElementById("latitud").value = position.coords.latitude;
      document.getElementById("longitud").value = position.coords.longitude;

      gpsStatus.textContent =
        `Ubicación agregada: ${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`;
    },
    () => {
      gpsStatus.textContent =
        "No se obtuvo la ubicación. Puedes enviar el reporte sin GPS.";
    },
    { enableHighAccuracy: true, timeout: 12000 }
  );
});

// Vista previa de fotografía
photoInput.addEventListener("change", () => {
  const file = photoInput.files[0];

  if (!file) {
    preview.hidden = true;
    preview.removeAttribute("src");
    return;
  }

  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
});

// Enviar reporte
form.addEventListener("submit", async (event) => {
  event.preventDefault();

  result.className = "result";
  result.textContent = "";

  const datos = new FormData(form);

  // Obtener los datos reales del formulario
  const obtener = (...nombres) => {
    for (const nombre of nombres) {
      const valor = datos.get(nombre);
      if (typeof valor === "string" && valor.trim()) {
        return valor.trim();
      }
    }
    return "No especificado";
  };

  const calle = obtener("calle", "calle_colonia", "ubicacion");
  const referencia = obtener("referencia", "puntos_referencia");
  const descripcion = obtener("descripcion");
  const latitud = obtener("latitud");
  const longitud = obtener("longitud");

  let mapa = "No se proporcionó ubicación GPS";

  if (latitud !== "No especificado" &&
      longitud !== "No especificado") {
    mapa = `https://www.google.com/maps?q=${latitud},${longitud}`;
  }

  const fotografia = photoInput.files[0];

  const mensaje = [
    "🌱 *TLALTELULCO LIMPIO*",
    "📋 *NUEVO REPORTE CIUDADANO*",
    "",
    "📍 *Municipio:* La Magdalena Tlaltelulco",
    `🏘️ *Calle o colonia:* ${calle}`,
    `📌 *Punto de referencia:* ${referencia}`,
    "",
    `📝 *Descripción:* ${descripcion}`,
    "",
    `🗺️ *Ubicación:* ${mapa}`,
    "",
    fotografia
      ? "📷 *Fotografía:* Adjuntar la imagen seleccionada."
      : "📷 *Fotografía:* No adjuntada.",
    "",
    "Reporte generado desde Tlaltelulco Limpio."
  ].join("\n");

  const whatsappURL =
    `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(mensaje)}`;

  // Abrir una ventana durante el clic para evitar bloqueos
  const ventanaWhatsApp = window.open("about:blank", "_blank");

  submitButton.disabled = true;
  submitButton.textContent = "Preparando reporte...";

  try {
    const response = await fetch("/api/reportar", {
      method: "POST",
      body: datos
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "No se pudo guardar el reporte.");
    }

    result.className = "result success";
    result.textContent =
      "Reporte guardado. Confirma el envío en WhatsApp y adjunta la fotografía si corresponde.";

    // Abrir WhatsApp con el mensaje preparado
    if (ventanaWhatsApp && !ventanaWhatsApp.closed) {
      ventanaWhatsApp.location.href = whatsappURL;
    } else {
      const enlace = document.createElement("a");
      enlace.href = whatsappURL;
      enlace.target = "_blank";
      enlace.rel = "noopener noreferrer";
      enlace.textContent = "Abrir WhatsApp para enviar el reporte";
      result.appendChild(document.createElement("br"));
      result.appendChild(enlace);
    }

    form.reset();

    document.getElementById("latitud").value = "";
    document.getElementById("longitud").value = "";

    gpsStatus.textContent =
      "Puedes compartir tu ubicación para señalar el sitio del reporte.";

    preview.hidden = true;
    preview.removeAttribute("src");

  } catch (error) {
    if (ventanaWhatsApp && !ventanaWhatsApp.closed) {
      ventanaWhatsApp.close();
    }

    result.className = "result error";
    result.textContent =
      error.message || "Ocurrió un error al procesar el reporte.";

  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Enviar reporte";
  }
});
