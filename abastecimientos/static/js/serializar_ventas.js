document.addEventListener('DOMContentLoaded', function () {
  const container = document.querySelector('.serializar-container');
  if (!container) return;

  const previewUrl = container.dataset.previewUrl;
  const btnPreview = document.getElementById('btn-preview');
  const fileInput = document.getElementById('file-input');
  const marcasContainer = document.getElementById('marcas-importadas');
  const marcasList = document.getElementById('marcas-list');
  const msg = document.getElementById('msg');

  function getCookie(name) {
    const cookieValue = document.cookie
      .split(';')
      .map(c => c.trim())
      .find(c => c.startsWith(name + '='));
    if (!cookieValue) return '';
    return decodeURIComponent(cookieValue.split('=')[1]);
  }

  btnPreview.addEventListener('click', async () => {
    msg.textContent = '';
    if (!fileInput.files.length) {
      msg.textContent = 'Selecciona un archivo .xlsx antes de previsualizar.';
      return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
      btnPreview.disabled = true;
      btnPreview.textContent = 'Cargando...';

      const resp = await fetch(previewUrl, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });

      if (!resp.ok) {
        const err = await resp.json();
        msg.textContent = err.error || 'Error al obtener marcas';
        return;
      }

      const data = await resp.json();
      const marcas = data.marcas || [];

      if (!marcas.length) {
        marcasList.innerHTML = '<em>No se detectaron marcas</em>';
      } else {
        marcasList.innerHTML = marcas.map(m => `<span class="marca-pill">${m}</span>`).join(' ');
      }
      marcasContainer.style.display = 'block';
    } catch (e) {
      console.error(e);
      msg.textContent = 'Error al previsualizar el archivo.';
    } finally {
      btnPreview.disabled = false;
      btnPreview.textContent = 'Mostrar marcas importadas';
    }
  });
});