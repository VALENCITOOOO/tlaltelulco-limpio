
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO
from threading import Lock
import numpy as np

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite.python.interpreter import Interpreter

BASE = Path(__file__).resolve().parent

MODELO = BASE / "modelo_basura.tflite"

interpreter = Interpreter(
    model_path=str(MODELO),
    num_threads=1
)

interpreter.allocate_tensors()

entrada = interpreter.get_input_details()[0]
salida = interpreter.get_output_details()[0]

bloqueo = Lock()

UMBRAL = 0.85


def detectar_basura(contenido):

    with Image.open(BytesIO(contenido)) as imagen:
        imagen = ImageOps.exif_transpose(imagen)
        imagen = imagen.convert("RGB")
        imagen = imagen.resize(
            (224, 224),
            Image.Resampling.BILINEAR
        )

        datos = np.array(imagen, dtype=np.float32)

    datos = np.expand_dims(datos, axis=0)

    with bloqueo:
        interpreter.set_tensor(
            entrada["index"],
            datos
        )

        interpreter.invoke()

        prediccion = interpreter.get_tensor(
            salida["index"]
        )[0]

   
    basura = float(prediccion[0])
    no_basura = float(prediccion[1])

    print("\n========== ANALISIS DE IA ==========")
    print(f"Basura: {basura * 100:.2f}%")
    print(f"No basura: {no_basura * 100:.2f}%")
    print(f"Imagen aceptada: {basura >= UMBRAL}")
    print("====================================\n", flush=True)

    return {
        "aceptada": basura >= UMBRAL,
        "basura": round(basura * 100, 2),
        "no_basura": round(no_basura * 100, 2)
    }
