"""Limpieza de texto (preprocesamiento).
Convierte una frase en una lista de palabras "limpias" para que el programa
compare texto de forma justa"""
import re
import unicodedata


def quitar_acentos(texto):
    """Quita acentos y marcas"""
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def limpiar(frase):
    """Recibe una frase y devuelve una lista de palabras limpias.
    Pasos: 1) minúsculas, 2) sin acentos, 3) sin signos, 4) separar en palabras. """
    frase = frase.lower()
    frase = quitar_acentos(frase)
    frase = re.sub(r"[^a-z0-9\s]", " ", frase)
    return frase.split()