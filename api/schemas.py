"""Contratos JSON: distingue recuperación de frases y orientación por palabras."""

from pydantic import BaseModel, Field, StrictStr, field_validator

from modelo.limpiar import limpiar


class Consulta(BaseModel):
    texto: StrictStr = Field(min_length=1, max_length=300)

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, texto: str) -> str:
        """No consulta cadenas que quedan vacías después de la limpieza real."""
        texto = texto.strip()
        if not limpiar(texto):
            raise ValueError("Escribe una palabra o frase.")
        return texto


class Candidata(BaseModel):
    nah: str
    prob: float


class Palabra(BaseModel):
    esp: str
    candidatas: list[Candidata]


class RespuestaConsulta(BaseModel):
    resultado: str
    encontrada: bool
    traduccion: str | None
    frase_encontrada: str | None
    similitud: float
    palabras: list[Palabra]
    # None significa que alguna palabra no tiene una candidata suficientemente clara.
    traduccion_literal: str | None
    desconocidas: list[str]
