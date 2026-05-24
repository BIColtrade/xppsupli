document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.querySelector(".users__filters");
  const filterArea = document.getElementById("userFilterArea");
  const filterRol = document.getElementById("userFilterRol");
  const rows = Array.from(document.querySelectorAll("tbody tr"));

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

  if (filterArea) {
    filterArea.addEventListener("change", () => filterForm?.submit());
  }
  if (filterRol) {
    filterRol.addEventListener("change", () => filterForm?.submit());
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
