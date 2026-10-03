// Prueba el JavaScript real con controles y respuestas HTTP controladas.
// No requiere paquetes de Node ni escribe archivos fuera de api/.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const codigo = readFileSync(resolve(__dirname, '../../web/script.js'), 'utf8');

function preparar(fetch) {
  const crearElemento = () => ({
    value: '', textContent: '', disabled: false, eventos: {},
    addEventListener(evento, funcion) { this.eventos[evento] = funcion; },
    setAttribute() {},
    replaceChildren(hijo) { this.textContent = hijo.textContent; },
  });
  const elementos = Object.fromEntries(['inputText', 'outputText', 'charCount',
    'btnConsultar', 'btnClear', 'btnCopy'].map(id => [id, crearElemento()]));
  const chips = [crearElemento()];
  chips[0].textContent = 'Hola amigo';
  const document = {
    getElementById: id => elementos[id], querySelectorAll: () => chips,
    createElement: crearElemento,
    addEventListener: (evento, funcion) => funcion(),
  };
  vm.runInNewContext(codigo, {
    document, fetch, window: { location: { protocol: 'http:' } },
    navigator: { clipboard: { writeText: async () => {} } },
    AbortController, setTimeout, clearTimeout,
  });
  elementos.inputText.value = 'Hola amigo';
  return { elementos, chips, consultar: elementos.btnConsultar.eventos.click };
}

for (const [estado, mensaje] of [
  [422, 'válida'], [503, 'no está disponible'], [500, 'Ocurrió un error'],
]) {
  test(`HTTP ${estado} muestra su estado y restaura los controles`, async () => {
    const { elementos, chips, consultar } = preparar(async () => ({ ok: false, status: estado }));
    await consultar();
    assert.ok(elementos.outputText.textContent.includes(mensaje));
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
  assert.equal(elementos.outputText.textContent, 'No encontré esa frase');
});

test('recuperación exitosa muestra exactamente resultado', async () => {
  const { elementos, consultar } = preparar(async () => ({
    ok: true, json: async () => ({ encontrada: true, resultado: 'Respuesta controlada' }),
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
  assert.ok(elementos.outputText.textContent.includes('No se pudo conectar'));
  assert.equal(elementos.btnConsultar.disabled, false);
  assert.equal(chips[0].disabled, false);
});

for (const encontrada of [true, false]) {
  test(`muestra la literal orientativa separada; encontrada=${encontrada}`, async () => {
    const resultado = encontrada ? 'Frase del corpus' : 'No encontré esa frase';
    const { elementos, consultar } = preparar(async () => ({
      ok: true, json: async () => ({ encontrada, resultado,
        traduccion_literal: 'token_a token_b', desconocidas: [] }),
    }));
    await consultar();
    assert.ok(elementos.outputText.textContent.startsWith(resultado));
    assert.ok(elementos.outputText.textContent.includes('Traducción literal orientativa'));
    assert.ok(elementos.outputText.textContent.includes('token_a token_b'));
  });
}

test('explica palabras sin candidata sin crear una traducción parcial', async () => {
  const { elementos, consultar } = preparar(async () => ({
    ok: true, json: async () => ({ encontrada: false, resultado: 'No encontré esa frase',
      traduccion_literal: null, desconocidas: ['desconocida'],
      palabras: [{ esp: 'hola', candidatas: [{ nah: 'NO CONCATENAR', prob: 0.9 }] }] }),
  }));
  await consultar();
  assert.ok(elementos.outputText.textContent.includes('Sin traducción literal completa'));
  assert.ok(elementos.outputText.textContent.includes('desconocida'));
  assert.ok(!elementos.outputText.textContent.includes('NO CONCATENAR'));
});
