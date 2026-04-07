document.addEventListener("DOMContentLoaded", () => {
  // Animar barras de progreso
  document.querySelectorAll(".pps-progress__fill").forEach((fill) => {
    const target = fill.getAttribute("data-width") || "0";
    fill.style.width = "0%";
    setTimeout(() => {
      fill.style.width = `${target}%`;
    }, 150);
  });

  // Auto-ocultar alertas
  document.querySelectorAll(".pps-alert").forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s";
      alert.style.opacity = "0";
      setTimeout(() => {
        alert.remove();
      }, 500);
    }, 5000);
  });
});
