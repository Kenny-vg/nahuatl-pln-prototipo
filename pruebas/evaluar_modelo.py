"""Evaluación del modelo para el Informe de QA.

Hace dos cosas:
1) Corre los casos de prueba y guarda los resultados en pruebas/resultados_casos.csv.
2) Mide, con las frases apartadas (RUTA_TEST), cuántas palabras responde
   la literal y cuántas veces la respuesta aparece en la frase de referencia.
"""
import csv
import pandas as pd

from modelo.traducir import traducir, cargar_modelo, RUIDO, MARGEN, PROB_PISO, PISO_SOMBRA
from modelo.limpiar import limpiar

RUTA_TEST = "datos/test_20%.csv"   # cambia el nombre si tu archivo se llama distinto
RUTA_SALIDA = "pruebas/resultados_casos.csv"

CASOS = [
    ("CP-N01", "Buenos días"), ("CP-N02", "Hola amigo"), ("CP-N03", "Gracias"),
    ("CP-N04", "Agua y maíz"), ("CP-N05", "Flor y corazón"),
    ("CP-M01", "BUENOS DÍAS"), ("CP-M02", "buenos dias"), ("CP-M03", "¡Gracias!"),
    ("CP-M04", "  agua   y   maíz  "),
    ("CP-F01", "computadora"), ("CP-F02", "agua y computadora"), ("CP-F03", "asdfgh"),
    ("CP-F04", "computadora teclado impresora"),
    ("CP-E01", "gracais"), ("CP-E02", "buenso dias"), ("CP-E03", "aguaa"),
    ("CP-R01", ""), ("CP-R02", "   "), ("CP-R03", "12345"),
    ("CP-R04", "a" * 301), ("CP-R05", "good morning"), ("CP-R06", "😀"),
    ("CP-R07", "<script>alert(1)</script>"),
]


def correr_casos():
    """Corre cada caso y guarda el resultado en resultados_casos.csv."""
    with open(RUTA_SALIDA, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Entrada", "encontrada", "similitud", "frase_encontrada",
                    "traduccion_literal", "desconocidas"])
        for id_, entrada in CASOS:
            try:
                r = traducir(entrada)
                w.writerow([id_, entrada[:40], r["encontrada"], r["similitud"],
                            r["frase_encontrada"], r["traduccion_literal"],
                            ", ".join(r["desconocidas"])])
            except Exception as e:  # un caso que truena es un hallazgo
                w.writerow([id_, entrada[:40], "ERROR", "", "", "", f"{type(e).__name__}: {e}"])
    print(f"Casos guardados en {RUTA_SALIDA}")


def elegir(candidatas):
    """Misma regla que traducir(): quita ruido y piso, exige el margen, y
    veta si una partícula débil ganadora hace sombra a una contendiente
    cercana (ver PISO_SOMBRA en traducir)."""
    todas = sorted(candidatas.items(), key=lambda x: -x[1])
    limpias = [(n, p) for n, p in todas if n not in RUIDO and p >= PROB_PISO]
    if todas and todas[0][0] in RUIDO and len(todas) >= 2:
        nah2, prob2 = todas[1]
        if nah2 not in RUIDO and prob2 >= PROB_PISO:
            if todas[0][1] < PISO_SOMBRA and todas[0][1] < MARGEN * prob2:
                return None
    if len(limpias) == 1:
        return limpias[0][0]
    if len(limpias) >= 2 and limpias[0][1] >= MARGEN * limpias[1][1]:
        return limpias[0][0]
    return None


def medir_palabras():
    """Mide respuesta y acierto por palabra con las frases apartadas."""
    tabla = cargar_modelo()["tabla"]
    df = pd.read_csv(RUTA_TEST).dropna(subset=["espanol", "nahuatl"])
    total = responde = acierta = 0
    for esp, nah in zip(df["espanol"], df["nahuatl"]):
        ref = set(limpiar(str(nah)))
        for palabra in limpiar(str(esp)):
            total += 1
            elegida = elegir(tabla.get(palabra, {}))
            if elegida:
                responde += 1
                acierta += elegida in ref
    print(f"Palabras evaluadas: {total}")
    print(f"Responde: {responde} ({100 * responde / total:.1f} %)")
    print(f"Acierta (aparece en la referencia): {acierta} ({100 * acierta / responde:.1f} % de las que responde)")
    print(f"Parámetros: MARGEN={MARGEN}, PROB_PISO={PROB_PISO}, RUIDO={sorted(RUIDO)}")


if __name__ == "__main__":
    correr_casos()
    medir_palabras()
