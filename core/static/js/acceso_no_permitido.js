document.addEventListener("DOMContentLoaded", () => {
  const card = document.querySelector(".access-card");
  if (!card) return;
  card.style.opacity = "0";
  card.style.transform = "translateY(10px)";
  requestAnimationFrame(() => {
    card.style.transition = "opacity 0.4s ease, transform 0.4s ease";
    card.style.opacity = "1";
    card.style.transform = "translateY(0)";
  });
});
