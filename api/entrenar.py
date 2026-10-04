"""Entrenamiento manual: reutiliza IBM Model 1 y guarda solo dentro de api/."""

from api.config import RAIZ_PROYECTO
from modelo.entrenar import cargar_pares, entrenar_ibm1, guardar_tabla, tabla_a_dict


def main():
    """Entrena con el 80 % y diez vueltas, sin sobrescribir un artefacto existente."""
    destino = RAIZ_PROYECTO / "api" / "artefactos" / "tabla.json"
    if destino.exists():
        raise SystemExit("Ya existe api/artefactos/tabla.json; no se sobrescribió.")
    pares = cargar_pares(RAIZ_PROYECTO / "datos" / "train_80%.csv")
    if not pares:
        raise SystemExit("No hay pares válidos para entrenar.")
    print(f"Pares cargados: {len(pares)} | iteraciones: 10", flush=True)
    try:
        tabla = tabla_a_dict(entrenar_ibm1(pares, iteraciones=10))
    except MemoryError:
        raise SystemExit(
            "Memoria insuficiente para entrenar el corpus completo. No se guardó "
            "ninguna tabla. Libera memoria o ejecuta este comando en otro equipo."
        ) from None
    if not tabla:
        raise SystemExit("El entrenamiento no produjo asociaciones.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    guardar_tabla(tabla, ruta=destino)
    print(f"Palabras aprendidas: {len(tabla)} | guardado en {destino}", flush=True)


if __name__ == "__main__":
    main()
