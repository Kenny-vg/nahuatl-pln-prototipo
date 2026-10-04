"""Prueba el adaptador y el algoritmo existente con un corpus pequeño artificial."""

import importlib
import json

import pytest
from fastapi.testclient import TestClient

from api.config import Configuracion, RAIZ_PROYECTO
from api.main import crear_app
from api.servicio import ModeloNoDisponible, ServicioModelo


@pytest.fixture
def modulo_limpio(monkeypatch):
    modulo = importlib.import_module("modelo.traducir")
    # Solo el estado en memoria de la prueba; nunca cambia archivos del modelo.
    monkeypatch.setattr(modulo, "_modelo", {})
    return modulo


@pytest.fixture
def recursos(tmp_path):
    tabla = tmp_path / "tabla_controlada.json"
    corpus = tmp_path / "corpus_controlado.csv"
    tabla.write_text(json.dumps({"hola": {"token_a": 0.8}, "amigo": {"token_b": 0.9}}), encoding="utf-8")
    corpus.write_text("sp,nah\nhola amigo,respuesta del corpus de prueba\nagua,otra respuesta\n", encoding="utf-8")
    return Configuracion(tabla, corpus)


def test_carga_unica_y_recuperacion_real_controlada(recursos, modulo_limpio, monkeypatch):
    servicio = ServicioModelo(recursos)
    original = modulo_limpio.cargar_modelo
    cargas = []

    def cargar(**kwargs):
        cargas.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(modulo_limpio, "cargar_modelo", cargar)
    servicio.cargar()
    servicio.cargar()
    assert servicio.listo
    assert len(cargas) == 1
    respuesta = servicio.consultar("hola amigo")
    assert respuesta["traduccion"] == "respuesta del corpus de prueba"
    assert respuesta["resultado"] == respuesta["traduccion"]
    assert respuesta["similitud"] == 1.0
    assert respuesta["traduccion_literal"] == "token_a token_b"
    assert respuesta["desconocidas"] == []
    assert len(modulo_limpio._modelo["tabla"]) == 2


@pytest.mark.parametrize("texto", ["desconocida", "hola desconocida"])
def test_rechazo_similitud_o_cobertura(recursos, modulo_limpio, texto):
    servicio = ServicioModelo(recursos)
    servicio.cargar()
    respuesta = servicio.consultar(texto)
    assert respuesta["encontrada"] is False
    assert respuesta["traduccion"] is None
    assert respuesta["resultado"] == "No encontré esa frase"
    if texto.startswith("hola"):
        assert respuesta["similitud"] >= 0.5
        assert respuesta["palabras"][0]["candidatas"]


@pytest.mark.parametrize("contenido", ['{', '{}', '[]', '{"hola": {"token": "0.5"}}', '{"hola": {"token": 2}}'])
def test_tabla_invalida(recursos, contenido):
    recursos.ruta_tabla.write_text(contenido, encoding="utf-8")
    servicio = ServicioModelo(recursos)
    servicio.cargar()
    assert not servicio.listo
    with pytest.raises(ModeloNoDisponible):
        servicio.consultar("hola")


def test_artefacto_ausente(tmp_path):
    servicio = ServicioModelo(Configuracion(tmp_path / "ausente.json"))
    with TestClient(crear_app(servicio)) as cliente:
        assert cliente.get("/salud").status_code == 503
        assert cliente.post("/consultar", json={"texto": "hola"}).status_code == 503
        assert cliente.post("/consultar", json={"texto": "!!!"}).status_code == 422
    assert not servicio.listo
    with pytest.raises(ModeloNoDisponible):
        servicio.consultar("hola")


def test_fallo_parcial_no_reintenta(recursos, modulo_limpio):
    recursos.ruta_corpus.write_text("columna_incorrecta\nvalor\n", encoding="utf-8")
    servicio = ServicioModelo(recursos)
    servicio.cargar()
    assert "tabla" in modulo_limpio._modelo
    assert not servicio.listo
    recursos.ruta_corpus.write_text("sp,nah\nhola,respuesta\n", encoding="utf-8")
    servicio.cargar()
    with pytest.raises(ModeloNoDisponible):
        servicio.consultar("hola")


def test_rutas_desde_proyecto(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NAHUATL_TABLA", "api/artefacto.json")
    monkeypatch.delenv("NAHUATL_CORPUS", raising=False)
    config = Configuracion.desde_entorno()
    assert config.ruta_tabla == RAIZ_PROYECTO / "api" / "artefacto.json"
    assert config.ruta_corpus == RAIZ_PROYECTO / "datos" / "train_80%.csv"
    monkeypatch.setenv("NAHUATL_CORPUS", "datos/mi_corpus.csv")
    config = Configuracion.desde_entorno()
    assert config.ruta_corpus == RAIZ_PROYECTO / "datos" / "mi_corpus.csv"


def test_seleccion_artefacto_local_y_prioridad_entorno(monkeypatch, tmp_path):
    import api.config as config

    monkeypatch.setattr(config, "RAIZ_PROYECTO", tmp_path)
    monkeypatch.delenv("NAHUATL_TABLA", raising=False)
    assert Configuracion.desde_entorno().ruta_tabla == tmp_path / "modelo" / "tabla.json"
    local = tmp_path / "api" / "artefactos" / "tabla.json"
    local.parent.mkdir(parents=True)
    local.write_text('{"prueba": {"token": 1}}', encoding="utf-8")
    assert Configuracion.desde_entorno().ruta_tabla == local
    monkeypatch.setenv("NAHUATL_TABLA", "otra.json")
    assert Configuracion.desde_entorno().ruta_tabla == tmp_path / "otra.json"


def test_parametros_y_literal_separada(recursos, modulo_limpio, monkeypatch):
    servicio = ServicioModelo(recursos)
    servicio.cargar()
    llamadas = []

    def traducir(texto, umbral, max_candidatas):
        llamadas.append((texto, umbral, max_candidatas))
        return {"encontrada": False, "traduccion": None, "frase_encontrada": None,
                "similitud": 0.8, "palabras": [], "traduccion_literal": "literal controlada",
                "desconocidas": []}

    monkeypatch.setattr(modulo_limpio, "traducir", traducir)
    respuesta = servicio.consultar("hola")
    assert llamadas == [("hola", 0.5, 3)]
    assert respuesta["resultado"] == "No encontré esa frase"
    assert respuesta["traduccion_literal"] == "literal controlada"


@pytest.mark.parametrize("contenido", ["sp,nah\n", "sp,nah\n!!!,respuesta\n", "sp,nah\nhola,   \n"])
def test_corpus_inutilizable(recursos, modulo_limpio, contenido):
    recursos.ruta_corpus.write_text(contenido, encoding="utf-8")
    servicio = ServicioModelo(recursos)
    servicio.cargar()
    assert not servicio.listo


def test_corpus_ausente(recursos, modulo_limpio):
    config = Configuracion(recursos.ruta_tabla, recursos.ruta_corpus.parent / "ausente.csv")
    servicio = ServicioModelo(config)
    servicio.cargar()
    assert not servicio.listo


def test_indice_incompleto(recursos, modulo_limpio, monkeypatch):
    original = modulo_limpio.cargar_modelo

    def cargar(**kwargs):
        modelo = original(**kwargs)
        modelo["matriz"] = modelo["matriz"][:1]
        return modelo

    monkeypatch.setattr(modulo_limpio, "cargar_modelo", cargar)
    servicio = ServicioModelo(recursos)
    servicio.cargar()
    assert not servicio.listo


@pytest.mark.parametrize("candidatas,literal,desconocidas", [
    ({"in": 0.99, "yn": 0.95, "on": 0.9, "token": 0.1}, "token", []),
    ({"token": 0.6, "otra": 0.3}, "token", []),
    ({"token": 0.45, "otra": 0.3}, "token", []),
    ({"token": 0.4, "otra": 0.3}, "token", []),
    ({"token": 0.38, "otra": 0.3}, None, ["hola"]),
    ({"token": 0.009}, None, ["hola"]),
    ({"token": 0.01}, "token", []),
])
def test_literal_respeta_reglas_del_modelo(recursos, modulo_limpio, candidatas, literal, desconocidas):
    recursos.ruta_tabla.write_text(json.dumps({"hola": candidatas}), encoding="utf-8")
    with TestClient(crear_app(ServicioModelo(recursos))) as cliente:
        respuesta = cliente.post("/consultar", json={"texto": "hola"})
    assert respuesta.status_code == 200
    assert respuesta.json()["traduccion_literal"] == literal
    assert respuesta.json()["desconocidas"] == desconocidas


def test_literal_sin_frase_y_sin_completar_palabras_desconocidas(recursos, modulo_limpio):
    with TestClient(crear_app(ServicioModelo(recursos))) as cliente:
        # No hay una frase del corpus que contenga 'saludo', pero sí asociación IBM.
        modulo_limpio._modelo["tabla"]["saludo"] = {"token_c": 0.9}
        datos = cliente.post("/consultar", json={"texto": "saludo saludo"}).json()
        assert datos["encontrada"] is False
        assert datos["resultado"] == "No encontré esa frase"
        assert datos["traduccion"] is None
        assert datos["traduccion_literal"] == "token_c token_c"
        incompleta = cliente.post("/consultar", json={"texto": "saludo desconocida"}).json()
        assert incompleta["traduccion_literal"] is None
        assert incompleta["desconocidas"] == ["desconocida"]
