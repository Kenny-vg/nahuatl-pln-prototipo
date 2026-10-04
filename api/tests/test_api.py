"""Pruebas de contrato con un servicio controlado, sin afirmar calidad del modelo."""

import pytest
from fastapi.testclient import TestClient

from api.main import crear_app
from api.servicio import ModeloNoDisponible


class ServicioControlado:
    def __init__(self, listo=True, encontrada=True, falla=False):
        self.listo, self.encontrada, self.falla = listo, encontrada, falla
        self.cargas = 0
        self.consultas = []

    def cargar(self):
        self.cargas += 1

    def consultar(self, texto):
        self.consultas.append(texto)
        if not self.listo:
            raise ModeloNoDisponible()
        if self.falla:
            raise RuntimeError("ruta-interna-secreta")
        return {
            "resultado": "respuesta controlada" if self.encontrada else "No encontré esa frase",
            "encontrada": self.encontrada,
            "traduccion": "respuesta controlada" if self.encontrada else None,
            "frase_encontrada": "Hola amigo" if self.encontrada else None,
            "similitud": 0.876,
            "traduccion_literal": "literal controlada",
            "desconocidas": [],
            "palabras": [{"esp": "hola", "candidatas": [{"nah": "token", "prob": 0.7}]}],
        }


@pytest.mark.parametrize("cuerpo", [
    {}, {"texto": None}, {"texto": 23}, {"texto": True}, {"texto": []},
    {"texto": {}}, {"texto": ""}, {"texto": "  \n "}, {"texto": "¿?! 💧"},
    {"texto": "x" * 301}, [], None,
])
def test_validacion(cuerpo):
    servicio = ServicioControlado()
    with TestClient(crear_app(servicio)) as cliente:
        respuesta = cliente.post("/consultar", json=cuerpo)
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["codigo"] == "TEXTO_INVALIDO"
    assert servicio.consultas == []


def test_json_malformado():
    with TestClient(crear_app(ServicioControlado())) as cliente:
        respuesta = cliente.post("/consultar", content='{', headers={"Content-Type": "application/json"})
    assert respuesta.status_code == 422


@pytest.mark.parametrize("encontrada", [True, False])
def test_contrato_y_sin_coincidencia(encontrada):
    servicio = ServicioControlado(encontrada=encontrada)
    with TestClient(crear_app(servicio)) as cliente:
        assert cliente.get("/salud").status_code == 200
        respuesta = cliente.post("/consultar", json={"texto": "  Hola amigo  "})
        assert cliente.post("/consultar", json={"texto": "x" * 300}).status_code == 200
    datos = respuesta.json()
    assert respuesta.status_code == 200
    assert set(datos) == {"resultado", "encontrada", "traduccion", "frase_encontrada", "similitud", "palabras", "traduccion_literal", "desconocidas"}
    assert datos["traduccion_literal"] == "literal controlada"
    assert datos["desconocidas"] == []
    assert datos["encontrada"] is encontrada
    assert datos["similitud"] == 0.876
    assert datos["palabras"][0]["candidatas"][0]["prob"] == 0.7
    if not encontrada:
        assert datos["resultado"] == "No encontré esa frase"
        assert datos["traduccion"] is None
    assert servicio.consultas[0] == "Hola amigo"
    assert servicio.cargas == 1


def test_no_disponible():
    with TestClient(crear_app(ServicioControlado(listo=False))) as cliente:
        assert cliente.get("/salud").status_code == 503
        assert cliente.post("/consultar", json={"texto": "hola"}).status_code == 503


def test_error_interno_sin_traza():
    with TestClient(crear_app(ServicioControlado(falla=True)), raise_server_exceptions=False) as cliente:
        respuesta = cliente.post("/consultar", json={"texto": "hola"})
    assert respuesta.status_code == 500
    assert "ruta-interna-secreta" not in respuesta.text


def test_web_mismo_origen():
    with TestClient(crear_app(ServicioControlado())) as cliente:
        respuesta = cliente.get("/web/")
        assert respuesta.status_code == 200
        assert 'id="inputText"' in respuesta.text
        assert cliente.get("/web/script.js").status_code == 200
        assert cliente.get("/web/styles.css").status_code == 200


def test_raiz_redirige_a_web():
    with TestClient(crear_app(ServicioControlado())) as cliente:
        respuesta = cliente.get("/", follow_redirects=False)
        assert respuesta.status_code == 307
        assert respuesta.headers["location"] == "/web/"
