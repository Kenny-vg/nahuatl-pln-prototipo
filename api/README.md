# API del consultor español → náhuatl

La API reutiliza `modelo.traducir.traducir()` con umbral 0.5 y tres candidatas.
Presenta la traducción recuperada del corpus y, por separado, la
`traduccion_literal` que ya calcula el modelo. La API no duplica el algoritmo
de selección de candidatas y nunca entrena automáticamente.

## Instalación en Windows PowerShell

Ejecuta desde la raíz del proyecto con Python 3.13 instalado. Todos los archivos
generados se mantienen en `api/`; no hace falta activar el entorno virtual.

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
New-Item -ItemType Directory -Force api/.tmp | Out-Null
$env:TEMP = Join-Path (Get-Location) "api/.tmp"
$env:TMP = $env:TEMP
py -3.13 -B -m venv api/.venv
& ./api/.venv/Scripts/python.exe -B -m pip install --no-cache-dir -r api/requirements-dev.txt
```

Para un entorno sin pruebas puedes instalar `api/requirements.txt` en lugar de
`api/requirements-dev.txt`. Mantén `PYTHONDONTWRITEBYTECODE=1` en cada terminal
que use la API: también evita crear cachés al importar `modelo/`.

## Configurar el artefacto IBM

En la revisión inicial no se encontró `modelo/tabla.json`. Hace falta un
JSON **ya entrenado**, no una tabla vacía. Su estructura debe ser un diccionario
no vacío `{palabra_es: {palabra_nah: probabilidad}}`, con probabilidades finitas
entre 0 y 1. La validación de formato no acredita su calidad ni su procedencia.

Indica la ubicación del archivo existente sin moverlo ni modificarlo:

```powershell
$env:NAHUATL_TABLA = "C:\ruta\al\artefacto\tabla.json"
```

Si omites la variable, se usa `api/artefactos/tabla.json` cuando existe; en caso
contrario se busca `modelo/tabla.json`. Una ruta relativa se resuelve
respecto a la raíz del proyecto. El corpus siempre es `datos/train.csv`; ambos
recursos se leen sin modificarlos. No se buscan artefactos arbitrarios fuera del
proyecto ni se descargan modelos automáticamente.

### Entrenar manualmente en este equipo

Si aún no existe la tabla local, ejecuta desde la raíz:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
& ./api/.venv/Scripts/python.exe -B -u -m api.entrenar
```

Este comando reutiliza las funciones de `modelo/entrenar.py`, lee
`datos/train_80%.csv`, ejecuta diez iteraciones y guarda el resultado en
`api/artefactos/tabla.json`. No modifica el modelo ni los CSV, no sobrescribe
una tabla existente y no se ejecuta al arrancar la API. El JSON es un artefacto
persistente de entrenamiento, no una caché temporal. Está excluido de Git.
Si aparece un error de memoria, no hay una tabla utilizable: libera memoria y
reintenta o entrena en un equipo con más memoria. No se reduce el corpus ni se
cambian las diez iteraciones automáticamente.
Reinicia Uvicorn al terminar. Si habías definido `NAHUATL_TABLA` para otro archivo,
actualiza esa variable o elimínala de la sesión para usar la selección local:

```powershell
Remove-Item Env:NAHUATL_TABLA -ErrorAction SilentlyContinue
```

El entrenamiento IBM usa únicamente el 80 %. El buscador mantiene el corpus
`datos/train.csv` solicitado para la API; por tanto, verificar recuperación sobre
ese corpus no constituye una evaluación independiente sobre el 20 % reservado.

La API carga una vez por proceso. El cargador existente construye TF-IDF en memoria
y conserva su caché; eso no reentrena IBM ni guarda un índice en disco. Si falla
alguna etapa, las consultas quedan bloqueadas aunque haya un caché parcial.
Después de corregir el artefacto, reinicia el servidor; no hay reintentos por petición.

## Arrancar y abrir la página

Desde la raíz del proyecto:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
& ./api/.venv/Scripts/python.exe -B -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Abre <http://127.0.0.1:8000/web/>. No abras el HTML con doble clic: la página
y `/consultar` usan el mismo origen y no se necesita CORS. HTML y CSS se sirven
sin alterar su diseño. No se habilitan credenciales ni orígenes externos.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/salud
$cuerpo = @{ texto = "Hola amigo" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/consultar -Method Post -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($cuerpo))
```

Sin artefacto, PowerShell mostrará un error HTTP 503: es el comportamiento previsto.
La página seguirá disponible y explicará que el consultor no está disponible.

## Contrato y errores

`POST /consultar` recibe `{"texto":"Hola amigo"}`. Devuelve `resultado`,
`encontrada`, `traduccion`, `frase_encontrada`, `similitud`, `palabras`,
`traduccion_literal` y `desconocidas`.
`resultado` es la traducción del corpus o `No encontré esa frase`. Incluso sin
coincidencia se conservan similitud y candidatas reales.

La literal se muestra como orientación palabra por palabra, en orden español;
no acredita corrección gramatical ni equivale a una frase del corpus. Puede estar
disponible aunque `encontrada` sea `false`, sin cambiar `resultado` ni `traduccion`.
Se conserva esta distinción al copiar el texto de la pantalla.

Se reutilizan las reglas de `modelo/traducir.py`: omitir `in`, `yn`, `on`, exigir
probabilidad mínima 0.01 y, cuando hay dos o más opciones elegibles, que la primera
supere o iguale 1.5 veces la segunda. La selección usa toda la tabla, no solo las
tres candidatas mostradas. Si alguna palabra no cumple, `traduccion_literal` es
`null` y `desconocidas` indica las palabras sin candidata clara. No se muestra
una traducción literal parcial. Estos criterios son heurísticos del modelo.

- 200: consulta válida, con o sin coincidencia.
- 422: texto ausente, nulo, tipo incorrecto, vacío tras limpiar o más de 300 caracteres.
- 503: tabla, corpus o índice no disponibles; no significa frase desconocida.
- 500: fallo inesperado, sin trazas ni rutas en la respuesta.

Los errores tienen `resultado` y `error.codigo`; no incluyen el contenido de la
excepción. `/salud` devuelve `estado` y `modelo_disponible`, con 200 o 503.
El frontend distingue esos estados, bloquea envíos duplicados y restaura controles
en `finally`. Una espera superior a 30 segundos cancela la espera del navegador.

## Pruebas

Desde la raíz, con el entorno anterior:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
& ./api/.venv/Scripts/python.exe -B -m pytest api/tests -p no:cacheprovider --basetemp=api/.tmp/pytest
```

Si tienes Node.js, las pruebas de interacción controlada del JavaScript no
requieren instalar paquetes adicionales:

```powershell
node --test api/tests/test_web.cjs
```

Las pruebas usan servicios controlados y un corpus artificial generado únicamente
dentro del directorio temporal de `api/`. Comprueban validaciones, contrato,
recuperación con la lógica existente, rechazo por similitud/cobertura, carga única,
fallo parcial, tabla ausente/inválida, errores 500 y servicio estático. También
verifican la literal, sus umbrales, partículas excluidas, repeticiones y palabras
desconocidas mediante datos artificiales.
No constituyen una evaluación del modelo IBM entrenado del proyecto.

Cuando esté disponible el JSON real: reinicia, comprueba `/salud`, consulta una
frase española del CSV y verifica que `frase_encontrada` y `traduccion` formen un
par de ese corpus. Si hay duplicados, usa el par recuperado, no presupongas una
traducción única. La verificación real queda pendiente mientras falte el artefacto.

## Verificación realizada en esta implementación

- 43 pruebas Python aprobadas y 9 pruebas JavaScript aprobadas, incluida la
  traducción literal con casos controlados.
- Uvicorn real: `/web/` responde 200; `/salud` y una consulta válida responden
  503 al faltar el artefacto. También se verificó el mensaje en el navegador y
  la restauración del botón de consulta.
- Entorno de comprobación: Python 3.12.14, FastAPI 0.142.2, Uvicorn 0.54.0,
  pandas 3.0.6 y scikit-learn 1.9.1. Python 3.13 es la versión indicada por el
  README raíz, pero no estaba instalado en este equipo y no se probó aquí.
- TestClient emitió un aviso de deprecación del uso de HTTPX con Starlette;
  no hubo fallos. No se verificó una traducción con un JSON IBM entrenado real.
- Se intentó entrenar manualmente con 15 284 pares de `train_80%.csv` y diez
  iteraciones. La implementación existente se detuvo con `MemoryError` antes
  de guardar el JSON. El artefacto sigue pendiente; la API continúa en estado
  de modelo no disponible. No se alteraron los datasets ni el algoritmo.
