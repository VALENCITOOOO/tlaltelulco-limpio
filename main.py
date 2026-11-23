import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

APP_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", APP_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
REPORTS_FILE = DATA_DIR / "reportes.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# IMPORTANTE: sustituye este número por el WhatsApp real del Ayuntamiento.
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "522460000000")

app = FastAPI(title="Tlaltelulco Limpio")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tlaltelulco Limpio | Reporte ciudadano</title>
<style>
:root{font-family:Arial,sans-serif;color:#18251f;background:#f2f6f2}
*{box-sizing:border-box}body{margin:0}
header{background:#176b45;color:white;padding:28px 18px;text-align:center}
header h1{margin:0 0 8px;font-size:clamp(25px,5vw,36px)}
header p{margin:0;color:#e4f4e9}
main{max-width:680px;margin:28px auto;padding:0 16px 35px}
.card{background:white;border-radius:16px;padding:24px;box-shadow:0 5px 22px #163b2514}
.notice{background:#eaf5ed;border-left:4px solid #258653;padding:12px 14px;border-radius:7px;margin-bottom:20px;font-size:14px}
label{display:block;font-weight:700;margin:16px 0 7px}
input,textarea{width:100%;padding:13px;border:1px solid #cbd8ce;border-radius:9px;font:inherit;background:#fff}
textarea{min-height:90px;resize:vertical}
button{width:100%;border:0;border-radius:9px;padding:15px;background:#18864f;color:white;font-size:16px;font-weight:700;margin-top:20px;cursor:pointer}
button:disabled{opacity:.6;cursor:wait}
.small{font-size:13px;color:#5b6c60;line-height:1.5}
#status{margin-top:15px;line-height:1.5;overflow-wrap:anywhere}
footer{text-align:center;color:#718078;font-size:12px;padding:15px}
</style>
</head>
<body>
<header><h1>🌱 Tlaltelulco Limpio</h1>
<p>Reporte ciudadano de acumulación de basura</p></header>
<main><section class="card">
<div class="notice"><b>Zona de cobertura:</b> La Magdalena Tlaltelulco, Tlaxcala.<br>
Ayúdanos a mantener limpias nuestras calles reportando puntos con basura.</div>
<form id="reportForm">
<label for="calle">Calle o colonia *</label>
<input id="calle" name="calle" placeholder="Ej. Avenida San Mauro" required>
<label for="referencia">Punto de referencia *</label>
<input id="referencia" name="referencia" placeholder="Ej. Frente a la tienda o cerca del parque" required>
<label for="descripcion">Descripción del problema</label>
<textarea id="descripcion" name="descripcion" placeholder="Describe dónde y qué tipo de basura hay..."></textarea>
<label for="foto">Fotografía (opcional)</label>
<input id="foto" name="foto" type="file" accept="image/*">
<p class="small">Si autorizas el acceso a la ubicación, el reporte incluirá las coordenadas de tu dispositivo.</p>
<input type="hidden" id="latitud" name="latitud">
<input type="hidden" id="longitud" name="longitud">
<button id="send" type="submit">Enviar reporte por WhatsApp</button>
</form>
<div id="status" role="status"></div>
</section></main>
<footer>Servicios Municipales · La Magdalena Tlaltelulco, Tlaxcala</footer>
<script>
const form=document.getElementById('reportForm');
const statusBox=document.getElementById('status');
form.addEventListener('submit', async (event)=>{
 event.preventDefault();
 const button=document.getElementById('send');
 button.disabled=true; button.textContent='Preparando reporte...';
 const sendReport=()=>{
   const data=new FormData(form);
   const calle=data.get('calle').trim(), referencia=data.get('referencia').trim();
   const descripcion=data.get('descripcion').trim() || 'Sin detalles adicionales';
   const lat=data.get('latitud'), lon=data.get('longitud');
   let message=`NUEVO REPORTE DE BASURA\\n\\nMunicipio: La Magdalena Tlaltelulco\\nCalle / Colonia: ${calle}\\nReferencias: ${referencia}\\nDetalles: ${descripcion}`;
   if(lat && lon) message+=`\\nUbicación: https://maps.google.com/?q=${lat},${lon}`;
   const photo=data.get('foto');
   if(photo && photo.size) message+='\\nSe seleccionó una fotografía. Adjuntarla manualmente en WhatsApp.';
   const phone='__PHONE__';
   const url=`https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
   statusBox.innerHTML='Se abrirá WhatsApp con el texto del reporte. Si seleccionaste una foto, tendrás que adjuntarla manualmente. Si WhatsApp no abre, <a target="_blank" rel="noopener" href="'+url+'">pulsa aquí</a>.';
   window.open(url,'_blank','noopener');
   button.disabled=false; button.textContent='Enviar reporte por WhatsApp';
 };
 if(navigator.geolocation){
   navigator.geolocation.getCurrentPosition(pos=>{
     document.getElementById('latitud').value=pos.coords.latitude;
     document.getElementById('longitud').value=pos.coords.longitude;
     sendReport();
   },()=>sendReport(),{timeout:5000});
 }else sendReport();
});
</script>
</body></html>"""
PAGE = PAGE.replace("__PHONE__", WHATSAPP_NUMBER)

@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE

@app.get("/health")
async def health():
    return {"status": "ok", "app": "Tlaltelulco Limpio"}
