document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".home-card");
  if (!cards.length) return;

  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 60}ms`;
    card.classList.add("home-card--ready");
  });
});
