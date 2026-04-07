document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.querySelector(".navbar");
  if (!navbar) return;

  const handleScroll = () => {
    if (window.scrollY > 8) {
      navbar.classList.add("navbar--scrolled");
    } else {
      navbar.classList.remove("navbar--scrolled");
    }
  };

  handleScroll();
  window.addEventListener("scroll", handleScroll, { passive: true });
});
