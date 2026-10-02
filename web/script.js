document.addEventListener('DOMContentLoaded', () => {
  const inputText = document.getElementById('inputText');
  const outputText = document.getElementById('outputText');
  const charCount = document.getElementById('charCount');
  const btnConsultar = document.getElementById('btnConsultar'); // Cambiado a btnConsultar
  const btnClear = document.getElementById('btnClear');
  const btnCopy = document.getElementById('btnCopy');
  const chips = document.querySelectorAll('.chip');

  inputText.addEventListener('input', () => {
    charCount.textContent = `${inputText.value.length} / 300`;
  });

  btnClear.addEventListener('click', () => {
    inputText.value = '';
    charCount.textContent = '0 / 300';
    outputText.innerHTML = '<span class="placeholder-text">El resultado aparecerá aquí.</span>';
  });

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      inputText.value = chip.textContent;
      charCount.textContent = `${inputText.value.length} / 300`;
      consultarAPI();
    });
  });

  // Función 100% dependiente de la API, sin datos falsos
  async function consultarAPI() {
    const text = inputText.value.trim();
    if (!text) return;

    outputText.innerHTML = '<span class="placeholder-text">Consultando...</span>';

    try {
      // Ojo: Abimael debe asegurarse que este sea el link correcto de la API
      const response = await fetch('http://127.0.0.1:8000/consultar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: text })
      });

      if (response.ok) {
        const data = await response.json();
        // Muestra lo que devuelva la API
        outputText.textContent = data.resultado || 'No encontré esa frase'; 
      } else {
        outputText.textContent = 'No encontré esa frase';
      }
    } catch (error) {
      // Si la API está apagada o Abimael no la ha subido, muestra error de conexión
      outputText.innerHTML = '<span class="placeholder-text" style="color: #ef4444;">Error: No hay conexión con la API.</span>';
    }
  }

  btnConsultar.addEventListener('click', consultarAPI);

  btnCopy.addEventListener('click', () => {
    if (outputText.textContent && !outputText.querySelector('.placeholder-text')) {
      navigator.clipboard.writeText(outputText.textContent);
      btnCopy.textContent = '¡Copiado!';
      setTimeout(() => btnCopy.textContent = 'Copiar', 1500);
    }
  });
});