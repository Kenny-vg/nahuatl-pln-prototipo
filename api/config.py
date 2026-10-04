"""Rutas y decisiones del servidor, independientes del directorio de arranque."""

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
UMBRAL = 0.5
MAX_CANDIDATAS = 3


@dataclass(frozen=True)
class Configuracion:
    """Permite indicar otro JSON entrenado sin moverlo ni alterar el modelo."""

    ruta_tabla: Path
    ruta_corpus: Path = RAIZ_PROYECTO / "datos" / "train_80%.csv"

    @classmethod
    def desde_entorno(cls):
        """Las rutas relativas del artefacto se resuelven contra el proyecto."""
        ruta = Path(os.environ.get("NAHUATL_TABLA", "modelo/tabla.json"))
        if not ruta.is_absolute():
            ruta = RAIZ_PROYECTO / ruta
        corpus = Path(os.environ.get("NAHUATL_CORPUS", "datos/train_80%.csv"))
        if not corpus.is_absolute():
            corpus = RAIZ_PROYECTO / corpus
        return cls(ruta_tabla=ruta.resolve(), ruta_corpus=corpus.resolve())
