# Documento del proyecto
**Entrega 1 · Prototipo funcional y repositorio**

- **Nombre del proyecto:** Consultor de frases español → náhuatl (prototipo PLN)
- **Equipo:** Equipo Náhuatl-PLN
- **Integrantes:** Rodrigo Leyba Palafox (datos) · Kendra Aiman de la Vega Anaya
  (líder técnico y modelado) · Abimael Enrique Betanzo Alava (backend e integración) ·
  Cristina Fernanda Martínez Cadena (frontend y QA) · Génesis Samantha Blanchard
  Mendoza (evaluación)
- **Rama de IA:** Procesamiento de Lenguaje Natural
- **Fecha:** octubre de 2026 *(confirmar día exacto de entrega)*

## 1. Problemática a resolver

El náhuatl lo hablan más de un millón y medio de personas en México y es lengua
oficial, pero casi no tiene herramientas digitales accesibles: no existe un
traductor español→náhuatl gratuito y fácil de usar para estudiantes y público
general. Además, los pocos textos digitales paralelos que existen son históricos
y religiosos, mezclan variantes y épocas sin una norma única de escritura, así
que ningún sistema puede cubrir el habla cotidiana con ellos.

Este proyecto ataca ese hueco con un consultor web gratuito: recupera la frase
más parecida del corpus y, cuando no hay cobertura, lo dice abiertamente en vez
de inventar una traducción. Para una lengua originaria, no inventar es un
requisito, no un detalle.

## 2. Descripción del proyecto

El programa recibe una frase corta en español (1 a 300 caracteres) y devuelve su
equivalencia en náhuatl con un buscador por similitud (TF-IDF + coseno) apoyado
en una tabla de alineación léxica estadística (IBM Model 1). La salida incluye:
traducción recuperada del corpus (o el aviso *"No encontré esa frase"*), frase
del corpus usada, similitud en porcentaje y candidatas por palabra. La interfaz
web muestra el resultado con su contexto (coincidencia exacta, parecida o no
encontrada) y nunca presenta una traducción literal palabra-por-palabra como si
fuera una traducción real.

## 3. Rama de IA

**Rama asignada:** Procesamiento de Lenguaje Natural.

Es la adecuada porque el problema es mapear texto entre dos lenguas con un
corpus paralelo escaso, ruidoso y con variación dialectal y ortográfica. Las
técnicas usadas (recuperación de información por similitud y alineación léxica
estadística) pertenecen a esta rama y permiten un sistema explicable línea por
línea, sin hardware especial, condición necesaria para un prototipo académico
desplegable.

## 4. Caso de uso

- **Usuario objetivo:** estudiantes de náhuatl y público interesado en la lengua.
- **Situación en la que se usa el programa:** quiere saber cómo se dice una frase
  cotidiana y la escribe en el consultor web (ejemplo: *"Gracias"*).
- **Resultado esperado:** el equivalente en náhuatl (*tlaxtlahuijli*) con su
  contexto de coincidencia; si la frase no tiene cobertura, el aviso honesto
  *"No encontré esa frase"* en lugar de una traducción inventada.

## 5. Requisitos

| Tipo | Requisito | Versión mínima |
|---|---|---|
| Lenguaje | Python | 3.13 |
| Datos | pandas | 2.2 |
| Modelo | scikit-learn | 1.6 |
| API | fastapi | 0.115 |
| Servidor | uvicorn | 0.30 |
| Validación | pydantic | 2.9 |
| Pruebas | pytest | 9.1.1 |

Versiones verificadas en desarrollo: Python 3.14.7, pandas 3.0.6,
scikit-learn 1.9.1, fastapi 0.142.2, uvicorn 0.54.0, pydantic 2.13.5.
Navegador moderno (Chrome o Edge) para la interfaz web.

## 6. Instrucciones de instalación y ejecución

- **Modalidad:** web URL + instalación local (la modalidad principal evaluada es local).
- **Repositorio:** https://github.com/Kenny-vg/nahuatl-pln-prototipo
- **Aplicación:** https://nahuatl-pln-prototipo.onrender.com/ (plan gratuito;
  puede tardar ~1 minuto en despertar por inactividad).

### 6.1 Instalación (la web pública no requiere este paso)

1. Clonar el repositorio y entrar a la carpeta del proyecto.
2. Crear entorno virtual e instalar dependencias de desarrollo:
   `pip install -r api/requirements-dev.txt`.
3. Entrenar el modelo una vez: `python -m modelo.entrenar`
   (genera `modelo/tabla.json` local; tarda segundos).

### 6.2 Ejecución

1. Arrancar el servidor desde la raíz:
   `uvicorn api.main:app --host 127.0.0.1 --port 8000`.
2. Abrir `http://127.0.0.1:8000/web/` (la raíz `/` redirige sola).
3. Escribir una frase o usar un ejemplo y pulsar Consultar;
   `/salud` debe responder `{"estado":"listo"}`.

## 7. Lista de verificación de la entrega

| Entregable | Ubicación (enlace o ruta) | Listo |
|---|---|---|
| Código completo en repositorio | https://github.com/Kenny-vg/nahuatl-pln-prototipo | Sí |
| Archivo de dependencias | `requirements.txt`, `api/requirements.txt`, `api/requirements-dev.txt` | Sí |
| Datos de prueba | `datos/test_20%.csv`, casos CP en `pruebas/evaluar_modelo.py` | Sí |
| Historial de commits de todos los integrantes | Repositorio (los 5 integrantes con commits) | Sí |
| Créditos y licencias en el README | README + `docs/fuentes_datos.md` (Axolotl MPL-2.0, Tatoeba CC BY 2.0 FR) | Sí |
| Bitácora de prompts | Pendiente por el equipo | No |
