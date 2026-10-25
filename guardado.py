"""
guardado.py — Leer y escribir JSON de forma segura (reutilizado de las criaturas).

Lo usan el entrenamiento, los experimentos y las grabaciones, por eso vive en
un módulo común.
"""

import json
import os


def guardar_json(ruta, datos):
    """
    GUARDADO ATÓMICO: primero escribimos en un archivo temporal y luego lo
    renombramos. Si el programa se interrumpe a mitad de la escritura, el
    archivo original sigue intacto. os.replace es atómico.
    """
    temporal = str(ruta) + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    os.replace(temporal, ruta)


def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)
