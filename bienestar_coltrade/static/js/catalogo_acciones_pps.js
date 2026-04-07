document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".accion-card");
  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 40}ms`;
    card.classList.add("accion-card--ready");
  });

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
