# Punto de entrada de la API en Vercel: expone la app Flask de src/app.py como funcion serverless.
# vercel.json redirige /api/* aqui; Flask recibe la ruta original y la resuelve con el blueprint de src/api.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from app import app  # noqa: E402,F401
