(function () {
  const searchInput = document.getElementById('tableSearch');
  const tables = Array.from(document.querySelectorAll('[data-filter-table]'));

  function normalize(value) {
    return (value || '').toString().toLowerCase().trim();
  }

  function filterTables(query) {
    const q = normalize(query);
    tables.forEach((tableWrap) => {
      const rows = Array.from(tableWrap.querySelectorAll('tbody tr'));
      rows.forEach((row) => {
        const text = normalize(row.innerText);
        row.style.display = !q || text.includes(q) ? '' : 'none';
      });
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', (event) => {
      filterTables(event.target.value);
    });
  }
})();