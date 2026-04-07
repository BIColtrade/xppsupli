document.addEventListener("DOMContentLoaded", () => {
  const row = document.querySelector(".ranking-me");
  if (row) {
    row.scrollIntoView({ behavior: "smooth", block: "center" });
  }
});
