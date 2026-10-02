# Traductor / consultor español → náhuatl (prototipo local)

Prototipo web local. Escribes una frase corta en español y te da una traducción
ORIENTATIVA al náhuatl, o avisa "no encontré esa frase". No inventa traducciones.

> Dirección: solo español → náhuatl. No es traductor oficial.
> El corpus mezcla variantes y épocas. NO tenemos variante definida.

## Equipo (5)
- Rodrigo Leyba Palafox: datos
- Kendra Aiman de la Vega Anaya: líder técnico y modelado PLN
- Abimael Enrique Betanzo Alava: backend e integración
- Cristina Fernanda Martínez Cadena: frontend y QA
- Génesis Samantha Blanchard Mendoza: evaluación

## Cómo correr (resumen corto)
1. Instalar Python 3.13.0 (probado en esta compu).
2. Crear entorno y instalar:
   `pip install -r requirements.txt`
3. Poner `datos/train.csv` local (no se sube a GitHub, pesa ~6 MB).
4. Entrenar una vez: `python -m modelo.entrenar`
5. Prender API: `uvicorn api.main:app --reload`
6. Abrir `web/index.html` en el navegador.

## Carpetas
- `datos/`: CSV original + lista propia de frases
- `modelo/`: limpieza + IBM Model 1 + buscador + traducir()
- `api/`: FastAPI que carga el modelo
- `web/`: página sencilla
- `pruebas/`: evaluación con 20% apartado
- `docs/`: documentos y bitácora de prompts

## Créditos y licencias (pendiente Entrega 1)
- Dataset: somosnlp-hackathon-2022/Axolotl-Spanish-Nahuatl, licencia MPL-2.0.
  Cita: Gutierrez-Vasques, Sierra y Pompa, "Axolotl: a web accessible parallel corpus for spanish-nahuatl".
- Referencia para comparar: somosnlp-hackathon-2022/t5-small-spanish-nahuatl y milmor/t5-small-spanish-nahuatl, Apache 2.0. NO son nuestro modelo.
- Verificación frases: Gran Diccionario Náhuatl UNAM (gdn.iib.unam.mx).
- Qué generó la IA y qué modificamos: ver `docs/BITACORA_PROMPTS.md`.
