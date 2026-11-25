
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from detector import detectar_basura
from starlette.concurrency import run_in_threadpool




BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "reportes.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Tlaltelulco Limpio - Reportes ciudadanos")

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads"
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                calle TEXT NOT NULL,
                referencia TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                latitud REAL,
                longitud REAL,
                foto TEXT
            )
        """)


inicializar_db()


@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.post("/api/validar-foto")
async def validar_foto(foto: UploadFile = File(...)):

    extension = Path(foto.filename or "").suffix.lower()

    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(
            status_code=400,
            detail="Formato de imagen no permitido."
        )

    contenido = await foto.read(8 * 1024 * 1024 + 1)

    if len(contenido) > 8 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="La imagen supera los 8 MB."
        )

    try:
        analisis = await run_in_threadpool(
            detectar_basura, contenido
        )

        return {
            "aceptada": analisis["aceptada"],
            "basura": analisis["basura"],
            "no_basura": analisis["no_basura"]
        }

    except (OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="No se pudo leer la fotografia."
        )

    except Exception as error:
        print(f"Error de IA: {error}", flush=True)

        raise HTTPException(
            status_code=503,
            detail="No se pudo analizar la fotografia."
        )



@app.post("/api/reportar")
async def reportar_basura(
    calle: str = Form(...),
    referencia: str = Form(...),
    descripcion: str = Form(...),
    latitud: str = Form(""),
    longitud: str = Form(""),
    foto: UploadFile | None = File(None)
):

    calle = calle.strip()
    referencia = referencia.strip()
    descripcion = descripcion.strip()

    if not calle or not referencia or not descripcion:
        raise HTTPException(
            status_code=400,
            detail="Completa calle, referencias y descripción."
        )

    try:
        lat = float(latitud) if latitud.strip() else None
        lon = float(longitud) if longitud.strip() else None
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Las coordenadas no son válidas."
        )

    # Fotografia obligatoria
    if not foto or not foto.filename:
        raise HTTPException(
            status_code=400,
            detail="Debes seleccionar una fotografía de la basura."
        )

    extension = Path(foto.filename).suffix.lower()

    permitidas = {".jpg", ".jpeg", ".png", ".webp"}

    if extension not in permitidas:
        raise HTTPException(
            status_code=400,
            detail="La fotografía debe ser JPG, PNG o WEBP."
        )

    contenido = await foto.read(8 * 1024 * 1024 + 1)

    if len(contenido) > 8 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="La fotografía no debe superar 8 MB."
        )

    # Analizar fotografia con inteligencia artificial
    try:
        analisis = await run_in_threadpool(
            detectar_basura,
            contenido
        )

    except (OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="No se pudo leer la fotografía."
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="El detector de basura no está disponible."
        )

    # Rechazar fotografias incorrectas
    if not analisis["aceptada"]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Imagen rechazada. La inteligencia artificial "
                "no pudo confirmar basura acumulada en la calle. "
                f"Confianza: {analisis['basura']}%. "
                "Selecciona otra fotografía."
            )
        )

    # Guardar fotografia aceptada
    foto_nombre = f"{uuid.uuid4().hex}{extension}"

    (UPLOAD_DIR / foto_nombre).write_bytes(contenido)

    fecha = datetime.now(
        timezone.utc
    ).astimezone().isoformat(timespec="seconds")

    with conectar() as conn:
        cursor = conn.execute("""
            INSERT INTO reportes (
                fecha, calle, referencia,
                descripcion, latitud, longitud, foto
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha,
            calle,
            referencia,
            descripcion,
            lat,
            lon,
            foto_nombre
        ))

        reporte_id = cursor.lastrowid

    return JSONResponse({
        "ok": True,
        "id": reporte_id,
        "confianza": analisis["basura"],
        "mensaje": (
            f"Basura detectada con {analisis['basura']}% "
            f"de confianza. Reporte #{reporte_id} guardado."
        )
    })


@app.get("/api/reportes")
async def listar_reportes():

    with conectar() as conn:
        rows = conn.execute("""
            SELECT id, fecha, calle, referencia,
            descripcion, latitud, longitud, foto
            FROM reportes
            ORDER BY id DESC LIMIT 100
        """).fetchall()

    return [dict(r) for r in rows]

