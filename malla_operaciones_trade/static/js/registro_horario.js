document.addEventListener("DOMContentLoaded", () => {
  const puntoSelect = document.getElementById("registroPunto");
  const coordSelect = document.getElementById("registroCoordinador");
  const asesorSelect = document.getElementById("registroAsesor");

  if (puntoSelect && coordSelect && asesorSelect) {
    puntoSelect.addEventListener("change", () => {
      const option = puntoSelect.selectedOptions[0];
      if (!option) return;
      const coordDefault = option.dataset.coordDefault || "";
      const asesorDefault = option.dataset.asesorDefault || "";
      if (coordDefault) {
        coordSelect.value = coordDefault;
      }
      if (asesorDefault) {
        asesorSelect.value = asesorDefault;
      }
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
