"""Pruebas automáticas del modelo (pytest).

Antes hay que haber entrenado el modelo (existe modelo/tabla.json).
Las pruebas revisan el COMPORTAMIENTO esperado (no inventar, no cerrarse,
tratar igual mayúsculas y acentos), no traducciones concretas, para que sigan
sirviendo aunque cambien los datos.
"""
import pytest

from modelo.limpiar import limpiar
from modelo.traducir import traducir, cargar_modelo

CLAVES = {"encontrada", "traduccion", "frase_encontrada", "similitud",
          "traduccion_literal", "desconocidas", "palabras"}


@pytest.fixture(scope="module", autouse=True)
def modelo_listo():
    """Carga el modelo una vez; si falta el entrenamiento, se omiten las pruebas."""
    try:
        cargar_modelo()
    except FileNotFoundError:
        pytest.skip("Falta modelo/tabla.json: entrena el modelo primero")


def test_limpiar_quita_mayusculas_acentos_y_signos():
    assert limpiar("¡BUENOS DÍAS!") == ["buenos", "dias"]


@pytest.mark.parametrize("a, b", [
    ("BUENOS DÍAS", "buenos dias"),
    ("¡Gracias!", "gracias"),
    ("  agua   y   maíz  ", "agua y maiz"),
])
def test_normalizacion_da_el_mismo_resultado(a, b):
    assert traducir(a) == traducir(b)


@pytest.mark.parametrize("texto", ["computadora", "asdfgh", "good morning", "12345"])
def test_palabras_desconocidas_no_se_inventan(texto):
    r = traducir(texto)
    assert r["encontrada"] is False
    assert r["traduccion_literal"] is None
    assert r["desconocidas"], "debe listar las palabras que no conoce"


def test_frase_con_palabra_desconocida_no_devuelve_frase_ajena():
    r = traducir("agua y computadora")
    assert r["encontrada"] is False
    assert r["traduccion_literal"] is None
    assert "computadora" in r["desconocidas"]


@pytest.mark.parametrize("texto", [
    "", "   ", "😀", "a" * 301, "<script>alert(1)</script>", "12345",
])
def test_entradas_raras_no_truenan(texto):
    r = traducir(texto)
    assert CLAVES <= set(r)


@pytest.mark.parametrize("texto", [
    "buenos días", "hola amigo", "gracias", "agua y maíz", "flor y corazón",
    "ya esta aqui el agua", "yo tengo un lapiz",
])
def test_frase_encontrada_contiene_todas_las_palabras_pedidas(texto):
    r = traducir(texto)
    if r["encontrada"]:
        assert set(limpiar(texto)) <= set(limpiar(r["frase_encontrada"]))


@pytest.mark.parametrize("texto", ["agua", "maiz", "agua y maiz"])
def test_literal_tiene_una_palabra_por_cada_palabra_pedida(texto):
    r = traducir(texto)
    if r["traduccion_literal"] is not None:
        assert len(r["traduccion_literal"].split()) == len(limpiar(texto))
        assert r["desconocidas"] == []


def test_frase_exacta_conocida_se_encuentra():
    r = traducir("ya esta aqui el agua")
    assert r["encontrada"] is True
    assert r["similitud"] >= 0.99
