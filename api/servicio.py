"""Carga una vez y protege el estado global del modelo ante cargas incompletas."""

import importlib
import json
import math
from threading import Lock

from api.config import Configuracion, MAX_CANDIDATAS, UMBRAL


class ModeloNoDisponible(Exception):
    """La consulta no puede ejecutarse; no equivale a una frase desconocida."""


class ServicioModelo:
    """Una instancia de producción por proceso; no reintenta cargas por petición."""

    def __init__(self, configuracion: Configuracion):
        self.configuracion = configuracion
        self.listo = False
        self._carga_intentada = False
        self._bloqueo = Lock()
        self._modulo = None

    def cargar(self):
        """Valida recursos y precarga el caché que traducir() reutiliza después.

        Un fallo deja el servicio cerrado a consultas, aunque el cargador original
        haya escrito parcialmente su diccionario. Se requiere reiniciar para
        volver a cargar después de corregir los recursos.
        """
        with self._bloqueo:
            if self._carga_intentada:
                return
            self._carga_intentada = True
            try:
                with self.configuracion.ruta_tabla.open(encoding="utf-8") as archivo:
                    tabla = json.load(archivo)
                self._validar_tabla(tabla)
                if not self.configuracion.ruta_corpus.is_file():
                    raise ValueError("Falta el corpus")

                self._modulo = importlib.import_module("modelo.traducir")
                # Un caché previo podría pertenecer a otras rutas o estar incompleto.
                # No lo sustituimos ni lo reutilizamos silenciosamente.
                if self._modulo._modelo:
                    raise ValueError("El modelo ya tenía estado previo")
                modelo = self._modulo.cargar_modelo(
                    ruta_tabla=str(self.configuracion.ruta_tabla),
                    ruta_pares=str(self.configuracion.ruta_corpus),
                )
                self._validar_modelo(modelo)
                self.listo = True
            except Exception:
                # Ni rutas ni trazas salen al cliente. Nunca entrenamos como fallback.
                self.listo = False

    @staticmethod
    def _validar_tabla(tabla):
        """Comprueba el formato IBM {español: {náhuatl: probabilidad}}."""
        if not isinstance(tabla, dict) or not tabla:
            raise ValueError("Tabla vacía o incompatible")
        for palabra, candidatas in tabla.items():
            if not isinstance(palabra, str) or not palabra.strip():
                raise ValueError("Palabra inválida")
            if not isinstance(candidatas, dict) or not candidatas:
                raise ValueError("Candidatas inválidas")
            for nah, probabilidad in candidatas.items():
                if (not isinstance(nah, str) or not nah.strip()
                        or type(probabilidad) not in (int, float)
                        or not math.isfinite(probabilidad)
                        or not 0 <= probabilidad <= 1):
                    raise ValueError("Probabilidad o candidata inválida")

    def _validar_modelo(self, modelo):
        """La tabla, los pares y las filas del índice deben estar completos."""
        self._validar_tabla(modelo["tabla"])
        frases_es, frases_nah = modelo["frases_es"], modelo["frases_nah"]
        if not frases_es or len(frases_es) != len(frases_nah):
            raise ValueError("Corpus vacío o desalineado")
        if any(not isinstance(frase, str) or not frase.strip()
               for frase in [*frases_es, *frases_nah]):
            raise ValueError("Corpus con frases vacías")
        matriz = modelo["matriz"]
        vocabulario = modelo["vectorizador"].vocabulary_
        if matriz.shape != (len(frases_es), len(vocabulario)) or not vocabulario:
            raise ValueError("Índice incompleto")
        if not all(math.isfinite(valor) for valor in matriz.data):
            raise ValueError("Índice inválido")

    def consultar(self, texto: str) -> dict:
        """Reutiliza la recuperación y la literal calculadas por traducir()."""
        if not self.listo:
            raise ModeloNoDisponible()
        respuesta = self._modulo.traducir(
            texto, umbral=UMBRAL, max_candidatas=MAX_CANDIDATAS
        )
        # La literal es orientativa y tiene su propio campo. No sustituye una
        # coincidencia del corpus ni convierte encontrada=False en True.
        campos = ("encontrada", "traduccion", "frase_encontrada", "similitud",
                  "palabras", "traduccion_literal", "desconocidas")
        datos = {campo: respuesta[campo] for campo in campos}
        datos["resultado"] = (
            datos["traduccion"] if datos["encontrada"] else "No encontré esa frase"
        )
        return datos
