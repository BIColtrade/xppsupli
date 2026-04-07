document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".pps-alert").forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s";
      alert.style.opacity = "0";
      setTimeout(() => {
        alert.remove();
      }, 500);
    }, 5000);
  });

  document.querySelectorAll("[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const msg = form.getAttribute("data-confirm") || "Estas seguro?";
      if (!confirm(msg)) event.preventDefault();
    });
  });
});
