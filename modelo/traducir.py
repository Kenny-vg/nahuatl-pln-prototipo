"""Función principal del modelo traducir(frase) une las dos partes:
1) el buscador de frases (respuesta de la frase completa más parecida)
2) la tabla aprendida (palabras candidatas para cada palabra de la frase) """

import json
import sys
import pandas as pd

from modelo.buscador import buscar, construir_indice
from modelo.limpiar import limpiar

RUTA_TABLA = "modelo/tabla.json"
RUTA_PARES = "datos/train_80%.csv"
# Partículas ultra-frecuentes: salen en casi todo y tapan las palabras
# con significado. Solo se ignoran al elegir la literal, nada se borra.
# ca es la 11a palabra más frecuente del corpus (partícula enfática,
# como in/yn/on); sin filtrarla el modelo adivina "corazón"->ca.
RUIDO = {"in", "yn", "on", "ca"}
# La ganadora debe superar a la 2da con significado por este factor.
# Así la regla se adapta sola: si el modelo está seguro pasa, si está
# parejo (todo ~0.03-0.05) dice "no sé" en vez de afirmar algo dudoso.
# Calibrado en test_20%: 1.5->56.2% responde/40.6% acierta; 1.3->68.7%/38.5%
# (neta 22.8%->26.5%). 1.3 desbloquea casos dialectales (dias: tonajli/tonaltin
# ratio 1.37) con pérdida mínima de precisión.
MARGEN = 1.3
# Piso para no aceptar migajas cuando casi no hay datos de esa palabra.
PROB_PISO = 0.01
_modelo = {} #guarda lo cargado para no leer los archivos en cada consulta

def cargar_modelo(ruta_tabla=RUTA_TABLA, ruta_pares=RUTA_PARES,
                    col_esp="espanol", col_nah="nahuatl"):
    """Carga la tabla entrenada y arma el indice del buscador (una sola vez)"""
    if not _modelo:
        with open(ruta_tabla, encoding="utf-8") as f:
            _modelo["tabla"] = json.load(f)
            df = pd.read_csv(ruta_pares)
            # El train.csv trae sp/nah: se renombra por dentro, el archivo no se toca.
            df = df.rename(columns={"sp": "espanol", "nah": "nahuatl"})
            df = df.dropna(subset=[col_esp, col_nah])
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
        "palabras": [ {"esp": "hola", "candidatas": [{"nah": "tok1", "prob": 0.9}]} ]
    }
    Regla anti-invención: aunque el parecido pase el umbral, solo se acepta
    la frase si contiene TODAS las palabras de la entrada. Si falta una,
    es como si no se hubiera encontrado nada (encontrada=False).
    "No encontrada" se lee como encontrada=False y/o candidatas vacías.
    Además devuelve traduccion_literal: une la mejor candidata CON SIGNIFICADO
    de cada palabra pedida (una por una, nada de más). Se saltan las partículas
    de RUIDO y la ganadora debe superar a la 2da por MARGEN; si alguna palabra
    no cumple, la literal es None y esa palabra sale en desconocidas.
    La literal sale en orden español y es orientativa palabra por palabra.
    """

    m = cargar_modelo()
    posicion, similitud = buscar(frase, m["vectorizador"], m["matriz"], umbral)
    if posicion is not None:
        # Cobertura total: la frase hallada debe tener TODAS las palabras
        # de la entrada. Se limpia igual para comparar justo.
        pedidas = set(limpiar(frase))
        halladas = set(limpiar(m["frases_es"][posicion]))
        if not pedidas <= halladas:
            posicion = None  # parece parecida, pero no es lo pedido
    palabras = []
    for p in limpiar(frase):
        opciones = sorted(m["tabla"].get(p,{}).items(), key=lambda x: -x[1])[:max_candidatas]
        palabras.append({"esp": p, "candidatas": [{"nah": n, "prob": pr} for n, pr in opciones]})
    # Literal: la mejor candidata con significado de cada palabra.
    # Se busca en TODA la tabla (no solo el top 3 mostrado), saltando RUIDO.
    # Gana solo si supera a la 2da por MARGEN; si no, no se adivina.
    elegidas = []
    desconocidas = []
    for p in limpiar(frase):
        todas = sorted(m["tabla"].get(p, {}).items(), key=lambda x: -x[1])
        limpias = [(nah, prob) for nah, prob in todas
                   if nah not in RUIDO and prob >= PROB_PISO]
        buena = None
        if len(limpias) == 1:
            buena = limpias[0][0]
        elif len(limpias) >= 2 and limpias[0][1] >= MARGEN * limpias[1][1]:
            buena = limpias[0][0]
        if buena is None:
            desconocidas.append(p)
        else:
            elegidas.append(buena)
    if desconocidas or not elegidas:
        literal = None
    else:
        literal = " ".join(elegidas)
    return {
        "encontrada": posicion is not None,
        "traduccion": m["frases_nah"][posicion] if posicion is not None else None,
        "frase_encontrada": m["frases_es"][posicion] if posicion is not None else None,
        "similitud": round(similitud, 3),
        "traduccion_literal": literal,
        "desconocidas": desconocidas,
        "palabras": palabras,
    } 

if __name__ == "__main__":
    entrada = " ".join(sys.argv[1:]) or "hola amigo"
    print(json.dumps(traducir(entrada), ensure_ascii=False, indent=2))
