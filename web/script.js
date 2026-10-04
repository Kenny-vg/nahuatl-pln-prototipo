/**
 * Conector de Interfaz Dinámica con FastAPI (/consultar).
 * - Exacta: 100% («Coincidencia exacta»)
 * - Casi exacta: 85% a 99% («Coincidencia casi exacta»)
 * - Parecida: 50% a 84% («Frase parecida, no igual»)
 * - No encontrada: < 50% («No encontré esa frase»)
 */
document.addEventListener('DOMContentLoaded', () => {
  // Elementos de Entrada
  const inputText = document.getElementById('inputText');
  const charCount = document.getElementById('charCount');
  const btnClear = document.getElementById('btnClear');
  const btnConsultar = document.getElementById('btnConsultar');
  const chips = document.querySelectorAll('.chip');

  // Tarjeta de Resultados y Guía
  const resultCard = document.getElementById('resultCard');
  const statusBadge = document.getElementById('statusBadge');
  const scoreTag = document.getElementById('scoreTag');
  const idleGuideBox = document.getElementById('idleGuideBox');

  // Bloques dinámicos de consulta
  const querySection = document.getElementById('querySection');
  const displayQuery = document.getElementById('displayQuery');
  const queryDivider = document.getElementById('queryDivider');

  // Sección de Coincidencia en Corpus
  const matchSection = document.getElementById('matchSection');
  const similarityText = document.getElementById('similarityText');
  const matchedPhraseText = document.getElementById('matchedPhraseText');
  const progressBarFill = document.getElementById('progressBarFill');

  // Sección de Traducción y Avisos
  const translationSection = document.getElementById('translationSection');
  const outputText = document.getElementById('outputText');
  const btnCopy = document.getElementById('btnCopy');
  const warningBox = document.getElementById('warningBox');
  const notFoundBox = document.getElementById('notFoundBox');
  const queryStatusMsg = document.getElementById('queryStatusMsg');

  // Tarjeta de Palabras Sueltas
  const wordsList = document.getElementById('wordsList');

  // Estado Local
  let consultaEnCurso = false;
  let resultadoCopiable = false;
  let temporizadorCopiar;

  // Actualizar contador de caracteres
  function actualizarContador() {
    charCount.textContent = `${inputText.value.length} / 300`;
  }

  inputText.addEventListener('input', actualizarContador);

  // Enviar con Enter (sin Shift)
  inputText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      consultarAPI();
    }
  });

  // Bloquear / Desbloquear controles durante la petición HTTP
  function bloquearControles(bloquear) {
    [inputText, btnConsultar, btnClear, btnCopy, ...chips].forEach((control) => {
      if (control) control.disabled = bloquear;
    });
    resultCard.setAttribute('aria-busy', String(bloquear));
  }

  // Renderizar la lista de palabras sueltas
  function renderizarPalabras(palabras) {
    wordsList.innerHTML = '';
    if (!Array.isArray(palabras) || palabras.length === 0) {
      wordsList.innerHTML = '<p class="words-empty-note">Sin candidatos para desglosar.</p>';
      return;
    }

    palabras.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'word-row';

      const spanEsp = document.createElement('span');
      spanEsp.className = 'word-esp';
      spanEsp.textContent = item.esp || '';

      const spanArrow = document.createElement('span');
      spanArrow.className = 'word-arrow';
      spanArrow.innerHTML = '&rarr;';

      const spanNah = document.createElement('span');
      const spanProb = document.createElement('span');
      spanProb.className = 'word-prob';

      if (Array.isArray(item.candidatas) && item.candidatas.length > 0) {
        const candidataPrincipal = item.candidatas[0];
        spanNah.className = 'word-nah';
        spanNah.textContent = candidataPrincipal.nah;
        spanProb.textContent = typeof candidataPrincipal.prob === 'number'
          ? `prob. ${candidataPrincipal.prob.toFixed(2)}`
          : '';
      } else {
        spanNah.className = 'word-nah no-cand';
        spanNah.textContent = 'sin candidatas';
        spanProb.textContent = '';
      }

      row.appendChild(spanEsp);
      row.appendChild(spanArrow);
      row.appendChild(spanNah);
      row.appendChild(spanProb);
      wordsList.appendChild(row);
    });
  }

  // Renderizar los resultados y aplicar colores y textos de coincidencia
  function mostrarResultado(textoIngresado, datos) {
    idleGuideBox.hidden = true;
    queryStatusMsg.hidden = true;

    displayQuery.textContent = textoIngresado;
    querySection.hidden = false;
    queryDivider.hidden = false;

    const similitud = typeof datos.similitud === 'number' && Number.isFinite(datos.similitud)
      ? Math.max(0, Math.min(1, datos.similitud))
      : 0;
    const porcentaje = Math.round(similitud * 100);

    // Actualizar palabras sueltas
    renderizarPalabras(datos.palabras);

    if (datos.encontrada && typeof datos.traduccion === 'string' && datos.traduccion.trim()) {
      matchSection.hidden = false;
      translationSection.hidden = false;
      notFoundBox.hidden = true;

      resultadoCopiable = true;
      outputText.textContent = datos.traduccion;
      matchedPhraseText.textContent = datos.frase_encontrada
        ? `«${datos.frase_encontrada}»`
        : `«${textoIngresado}»`;
      progressBarFill.style.width = `${porcentaje}%`;

      if (porcentaje >= 85) {
        // ==========================================
        // ESTADO 1: Exacta (100%) o Casi exacta (85-99%)
        // ==========================================
        resultCard.className = 'box-card result-card state-exact';
        statusBadge.textContent = porcentaje === 100 ? 'Coincidencia exacta' : 'Coincidencia casi exacta';
        scoreTag.textContent = `similitud ${porcentaje}%`;
        similarityText.textContent = porcentaje === 100 ? '' : 'similitud alta';
        warningBox.hidden = true;
      } else {
        // ==========================================
        // ESTADO 2: Parecida, no igual (50-84%)
        // ==========================================
        resultCard.className = 'box-card result-card state-similar';
        statusBadge.textContent = 'Frase parecida, no igual';
        scoreTag.textContent = `similitud ${porcentaje}%`;
        similarityText.textContent = 'similitud media';
        warningBox.hidden = false;
      }
    } else {
      // ==========================================
      // ESTADO 3: No encontrada (< 50%)
      // ==========================================
      resultCard.className = 'box-card result-card state-not-found';
      statusBadge.textContent = 'No encontré esa frase';
      scoreTag.textContent = '';
      similarityText.textContent = '';
      matchSection.hidden = true;
      translationSection.hidden = true;
      warningBox.hidden = true;
      notFoundBox.hidden = false;
      resultadoCopiable = false;
    }
  }

  // Estado de carga mientras responde la API
  function mostrarCargando(textoIngresado) {
    idleGuideBox.hidden = true;
    displayQuery.textContent = textoIngresado;
    querySection.hidden = false;
    queryDivider.hidden = false;
    resultCard.className = 'box-card result-card state-idle';
    statusBadge.textContent = 'Consultando...';
    scoreTag.textContent = '';
    matchSection.hidden = true;
    translationSection.hidden = true;
    warningBox.hidden = true;
    notFoundBox.hidden = true;
    queryStatusMsg.hidden = false;
    queryStatusMsg.textContent = 'Buscando en el corpus Axolotl...';
    wordsList.innerHTML = '<p class="words-empty-note">Consultando candidatas...</p>';
  }

  // Mostrar mensaje de error o aviso del sistema
  function mostrarError(mensaje) {
    idleGuideBox.hidden = true;
    resultCard.className = 'box-card result-card state-not-found';
    statusBadge.textContent = 'Aviso';
    scoreTag.textContent = '';
    matchSection.hidden = true;
    translationSection.hidden = true;
    warningBox.hidden = true;
    notFoundBox.hidden = true;
    queryStatusMsg.hidden = false;
    queryStatusMsg.textContent = mensaje;
    resultadoCopiable = false;
  }

  // Restablecer interfaz limpia al presionar Borrar
  function restablecerEstado() {
    inputText.value = '';
    actualizarContador();
    querySection.hidden = true;
    queryDivider.hidden = true;
    matchSection.hidden = true;
    translationSection.hidden = true;
    warningBox.hidden = true;
    notFoundBox.hidden = true;
    queryStatusMsg.hidden = true;
    
    // Vuelve la guía visual para que la tarjeta no quede desierta
    idleGuideBox.hidden = false;
    resultCard.className = 'box-card result-card state-idle';
    statusBadge.textContent = 'Esperando consulta';
    scoreTag.textContent = '';
    wordsList.innerHTML = '<p class="words-empty-note">Las candidatas aprendidas por el modelo aparecerán aquí tras consultar.</p>';
    resultadoCopiable = false;
    inputText.focus();
  }

  btnClear.addEventListener('click', restablecerEstado);

  // Chips de ejemplo
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      inputText.value = chip.textContent.trim();
      actualizarContador();
      consultarAPI();
    });
  });

  // Petición a FastAPI (/consultar)
  async function consultarAPI() {
    if (consultaEnCurso) return;

    const texto = inputText.value.trim();
    if (!texto) {
      mostrarError('Escribe una palabra o frase para consultar.');
      return;
    }

    if (window.location.protocol === 'file:') {
      mostrarError('Abre esta página desde http://127.0.0.1:8000/web/ para consultar.');
      return;
    }

    consultaEnCurso = true;
    bloquearControles(true);
    mostrarCargando(texto);

    const controlador = new AbortController();
    const tiempoLimite = setTimeout(() => controlador.abort(), 30000);

    try {
      const response = await fetch('/consultar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto }),
        signal: controlador.signal
      });

      if (response.ok) {
        const datos = await response.json();
        if (typeof datos.resultado !== 'string' || typeof datos.encontrada !== 'boolean') {
          mostrarError('No se pudo obtener el resultado. Inténtalo de nuevo.');
        } else {
          mostrarResultado(texto, datos);
        }
      } else if (response.status === 422) {
        mostrarError('Escribe una palabra o frase válida de hasta 300 caracteres.');
      } else if (response.status === 503) {
        mostrarError('El consultor no está disponible en este momento. Inténtalo más tarde.');
      } else {
        mostrarError('Ocurrió un error al consultar. Inténtalo de nuevo.');
      }
    } catch (error) {
      mostrarError(error.name === 'AbortError'
        ? 'La consulta tardó demasiado. Inténtalo de nuevo.'
        : 'No se pudo conectar con el consultor. Inténtalo de nuevo.');
    } finally {
      clearTimeout(tiempoLimite);
      consultaEnCurso = false;
      bloquearControles(false);
    }
  }

  btnConsultar.addEventListener('click', consultarAPI);

  // Copiar al portapapeles
  btnCopy.addEventListener('click', async () => {
    if (!resultadoCopiable || consultaEnCurso) return;

    const textoACopiar = outputText.textContent.trim();
    if (!textoACopiar) return;

    try {
      await navigator.clipboard.writeText(textoACopiar);
      btnCopy.textContent = '¡Copiado!';
    } catch {
      btnCopy.textContent = 'No se pudo copiar';
    }

    clearTimeout(temporizadorCopiar);
    temporizadorCopiar = setTimeout(() => {
      btnCopy.textContent = 'Copiar';
    }, 1500);
  });
});