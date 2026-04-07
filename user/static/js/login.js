document.addEventListener("DOMContentLoaded", () => {
  const card = document.querySelector(".login-card");
  if (!card) return;

  const updateGlow = (event) => {
    const rect = card.getBoundingClientRect();
    const x = Math.min(Math.max(event.clientX - rect.left, 0), rect.width);
    const y = Math.min(Math.max(event.clientY - rect.top, 0), rect.height);
    card.style.setProperty("--mx", `${x}px`);
    card.style.setProperty("--my", `${y}px`);
  };

  card.addEventListener("pointermove", updateGlow, { passive: true });
  card.addEventListener("pointerleave", () => {
    card.style.setProperty("--mx", "50%");
    card.style.setProperty("--my", "25%");
  });
});
