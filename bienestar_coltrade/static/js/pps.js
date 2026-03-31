// PPS - People Performance System

document.addEventListener("DOMContentLoaded", function () {

  // Auto-ocultar alertas despues de 5 segundos
  document.querySelectorAll(".pps-alert").forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = "opacity 0.5s";
      alert.style.opacity = "0";
      setTimeout(function () { alert.remove(); }, 500);
    }, 5000);
  });

  // Confirmar antes de enviar formularios con data-confirm
  document.querySelectorAll("[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var msg = form.getAttribute("data-confirm") || "Estas seguro?";
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // Animar barras de progreso al cargar
  document.querySelectorAll(".pps-progress__fill").forEach(function (fill) {
    var target = fill.getAttribute("data-width") || "0";
    fill.style.width = "0%";
    setTimeout(function () {
      fill.style.width = target + "%";
    }, 150);
  });

  // Resaltar la fila del usuario actual en el ranking
  document.querySelectorAll(".ranking-me").forEach(function (row) {
    row.scrollIntoView({ behavior: "smooth", block: "center" });
  });

});
