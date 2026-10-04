"""FastAPI: recibe consultas del navegador y sirve el frontend sin cambiarlo."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.config import Configuracion, RAIZ_PROYECTO
from api.schemas import Consulta, RespuestaConsulta
from api.servicio import ModeloNoDisponible, ServicioModelo


def error_publico(estado: int, codigo: str, mensaje: str):
    """Errores uniformes sin valores de entrada, rutas ni trazas internas."""
    return JSONResponse(status_code=estado, content={
        "resultado": mensaje, "error": {"codigo": codigo}
    })


def crear_app(servicio=None):
    """La inyección del servicio permite pruebas aisladas sin entrenar modelos."""
    if servicio is None:
        servicio = ServicioModelo(Configuracion.desde_entorno())

    @asynccontextmanager
    async def ciclo_de_vida(app):
        # Se carga al arrancar, antes de atender consultas. Un fallo conserva /salud.
        servicio.cargar()
        yield

    app = FastAPI(title="Consultor español-náhuatl", lifespan=ciclo_de_vida)

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(request, exc):
        return error_publico(422, "TEXTO_INVALIDO",
                             "Escribe una palabra o frase de hasta 300 caracteres.")

    @app.exception_handler(ModeloNoDisponible)
    async def modelo_no_disponible(request, exc):
        return error_publico(503, "MODELO_NO_DISPONIBLE", "El modelo no está disponible.")

    @app.exception_handler(Exception)
    async def fallo_inesperado(request, exc):
        return error_publico(500, "ERROR_INTERNO", "No se pudo procesar la consulta.")

    @app.get("/salud")
    def salud():
        """Distingue un servidor encendido de un modelo listo para consultar."""
        if not servicio.listo:
            return JSONResponse(status_code=503, content={
                "estado": "modelo_no_disponible", "modelo_disponible": False
            })
        return {"estado": "listo", "modelo_disponible": True}

    @app.post("/consultar", response_model=RespuestaConsulta)
    def consultar(consulta: Consulta):
        """Recibe {texto}, valida con Pydantic y devuelve la recuperación real."""
        return servicio.consultar(consulta.texto)

    @app.get("/", include_in_schema=False)
    def raiz():
        """La URL raíz del despliegue muestra la app en vez de un 404."""
        return RedirectResponse(url="/web/", status_code=307)

    # /web/ y /consultar comparten origen; no hace falta habilitar CORS.
    app.mount("/web", StaticFiles(directory=RAIZ_PROYECTO / "web", html=True), name="web")
    return app


app = crear_app()
