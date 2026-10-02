"""Entrenamiento del modelo: IBM Model 1.
Idea: si una palabra en español aparece en muchas frases junto con la misma
palabra en náhuatl, probablemente significan lo mismo. El programa lo aprende
contando y afinando una tabla de probabilidades en varias "vueltas"."""

import json
import sys
from collections import defaultdict
import pandas as pd

from modelo.limpiar import limpiar

RUTA_PARES = "datos/train.csv"
RUTA_TABLA = "modelo/tabla.json"

def cargar_pares(ruta_csv, col_esp="espanol", col_nah="nahuatl"):
    """Carga un CSV de pares de frases y devuelve una lista de tuplas (frase_esp, frase_nah)"""
    df = pd.read_csv(ruta_csv)
    # El train.csv trae sp/nah: se renombra por dentro, el archivo no se toca.
    df = df.rename(columns={"sp": "espanol", "nah": "nahuatl"})
    if col_esp not in df.columns or col_nah not in df.columns:
        raise ValueError(f"No encontré las columnas. El CSV tiene: {list(df.columns)}")
    df = df.dropna(subset=[col_esp, col_nah])
    pares = []
    for esp, nah in zip(df[col_esp], df[col_nah]):
        palabras_esp, palabras_nah = limpiar(str(esp)), limpiar(str(nah))
        if palabras_esp and palabras_nah:
            pares.append((palabras_esp, palabras_nah))
    return pares

def entrenar_ibm1(pares, iteraciones=5):
    """Entrena el modelo IBM Model 1 a partir de una lista de pares de frases."""
    vocab_nah = {n for _, palabras_nah in pares for n in palabras_nah}
    t = defaultdict(lambda:1.0 / len(vocab_nah)) #arranque: todo igual de probable

    for _ in range (iteraciones):
        conteo = defaultdict(float) #conteo de apariciones
        total = defaultdict(float) #total de apariciones por palabra en español
        for palabras_esp, palabras_nah in pares:
            esp_con_nulo = ["NULL"] + palabras_esp #NULL palabra sin pareja
            
            for n in palabras_nah:
                z = sum(t[(n,e)] for e in esp_con_nulo) #Paso E: suma para normalizar
                for e in esp_con_nulo:
                    parte = t[(n,e)] / z # La parte que le toca a 'e'
                    conteo[(n,e)] += parte
                    total[e] += parte
        for (n,e), c in conteo.items():
            t[(n,e)] = c / total[e] #Paso M: actualizar la probabilidad, nueva tabla
    return t


def tabla_a_dict(t, umbral=0.001):
    """Convierte la tabla a {esp: {nah: prob}} para guardarla en JSON.
    JSON no acepta claves con tuplas, y quitamos probabilidades muy pequeñas
    para que el archivo no pese demasiado.
    """
    tabla = defaultdict(dict)
    for (n,e), p in t.items():
        if e != "NULL" and p >= umbral:
            tabla[e][n] =round(p, 4)
    return dict(tabla)

def guardar_tabla(tabla, ruta=RUTA_TABLA):
    """Guarda la tabla de probabilidades en un archivo JSON"""
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(tabla, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_PARES
    vueltas = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    pares = cargar_pares(ruta)
    print(f"Pares cargados: {len(pares)} | vueltas: {vueltas}")
    tabla = tabla_a_dict(entrenar_ibm1(pares,vueltas))
    guardar_tabla(tabla)
    print(f"Palabras en español aprendidas: {len(tabla)} | tabla guardada en {RUTA_TABLA}")

