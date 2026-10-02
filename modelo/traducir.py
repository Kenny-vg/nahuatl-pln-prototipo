"""Función principal del modelo traducir(frase) une las dos partes:
1) el buscador de frases (respuesta de la frase completa más parecida)
2) la tabla aprendida (palabras candidatas para cada palabra de la frase) """

import json
import sys
import pandas as pd

from modelo.buscador import buscar, construir_indice
from modelo.limpiar import limpiar

RUTA_TABLA = "modelo/tabla.json"
RUTA_PARES = "datos/pares.ejemplo.csv"
_modelo = {} #guarda lo cargado para no leer los archivos en cada consulta

def cargar_modelo(ruta_tabla=RUTA_TABLA, ruta_pares=RUTA_PARES,
                    col_esp="espanol", col_nah="nahuatl"):
    """Carga la tabla entrenada y arma el indice del buscador (una sola vez)"""
    if not _modelo:
        with open(ruta_tabla, encoding="utf-8") as f:
            _modelo["tabla"] = json.load(f)
            df = pd.read_csv(ruta_pares).dropna(subset=[col_esp, col_nah])
            _modelo["frases_es"] = df[col_esp].astype(str).tolist()
            _modelo["frases_nah"] = df[col_nah].astype(str).tolist()
            _modelo["vectorizador"], _modelo["matriz"] = construir_indice(_modelo["frases_es"])
    return _modelo

def traducir(frase, umbral=0.5, max_candidatas=3):
    """Recibe una frase en español y devuelve un diccionario con el resultado.
    {
        "encontrada": True/False,          # ¿hubo una frase conocida parecida?
        "traduccion": "..." o None,        # traducción de esa frase
        "frase_encontrada": "..." o None,  # cuál frase conocida se usó
        "similitud": 0.0 a 1.0,            # qué tan parecida fue
        "palabras": [ {"esp": "hola", "candidatas": [{"nah": "niltze", "prob": 0.9}]} ]
    } """

    m = cargar_modelo()
    posicion, similitud = buscar(frase, m["vectorizador"], m["matriz"], umbral)
    palabras = []
    for p in limpiar(frase):
        opciones = sorted(m["tabla"].get(p,{}).items(), key=lambda x: -x[1])[:max_candidatas]
        palabras.append({"esp": p, "candidatas": [{"nah": n, "prob": pr} for n, pr in opciones]})
    return {
        "encontrada": posicion is not None,
        "traduccion": m["frases_nah"][posicion] if posicion is not None else None,
        "frase_encontrada": m["frases_es"][posicion] if posicion is not None else None,
        "similitud": round(similitud, 3),
        "palabras": palabras,
    } 

if __name__ == "__main__":
    entrada = " ".join(sys.argv[1:]) or "hola amigo"
    print(json.dumps(traducir(entrada), ensure_ascii=False, indent=2))
