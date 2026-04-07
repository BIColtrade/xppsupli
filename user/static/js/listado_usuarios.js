document.addEventListener("DOMContentLoaded", () => {
  const filterInput = document.getElementById("userFilter");
  const rows = Array.from(document.querySelectorAll("tbody tr"));

  const normalizeText = (value) =>
    (value || "").toString().toLowerCase().trim();

  const setRowEditing = (row, editing) => {
    const fields = Array.from(row.querySelectorAll('[data-editable="1"]'));
    const saveBtn = row.querySelector(".btn-save");
    const editBtn = row.querySelector('[data-action="edit"]');

    fields.forEach((field) => {
      field.disabled = !editing;
      field.classList.toggle("is-disabled", !editing);
    });
    if (saveBtn) {
      saveBtn.disabled = !editing;
    }
    if (editBtn) {
      editBtn.disabled = editing;
    }
  };

  rows.forEach((row) => {
    if (row.hasAttribute("data-user-row")) {
      setRowEditing(row, false);
      const editBtn = row.querySelector('[data-action="edit"]');
      if (editBtn) {
        editBtn.addEventListener("click", () => {
          setRowEditing(row, true);
        });
      }
    }
  });

  if (filterInput) {
    filterInput.addEventListener("input", () => {
      const q = normalizeText(filterInput.value);
      rows.forEach((row) => {
        const email = normalizeText(row.querySelector('[data-filter="email"]')?.value);
        const nombre = normalizeText(row.querySelector('[data-filter="nombre"]')?.value);
        const apellido = normalizeText(row.querySelector('[data-filter="apellido"]')?.value);
        const fullName = `${nombre} ${apellido}`.trim();

        const match = !q || email.includes(q) || fullName.includes(q);
        row.style.display = match ? "" : "none";
      });
    });
  }

  document.querySelectorAll(".msg").forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s";
      alert.style.opacity = "0";
      setTimeout(() => {
        alert.remove();
      }, 500);
    }, 5000);
  });
});
