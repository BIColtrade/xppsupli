document.addEventListener("DOMContentLoaded", () => {
  const empty = document.querySelector(".listado__empty");
  if (!empty) return;
  empty.style.opacity = "0";
  empty.style.transform = "translateY(6px)";
  requestAnimationFrame(() => {
    empty.style.transition = "opacity 0.4s ease, transform 0.4s ease";
    empty.style.opacity = "1";
    empty.style.transform = "translateY(0)";
  });
});
