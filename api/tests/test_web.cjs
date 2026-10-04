// Prueba el JavaScript real con controles y respuestas HTTP controladas.
// No requiere paquetes de Node ni escribe archivos fuera de api/.
// El mock reproduce las IDs reales de web/index.html que usa web/script.js.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const codigo = readFileSync(resolve(__dirname, '../../web/script.js'), 'utf8');

const IDS = ['inputText', 'charCount', 'btnClear', 'btnConsultar', 'resultCard',
  'statusBadge', 'scoreTag', 'idleGuideBox', 'querySection', 'displayQuery',
  'queryDivider', 'matchSection', 'similarityText', 'matchedPhraseText',
  'progressBarFill', 'translationSection', 'outputText', 'btnCopy', 'warningBox',
  'notFoundBox', 'queryStatusMsg', 'wordsList'];

function preparar(fetch) {
  const copias = [];
  const crearElemento = () => ({
    value: '', textContent: '', innerHTML: '', disabled: false, hidden: false,
    className: '', style: {}, atributos: {}, hijos: [], eventos: {},
    addEventListener(evento, funcion) { this.eventos[evento] = funcion; },
    setAttribute(nombre, valor) { this.atributos[nombre] = valor; },
    appendChild(hijo) { this.hijos.push(hijo); return hijo; },
    focus() {},
  });
  const elementos = Object.fromEntries(IDS.map(id => [id, crearElemento()]));
  const chips = [crearElemento()];
  chips[0].textContent = 'Hola amigo';
  const document = {
    getElementById: id => elementos[id], querySelectorAll: () => chips,
    createElement: crearElemento,
    addEventListener: (evento, funcion) => funcion(),
  };
  vm.runInNewContext(codigo, {
    document, fetch, window: { location: { protocol: 'http:' } },
    navigator: { clipboard: { writeText: async texto => { copias.push(texto); } } },
    AbortController, setTimeout, clearTimeout,
  });
  elementos.inputText.value = 'Hola amigo';
  return { elementos, chips, copias, consultar: elementos.btnConsultar.eventos.click };
}

test('separa traducción, parecido y frase; borrar limpia los detalles', async () => {
  const {elementos, consultar} = preparar(async () => ({ok: true, json: async () => ({
    encontrada: true, resultado: 'texto', traduccion: 'texto náhuatl',
    frase_encontrada: 'Buenos días Francisco', similitud: 0.661,
    traduccion_literal: null, desconocidas: ['dias'],
  })}));
  await consultar();
  assert.equal(elementos.outputText.textContent, 'texto náhuatl');
  assert.equal(elementos.statusBadge.textContent, 'Frase parecida, no igual');
  assert.ok(elementos.scoreTag.textContent.includes('66%'));
  assert.equal(elementos.similarityText.textContent, 'similitud media');
  assert.ok(elementos.matchedPhraseText.textContent.includes('Buenos días Francisco'));
  assert.equal(elementos.queryStatusMsg.hidden, true);
  assert.equal(elementos.matchSection.hidden, false);
  elementos.btnClear.eventos.click();
  assert.equal(elementos.inputText.value, '');
  assert.equal(elementos.outputText.textContent, '');
  assert.equal(elementos.matchSection.hidden, true);
  assert.equal(elementos.translationSection.hidden, true);
  assert.equal(elementos.idleGuideBox.hidden, false);
  assert.equal(elementos.statusBadge.textContent, 'Esperando consulta');
});

test('el parecido no aceptado no se presenta como confianza de la literal', async () => {
  const {elementos, consultar} = preparar(async () => ({ok: true, json: async () => ({
    encontrada: false, resultado: 'No encontré esa frase', similitud: 0.8,
    traduccion_literal: 'token', palabras: [{esp:'agua', candidatas:[]}],
  })}));
  await consultar();
  assert.equal(elementos.outputText.textContent, '');
  assert.equal(elementos.matchSection.hidden, true);
  assert.equal(elementos.notFoundBox.hidden, false);
  assert.equal(elementos.queryStatusMsg.hidden, true);
  assert.ok(!elementos.queryStatusMsg.textContent.includes('token'));
  assert.equal(elementos.wordsList.hijos.length, 1);
  assert.equal(elementos.wordsList.hijos[0].hijos[2].textContent, 'sin candidatas');
});

test('copiar excluye avisos y porcentaje; error posterior borra resultados anteriores', async () => {
  let intentos = 0;
  const {elementos, consultar, copias} = preparar(async () => ++intentos === 1
    ? {ok: true, json: async () => ({encontrada: true, resultado: 'token',
      traduccion: 'token', similitud: 1, frase_encontrada: 'frase'})}
    : {ok: false, status: 503});
  await consultar();
  assert.equal(elementos.statusBadge.textContent, 'Coincidencia exacta');
  await elementos.btnCopy.eventos.click();
  assert.deepEqual(copias, ['token']);
  await consultar();
  assert.equal(elementos.outputText.textContent, '');
  assert.equal(elementos.matchSection.hidden, true);
  assert.equal(elementos.translationSection.hidden, true);
  assert.ok(elementos.queryStatusMsg.textContent.includes('no está disponible'));
});

for (const [estado, mensaje] of [
  [422, 'válida'], [503, 'no está disponible'], [500, 'Ocurrió un error'],
]) {
  test(`HTTP ${estado} muestra su estado y restaura los controles`, async () => {
    const { elementos, chips, consultar } = preparar(async () => ({ ok: false, status: estado }));
    await consultar();
    assert.ok(elementos.queryStatusMsg.textContent.includes(mensaje));
    assert.equal(elementos.outputText.textContent, '');
    for (const control of [...Object.values(elementos), ...chips]) assert.equal(control.disabled, false);
  });
}

test('sin coincidencia no se confunde con error de conexión', async () => {
  const { elementos, consultar } = preparar(async (url, opciones) => {
    assert.equal(url, '/consultar');
    assert.equal(opciones.method, 'POST');
    assert.deepEqual(JSON.parse(opciones.body), { texto: 'Hola amigo' });
    return { ok: true, json: async () => ({ encontrada: false, resultado: 'No encontré esa frase' }) };
  });
  await consultar();
  assert.equal(elementos.outputText.textContent, '');
  assert.equal(elementos.statusBadge.textContent, 'No encontré esa frase');
  assert.equal(elementos.notFoundBox.hidden, false);
});

test('recuperación exitosa muestra exactamente resultado', async () => {
  const { elementos, consultar } = preparar(async () => ({
    ok: true, json: async () => ({ encontrada: true, resultado: 'Respuesta controlada', traduccion: 'Respuesta controlada' }),
  }));
  await consultar();
  assert.equal(elementos.outputText.textContent, 'Respuesta controlada');
});

test('bloquea envíos duplicados y restaura tras fallo de red', async () => {
  let rechazar;
  let peticiones = 0;
  const { elementos, chips, consultar } = preparar(() => {
    peticiones++;
    return new Promise((resolve, reject) => { rechazar = reject; });
  });
  const pendiente = consultar();
  assert.equal(elementos.btnConsultar.disabled, true);
  assert.equal(chips[0].disabled, true);
  await consultar();
  assert.equal(peticiones, 1);
  rechazar(new Error('fallo controlado'));
  await pendiente;
  assert.ok(elementos.queryStatusMsg.textContent.includes('No se pudo conectar'));
  assert.equal(elementos.btnConsultar.disabled, false);
  assert.equal(chips[0].disabled, false);
});

for (const encontrada of [true, false]) {
  test(`la literal de la API no se pega como texto; encontrada=${encontrada}`, async () => {
    const { elementos, consultar } = preparar(async () => ({
      ok: true, json: async () => (encontrada
        ? { encontrada, resultado: 'Frase del corpus', traduccion: 'Frase del corpus',
            frase_encontrada: 'Frase del corpus', similitud: 1,
            traduccion_literal: 'token_a token_b', desconocidas: [] }
        : { encontrada, resultado: 'No encontré esa frase', similitud: 0.2,
            traduccion_literal: 'token_a token_b', desconocidas: [] }),
    }));
    await consultar();
    assert.equal(elementos.queryStatusMsg.hidden, true);
    assert.ok(!elementos.queryStatusMsg.textContent.includes('token_a token_b'));
    if (encontrada) {
      assert.equal(elementos.outputText.textContent, 'Frase del corpus');
    } else {
      assert.equal(elementos.outputText.textContent, '');
    }
  });
}

test('las desconocidas se ven en la tarjeta de palabras, no como texto pegado', async () => {
  const { elementos, consultar } = preparar(async () => ({
    ok: true, json: async () => ({ encontrada: false, resultado: 'No encontré esa frase',
      traduccion_literal: null, desconocidas: ['desconocida'],
      palabras: [{ esp: 'hola', candidatas: [{ nah: 'NO CONCATENAR', prob: 0.9 }] }] }),
  }));
  await consultar();
  assert.equal(elementos.queryStatusMsg.hidden, true);
  assert.equal(elementos.notFoundBox.hidden, false);
  assert.equal(elementos.wordsList.hijos[0].hijos[2].textContent, 'NO CONCATENAR');
  assert.ok(!elementos.outputText.textContent.includes('NO CONCATENAR'));
});

test('la partícula principal se etiqueta y no se confunde con traducción', async () => {
  const { elementos, consultar } = preparar(async () => ({
    ok: true, json: async () => ({ encontrada: false, resultado: 'No encontré esa frase',
      traduccion_literal: null, desconocidas: ['que'],
      palabras: [{ esp: 'que', candidatas: [{ nah: 'on', prob: 0.14 }, { nah: 'yehjuan', prob: 0.12 }] }] }),
  }));
  await consultar();
  const fila = elementos.wordsList.hijos[0];
  assert.ok(fila.hijos[2].textContent.includes('(partícula)'));
  assert.ok(fila.hijos[3].textContent.includes('se omite en la literal'));
  assert.equal(elementos.queryStatusMsg.hidden, true);
});
