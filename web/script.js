// Conecta los controles existentes con la API sin alterar el diseño de la página.
document.addEventListener('DOMContentLoaded', () => {
  const inputText = document.getElementById('inputText');
  const outputText = document.getElementById('outputText');
  const charCount = document.getElementById('charCount');
  const btnConsultar = document.getElementById('btnConsultar'); // Cambiado a btnConsultar
  const btnClear = document.getElementById('btnClear');
  const btnCopy = document.getElementById('btnCopy');
  const chips = document.querySelectorAll('.chip');
  let consultaEnCurso = false;
  let resultadoCopiable = false;
  let temporizadorCopiar;
  outputText.setAttribute('aria-live', 'polite');
  outputText.setAttribute('role', 'status');

  // Los mensajes usan la clase visual existente; el texto remoto nunca es HTML.
  function mostrarMensaje(mensaje, esTraduccion = false) {
    resultadoCopiable = esTraduccion;
    clearTimeout(temporizadorCopiar);
    btnCopy.textContent = 'Copiar';
    if (esTraduccion) {
      outputText.textContent = mensaje;
    } else {
      const aviso = document.createElement('span');
      aviso.className = 'placeholder-text';
      aviso.textContent = mensaje;
      outputText.replaceChildren(aviso);
    }
  }

  function bloquearControles(bloquear) {
    [inputText, btnConsultar, btnClear, btnCopy, ...chips].forEach(control => {
      control.disabled = bloquear;
    });
    outputText.setAttribute('aria-busy', String(bloquear));
  }

  function mostrarResultado(datos) {
    // El servidor entrega ambas salidas del modelo. No elegimos ni concatenamos
    // candidatas aquí; mantenemos el aviso orientativo también al copiar.
    const literal = typeof datos.traduccion_literal === 'string'
      && datos.traduccion_literal.trim() ? datos.traduccion_literal : null;
    let mensaje = datos.resultado;
    if (literal) {
      mensaje += ` · Traducción literal orientativa (palabra por palabra, en orden español): ${literal}`;
    } else if (Array.isArray(datos.desconocidas) && datos.desconocidas.length) {
      mensaje += ` · Sin traducción literal completa: no hay una candidata clara para ${datos.desconocidas.join(', ')}.`;
    }
    mostrarMensaje(mensaje, datos.encontrada || Boolean(literal));
  }

  inputText.addEventListener('input', () => {
    charCount.textContent = `${inputText.value.length} / 300`;
  });

  btnClear.addEventListener('click', () => {
    inputText.value = '';
    charCount.textContent = '0 / 300';
    mostrarMensaje('El resultado aparecerá aquí.');
  });

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      inputText.value = chip.textContent;
      charCount.textContent = `${inputText.value.length} / 300`;
      consultarAPI();
    });
  });

  // Un envío corresponde a una consulta. La API valida el contenido definitivo.
  async function consultarAPI() {
    if (consultaEnCurso) return;
    const text = inputText.value.trim();
    if (!text) {
      mostrarMensaje('Escribe una palabra o frase para consultar.');
      return;
    }
    if (window.location.protocol === 'file:') {
      mostrarMensaje('Abre esta página desde http://127.0.0.1:8000/web/ para consultar.');
      return;
    }

    consultaEnCurso = true;
    bloquearControles(true);
    mostrarMensaje('Consultando...');
    const controlador = new AbortController();
    const tiempoLimite = setTimeout(() => controlador.abort(), 30000);

    try {
      // Ruta relativa al origen: FastAPI sirve esta página desde /web/.
      const response = await fetch('/consultar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: text }),
        signal: controlador.signal
      });

      if (response.ok) {
        const data = await response.json();
        if (typeof data.resultado !== 'string' || typeof data.encontrada !== 'boolean') {
          mostrarMensaje('No se pudo obtener el resultado. Inténtalo de nuevo.');
        } else {
          mostrarResultado(data);
        }
      } else if (response.status === 422) {
        mostrarMensaje('Escribe una palabra o frase válida de hasta 300 caracteres.');
      } else if (response.status === 503) {
        // Falta de modelo no significa que la frase no exista en el corpus.
        mostrarMensaje('El consultor no está disponible en este momento. Inténtalo más tarde.');
      } else {
        mostrarMensaje('Ocurrió un error al consultar. Inténtalo de nuevo.');
      }
    } catch (error) {
      mostrarMensaje(error.name === 'AbortError'
        ? 'La consulta tardó demasiado. Inténtalo de nuevo.'
        : 'No se pudo conectar con el consultor. Inténtalo de nuevo.');
    } finally {
      // También se restablecen los controles si falla la conexión o el JSON.
      clearTimeout(tiempoLimite);
      consultaEnCurso = false;
      bloquearControles(false);
    }
  }

  btnConsultar.addEventListener('click', consultarAPI);

  btnCopy.addEventListener('click', async () => {
    if (resultadoCopiable && !consultaEnCurso) {
      try {
        await navigator.clipboard.writeText(outputText.textContent);
        if (consultaEnCurso || !resultadoCopiable) return;
        btnCopy.textContent = '¡Copiado!';
      } catch (error) {
        if (consultaEnCurso || !resultadoCopiable) return;
        btnCopy.textContent = 'No se pudo copiar';
      }
      temporizadorCopiar = setTimeout(() => btnCopy.textContent = 'Copiar', 1500);
    }
  });
});
