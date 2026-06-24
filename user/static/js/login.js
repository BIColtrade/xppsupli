document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("togglePassword");
  if (toggleBtn) {
    const passwordInput = document.getElementById("password");
    const eyeShow = document.getElementById("eyeShow");
    const eyeHide = document.getElementById("eyeHide");
    toggleBtn.addEventListener("click", () => {
      const isPassword = passwordInput.type === "password";
      passwordInput.type = isPassword ? "text" : "password";
      eyeShow.classList.toggle("hidden", isPassword);
      eyeHide.classList.toggle("hidden", !isPassword);
    });
  }

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
