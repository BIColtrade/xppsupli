document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("js-enabled");

  const rows = document.querySelectorAll(".pps-table tbody tr");
  rows.forEach((row, index) => {
    row.style.transitionDelay = `${index * 40}ms`;
    requestAnimationFrame(() => {
      row.classList.add("pps-row--ready");
    });
  });
});
