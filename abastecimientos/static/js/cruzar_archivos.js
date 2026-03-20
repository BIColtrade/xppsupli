document.addEventListener('DOMContentLoaded', function () {
  const app = document.getElementById('cruzar-app');
  if (!app) return;

  const dataUrl = app.dataset.url;
  const exportUrl = app.dataset.exportUrl;

  const statusEl = document.getElementById('status');
  const tbody = document.querySelector('#cruzar-table tbody');
  const btnRefresh = document.getElementById('btn-refresh');
  const btnExport = document.getElementById('btn-export');

  const cols = [
    'Material',
    'Producto',
    'Marca',
    'Centro Costos',
    'Punto de Venta',
    'Sugerido Claro',
    'Inventario',
    'Transitos',
    'Ventas Actuales',
    'Envio Inventario 3 meses',
    'Sugerido Coltrade',
    'Promedio 3 Meses',
    'Sugerido Final'
  ];

  function setStatus(message) {
    if (statusEl) statusEl.textContent = message;
  }

  function clearTable() {
    if (tbody) tbody.innerHTML = '';
  }

  function formatValue(value) {
    if (value === null || value === undefined) return '';
    return String(value);
  }

  function applyNumberStyle(td, value) {
    const num = parseFloat(String(value).replace(',', '.'));
    if (Number.isNaN(num)) return;
    if (num > 0) td.classList.add('cell-positive');
    if (num < 0) td.classList.add('cell-negative');
  }

  async function loadData() {
    setStatus('Cargando datos...');
    clearTable();

    try {
      const res = await fetch(dataUrl, { headers: { 'Accept': 'application/json' } });
      const json = await res.json();
      if (json.status !== 'ok') {
        throw new Error(json.message || 'Error al obtener datos');
      }

      const rows = json.data || [];
      if (!rows.length) {
        setStatus('No se encontraron registros.');
        return;
      }

      setStatus(`Registros: ${rows.length}`);

      for (const r of rows) {
        const tr = document.createElement('tr');
        for (const c of cols) {
          const td = document.createElement('td');
          const val = formatValue(r[c]);
          td.textContent = val;

          if (
            ['Inventario', 'Transitos', 'Ventas Actuales', 'Envio Inventario 3 meses'].includes(c)
          ) {
            applyNumberStyle(td, val);
          }

          tr.appendChild(td);
        }
        tbody.appendChild(tr);
      }
    } catch (err) {
      console.error(err);
      setStatus('Error cargando datos: ' + err.message);
    }
  }

  if (btnRefresh) btnRefresh.addEventListener('click', loadData);
  if (btnExport) {
    btnExport.addEventListener('click', function () {
      window.location.href = exportUrl;
    });
  }

  loadData();
});