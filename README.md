# Tlaltelulco Limpio (versión web)

## Probar en tu computadora
1. Instala Python 3.10 o superior.
2. Abre PowerShell dentro de esta carpeta.
3. Ejecuta:
   ```powershell
   py -m pip install -r requirements.txt
   py -m uvicorn main:app --reload
   ```
4. Abre http://127.0.0.1:8000

## Publicar gratis con GitHub y Render
1. Crea un repositorio en GitHub y sube el contenido de esta carpeta.
2. Entra a https://render.com y crea una cuenta.
3. Selecciona **New + > Web Service** y conecta el repositorio.
4. Render detectará `render.yaml`; confirma la creación.
5. Cuando termine el despliegue, Render mostrará el enlace público.

## IMPORTANTE: número de WhatsApp
El proyecto conserva el número provisional que estaba en tu aplicación original (`522460000000`).
Antes de publicar, reemplázalo en `main.py` por el número real del área que recibirá los reportes, con código de país y solo dígitos. También puedes configurar la variable `WHATSAPP_NUMBER` en Render.

## Funcionamiento
La página abre WhatsApp con calle, referencia, descripción y ubicación GPS si el usuario autoriza el permiso.
La fotografía se puede seleccionar en la página, pero WhatsApp no permite adjuntarla automáticamente desde un enlace web: el usuario tendrá que agregarla manualmente en el chat.
